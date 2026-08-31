#!/usr/bin/env python3
"""
flesh_out_sign.py — turn a freshly-promoted minimal sign page into a rich,
schema-driven one by asking a Cursor agent to author the pageContent.

Pipeline:
  1. gather context for a sign (its 3 Cree options from the translation
     workbench DATA, the graphic concept, the trail stats, the Trailforks/GPX
     info already on the model, and the neighbouring trails in the same area);
  2. build a tight prompt that asks for ONLY a JSON object of pageContent
     fields, following the same schema the renderer consumes;
  3. run the `cursor-agent` CLI in headless print mode (uses your existing
     Cursor desktop login — no API key needed), or accept a ready JSON via
     --from-json (so chat-authored content applies the same way);
  4. validate via catalogue_editor_server._clean_page_content, merge onto the
     model's existing pageContent, stamp the chosen pageStatus, write
     catalogue.json, and re-render docs/<slug>/index.html.

The pageStatus is set by the caller (never the LLM): the CLI defaults to
"agent-drafted" (a draft for you to review, see tools/SIGN_PAGE_AUTHORING.md),
while the editor's "Flesh out details (AI)" button locks the page as
"user-reviewed" so a later "Move to production" won't regenerate over it. Pass
--status to override on the CLI.

Usage:
  # see the exact prompt without calling anything (safe, no writes)
  python3 tools/flesh_out_sign.py --model caddytrack --dry-run

  # run the Cursor agent and apply the result
  python3 tools/flesh_out_sign.py --model caddytrack

  # apply a pageContent JSON you already have (e.g. authored in chat)
  python3 tools/flesh_out_sign.py --model caddytrack --from-json draft.json
"""
import argparse, json, os, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import catalogue_editor_server as ce          # noqa: E402  (schema cleaner + paths)
import sign_page_renderer as spr              # noqa: E402

HTML = REPO_ROOT / "docs" / "cree-trail-names.html"
GFX_JS = REPO_ROOT / "docs" / "graphics-data.js"
PROMPT_DIR = REPO_ROOT / "docs" / "sign-drafts" / "flesh-prompts"

# Fields the agent is allowed to author. trailforks/photo.src/accentColor stay
# under our control (they come from the editor uploads, not the LLM).
AUTHORED_KEYS = {"headerTitle", "linguistics", "culturalStory", "trailStory",
                 "sources", "photoCaption"}


# --------------------------------------------------------------------------- #
# context gathering
# --------------------------------------------------------------------------- #
def _node_data_entry(en):
    """Return the DATA[] object (loc/dist/desc/asc + cree[]) for an English name,
    plus the list of sibling trail names sharing its loc, via node."""
    code = r"""
const fs=require('fs');
const h=fs.readFileSync(process.argv[1],'utf8');
const m=h.match(/const DATA = (\[[\s\S]*?\n\]);/);
if(!m){process.stdout.write('null');process.exit(0);}
const DATA=eval(m[1]);
const en=process.argv[2];
const d=DATA.find(x=>x.en===en)||null;
let siblings=[];
if(d&&d.loc){siblings=DATA.filter(x=>x.loc===d.loc&&x.en!==en).map(x=>({en:x.en,cree:(x.cree&&x.cree[0])?x.cree[0].t:''}));}
process.stdout.write(JSON.stringify({entry:d,siblings:siblings.slice(0,12)}));
"""
    r = subprocess.run(["node", "-e", code, str(HTML), en],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return {"entry": None, "siblings": []}
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"entry": None, "siblings": []}


def _node_graphics(en):
    code = ("global.window={};require(%s);"
            "process.stdout.write(JSON.stringify(window.TRAIL_GRAPHICS[%s]||null));"
            % (json.dumps(str(GFX_JS)), json.dumps(en)))
    r = subprocess.run(["node", "-e", code], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def gather_context(model):
    en = model.get("englishName") or model.get("title") or model.get("id")
    data = _node_data_entry(en)
    gfx = _node_graphics(en) or {}
    entry = data.get("entry") or {}
    pc = model.get("pageContent") or {}
    return {
        "id": model.get("id"),
        "englishName": en,
        "creeName": model.get("creeName") or "",
        "creeSyllabics": model.get("creeSyllabics") or "",
        "loc": entry.get("loc") or "",
        "dist": entry.get("dist") or "",
        "desc": entry.get("desc") or "",
        "asc": entry.get("asc") or "",
        "creeOptions": entry.get("cree") or [],
        "graphicConcept": gfx.get("concept") or "",
        "graphicSubject": gfx.get("subject") or "",
        "graphicType": gfx.get("type") or "screenprint",
        "siblings": data.get("siblings") or [],
        "trailforks": {k: v for k, v in (pc.get("trailforks") or {}).items()
                       if k in ("trailUrl", "displayName", "trailId", "mapStatus")},
        "photoSrc": (pc.get("photo") or {}).get("src") or "",
    }


# --------------------------------------------------------------------------- #
# prompt
# --------------------------------------------------------------------------- #
SCHEMA_DOC = (REPO_ROOT / "tools" / "SIGN_PAGE_AUTHORING.md")


def _order_options(ctx):
    """Put the option actually on the plaque (matches the model's chosen
    creeName / creeSyllabics) first; the rest are alternates. This is what makes
    the page's blurbs describe the CHOSEN name, not always option 1."""
    opts = ctx["creeOptions"] or []
    cn = (ctx.get("creeName") or "").strip()
    cs = (ctx.get("creeSyllabics") or "").strip()

    def is_plaque(o):
        return ((o.get("t", "").strip() == cn and cn)
                or (cs and o.get("s", "").strip() == cs))

    plaque = next((o for o in opts if is_plaque(o)), None)
    others = [o for o in opts if o is not plaque]
    return plaque, others


def build_prompt(ctx):
    plaque, others = _order_options(ctx)
    plaque_line = (
        f"  {plaque.get('t','')}  [{plaque.get('s','')}]  — {plaque.get('g','')}"
        f"  (why: {plaque.get('why','')}; innuendo: {plaque.get('inn','')})"
        if plaque else f"  {ctx['creeName']}  [{ctx['creeSyllabics']}]")
    others_block = "\n".join(
        f"  - {o.get('t','')}  [{o.get('s','')}]  — {o.get('g','')}"
        f"  (why: {o.get('why','')})"
        for o in others) or "  (none)"
    sibs = ", ".join(f"{s['en']} ({s['cree']})" for s in ctx["siblings"]) or "(none listed)"
    tf = ctx["trailforks"]
    tf_line = (f"Trailforks: {tf.get('trailUrl','')} {tf.get('mapStatus','')}"
               if tf else "Trailforks: (none yet)")
    return f"""You are authoring the rich content for a 3D-printed Plains Cree (nêhiyawêwin) mountain-bike trail sign page. Produce ONLY a single JSON object (no prose, no markdown fences) matching the schema below. It will be validated and rendered verbatim.

TRAIL
  English name : {ctx['englishName']}
  Location     : {ctx['loc']}
  Stats        : distance {ctx['dist']}, descent {ctx['desc']}, ascent {ctx['asc']}
  Sign icon    : {ctx['graphicConcept']}  ({ctx['graphicType']})
  {tf_line}
  Nearby trails (for cross-reference, optional): {sibs}

THE NAME ON THE PLAQUE — write the page (especially the cultural story and primarySection) about THIS name, not any other:
{plaque_line}

OTHER CANDIDATE RENDERINGS that were considered — use ONLY to fill relatedForms / quickReference (they are NOT on the plaque):
{others_block}

OUTPUT JSON SHAPE (omit a field only if you truly have nothing real to say):
{{
  "headerTitle": "<English> • <sro> • <syllabics>",
  "photoCaption": "one-line caption for the sign render",
  "linguistics": {{
    "meaning": "short gloss of the plaque name (plain text)",
    "primarySection": {{
      "heading": "The Name on the Plaque",
      "sro": "{ctx['creeName']}",
      "syllabics": "{ctx['creeSyllabics']}",
      "morphemes": [ {{"key":"m0","sro":"…","syllabics":"…","gloss":"plain-text tooltip"}} ]
    }},
    "relatedForms": [ {{"english":"…","sro":"…","syllabics":"…","note":"plain-text italic note","morphemes":[]}} ],
    "quickReference": [ {{"english":"…","sro":"…","syllabics":"…","note":"tooltip"}} ],
    "baseWords": [ {{"sro":"…","english":"…","syllabics":"…"}} ]
  }},
  "culturalStory": {{ "heading":"…", "body":[ "paragraph (may use <strong>/<em>)", "…" ] }},
  "trailStory":   {{ "heading":"The Trail", "body":[ "1-2 sentences on the ride + tap-through to Trailforks" ] }},
  "sources": ["itwêwina","Online Cree Dictionary","Plains Cree Dictionary"]
}}

RULES
- Build relatedForms / quickReference / baseWords from the candidate renderings above and their morphemes; do not invent Cree words you are unsure of.
- HTML (<strong>, <em>, &nbsp;) is allowed ONLY inside culturalStory.body[] and trailStory.body[]. Everything else is plain text.
- The cultural story should explain the name, any wordplay/innuendo, ties to neighbouring trails, and end acknowledging it sits on ᓀᐦᐃᔭᐤ ᐊᐢᑭᕀ Nêhiyaw-Askiy — Plains Cree territory, Treaty 6, a homeland of the Métis Nation.
- Do NOT invent specific people, dates, or trail-difficulty ratings unless they are given above. Keep trailStory to the stats provided.
- Output the JSON object only."""


# --------------------------------------------------------------------------- #
# cursor-agent invocation
# --------------------------------------------------------------------------- #
def find_cursor_agent(explicit=None):
    if explicit:
        return explicit if (os.path.isfile(explicit) and os.access(explicit, os.X_OK)) else None
    found = shutil.which("cursor-agent")
    if found:
        return found
    for cand in (Path.home() / ".local" / "bin" / "cursor-agent",
                 Path("/usr/local/bin/cursor-agent")):
        if cand.is_file() and os.access(cand, os.X_OK):
            return str(cand)
    return None


def run_cursor_agent(prompt, agent_bin, model_name, timeout=420):
    """Run cursor-agent headless (read-only 'ask' mode) and return its final
    assistant text. 'ask' mode keeps the agent read-only so it answers with the
    JSON instead of editing files itself."""
    cmd = [agent_bin, "-p", prompt, "--output-format", "json",
           "--mode", "ask", "--trust"]
    if model_name:
        cmd += ["--model", model_name]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT),
                          timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"cursor-agent exited {proc.returncode}: "
                           f"{(proc.stderr or proc.stdout)[-400:]}")
    out = proc.stdout.strip()
    # --output-format json prints an envelope like
    #   {"type":"result","subtype":"success","is_error":false,"result":"…", …}
    # pull the assistant text out of it (and surface a run-level error).
    try:
        env = json.loads(out)
        if isinstance(env, dict):
            if env.get("is_error") or env.get("subtype") == "error":
                raise RuntimeError("cursor-agent run errored: "
                                   + str(env.get("result") or env)[:400])
            for k in ("result", "text", "response", "content", "output"):
                if isinstance(env.get(k), str) and env[k].strip():
                    return env[k]
        return out
    except json.JSONDecodeError:
        return out


def extract_json_object(text):
    """Find the first balanced {...} JSON object in a blob of text."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?|```$", "", text).strip()
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object found in agent output")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i + 1])
    raise ValueError("unbalanced JSON object in agent output")


# --------------------------------------------------------------------------- #
# apply
# --------------------------------------------------------------------------- #
def apply_authored(model_id, authored, final_status="agent-drafted"):
    """Merge authored fields onto the model's pageContent, validate, render.

    ``final_status`` is the pageStatus stamped on the result. It is forced by the
    caller (never read from the LLM output) so the model can't self-promote, but
    a trusted caller can lock the page as ``user-reviewed`` to protect the freshly
    authored content from being clobbered by later "Move to production" runs
    (promote_sign leaves user-reviewed/published pages untouched)."""
    if final_status not in ce.ALLOWED_PAGE_STATUSES:
        raise ValueError(f"final_status must be one of {sorted(ce.ALLOWED_PAGE_STATUSES)}")
    cat = ce.load_catalogue()
    model = ce.find_model(cat, model_id)
    pc = dict(model.get("pageContent") or {})

    if authored.get("headerTitle"):
        pc["headerTitle"] = authored["headerTitle"]
    if authored.get("photoCaption"):
        photo = dict(pc.get("photo") or {})
        if photo.get("src"):
            photo["caption"] = authored["photoCaption"]
            pc["photo"] = photo
    for key in ("linguistics", "culturalStory", "trailStory", "sources"):
        if authored.get(key) is not None:
            pc[key] = authored[key]
    # status is decided by the caller, never the LLM
    pc["pageStatus"] = final_status

    model["pageContent"] = ce._clean_page_content(pc)
    ce.write_json(ce.CATALOGUE_PATH, cat)
    summaries = spr.render_for_ids([model_id], force=True)
    return summaries


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="catalogue model id (e.g. caddytrack)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the prompt and exit (no agent, no writes)")
    ap.add_argument("--from-json", default="",
                    help="apply a pageContent JSON file instead of calling the agent")
    ap.add_argument("--model-name", default="",
                    help="cursor-agent model id (e.g. sonnet-4, gpt-5); "
                         "empty = use the account default")
    ap.add_argument("--cursor-agent", default="", help="path to the cursor-agent binary")
    ap.add_argument("--save-prompt", action="store_true",
                    help="also write the prompt to docs/sign-drafts/flesh-prompts/<id>.txt")
    ap.add_argument("--status", default="agent-drafted",
                    choices=sorted(ce.ALLOWED_PAGE_STATUSES),
                    help="pageStatus to stamp on the result (default: agent-drafted; "
                         "use user-reviewed to lock the page against later regeneration)")
    args = ap.parse_args()

    cat = ce.load_catalogue()
    try:
        model = ce.find_model(cat, args.model)
    except Exception as e:
        sys.exit(f"error: {e}")

    # --- apply a ready JSON (chat-authored or agent output saved to disk) ---
    if args.from_json:
        authored = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
        summaries = apply_authored(args.model, authored, final_status=args.status)
        print(json.dumps({"ok": True, "applied": "from-json", "summaries": summaries},
                         ensure_ascii=False))
        return

    ctx = gather_context(model)
    prompt = build_prompt(ctx)

    if args.save_prompt or args.dry_run:
        PROMPT_DIR.mkdir(parents=True, exist_ok=True)
        (PROMPT_DIR / f"{args.model}.txt").write_text(prompt, encoding="utf-8")

    if args.dry_run:
        print(prompt)
        return

    agent_bin = find_cursor_agent(args.cursor_agent or None)
    if not agent_bin:
        sys.exit(
            "cursor-agent CLI not found. Install it once and log in:\n"
            "  curl https://cursor.com/install -fsS | bash\n"
            "  cursor-agent login\n"
            "Then re-run, or pass --cursor-agent /path/to/cursor-agent.\n"
            "(Alternatively author the JSON in chat and apply with --from-json.)")

    text = run_cursor_agent(prompt, agent_bin, args.model_name)
    authored = extract_json_object(text)
    summaries = apply_authored(args.model, authored, final_status=args.status)
    print(json.dumps({"ok": True, "applied": "cursor-agent", "model": args.model_name,
                      "summaries": summaries}, ensure_ascii=False))


if __name__ == "__main__":
    main()
