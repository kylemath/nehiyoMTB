# Submitting to *Names: A Journal of Onomastics*

Requirements were checked on the journal's own pages on November 18, 2026:
the author guidelines, the ANS Style Sheet (April 2024), the AI-TT policy, the
publication and ethics pages, and the submission form at
https://ans-names.pitt.edu. Re-check them on the day you submit, because they
change.

Build everything with `make` in `paper/`. The files to upload are in
`paper/names/submission/`.

## 1. Before anything else: the AI policy

Names does not accept text written by AI. That includes AI-generated text that a
person has edited afterwards. Claude drafted the current manuscript as a
scaffold, so it cannot be submitted as it stands.

- [ ] Write the submitted prose yourself. Use the draft as an outline and a
      source of numbers, tables and citations. The scripts, tables and figures
      are analysis tools, which the policy treats differently from prose, but
      they must be disclosed.
- [ ] Write the AI disclosure at the end of the manuscript truthfully. Names
      wants the exact tool names and sources, the dates you used them, the
      precise prompts, and how you used the output. The repository records:
      - a language model drafted the workbench candidates and the sign-page text
        (which model and when is still for you to say);
      - the OpenAI image API drafted the sign icons from the prompts in
        `docs/sign-drafts/manifest.json` and `docs/sign-drafts/flesh-prompts/`;
      - Claude Code (Anthropic) wrote the analysis scripts and the draft
        manuscript, November 17 and 18, 2026.
- [ ] If you are unsure whether the workbench candidates count as "AI-generated
      data" under the policy, ask the editor before you submit:
      Dr. I. M. Nick, nameseditor@gmail.com.

## 2. Fill in the bold "[k to supply]" notes

- [ ] How the workbench candidates were produced (which tool, when, and how you
      chose among them).
- [ ] Who you consulted (by role, or by name only with written permission),
      how, what protocol you offered, and which names changed or were declined.
      Do not quote anyone unless they have agreed to be quoted.
- [ ] Trail builders, trail associations and the City: who you asked about the
      signs and what they said.
- [ ] Ethics: confirm that no personal data are reported. Say whether you
      consulted a research ethics board or judged the work exempt.
- [ ] Funding (none?) and financial interest (sign sales, and how proceeds are
      used).
- [ ] Final version only: affiliation, ORCID, a contributor note of 100 to 150
      words, and a correspondence line. These go in after acceptance.
- [ ] Have a fluent speaker check `supplementary/name_coding.csv`. Ask in
      particular whether the strategy column is right.
- [ ] Fix or explain the spelling disagreements the audit found. Ray Gun is
      missing a p. Wonder Woman's w-dot is on the wrong syllable. Bed Springs has
      no syllabics at all. If you correct `docs/catalogue.json`, rerun `make` and
      every number updates.

## 3. Format: what the build already does, and what to check by eye

Each item below is handled by the build. Open the .docx in Word and check that
each one is still true after your edits.

- [ ] Word file, 12 pt Times New Roman, single spaced, justified, hyphenation
      off, 1-inch margins.
- [ ] Paragraphs indented, with no blank lines between them. Every paragraph has
      at least three sentences.
- [ ] Title in bold, at most 50 words (it is 15 now). Abstract at most 200
      words. 5 to 7 keywords, with at least 2 from the ICOS list (toponymy,
      hodonym and microtoponym are on it). Avoid multi-word keywords.
- [ ] Sections in this order: Introduction, Methodology, Results, Discussion,
      Conclusion, then Notes and References.
- [ ] Main text at most 5,000 words, not counting notes, references, tables and
      graphics. See `wordcount.txt`; it is about 4,460 now.
- [ ] Headings: level 1 bold, level 2 bold italic, level 3 italic.
- [ ] Names under discussion in italics, glosses in 'single quotes', and
      connotations in "double quotes".
- [ ] No footnotes and no automatic endnotes. Notes are typed as plain numbered
      paragraphs after the text, about 400 words at most.
- [ ] Citations follow Chicago author-date with the ANS changes: no comma
      between author and year, & for two authors, et al. for three or more, and
      several works listed most recent first.
- [ ] References have a hanging indent, with volume and issue included. Online
      sources carry a URL and "Accessed Month Day, Year." Non-English titles
      have a translation in brackets (Helset 2019).
- [ ] Tables have no vertical lines and a label on every column. Percentages
      have 2 decimals. Every table and figure has its title above and its
      source below.
- [ ] US or British spelling, used consistently. Names returns manuscripts with
      many errors without review.

## 4. Figures

- [ ] Upload each figure as its own file, as well as embedded in the text:
      `figures/Figure1_map.jpg` (line art, 1200 dpi) and
      `figures/Figure2_signs.jpg` (grayscale photograph, 600 dpi).
- [ ] Colour is free online. Colour in print costs US$400 per figure, plus $75
      for each colour element beyond 4. Both figures are grayscale, so there is
      no colour charge. A colour version of the photograph is in
      `allSigns.jpg` if you decide you want one.
- [ ] Permissions: Figure 1 draws trail tracks that come from Trailforks.
      Decide whether to ask Trailforks for permission, or to credit it as the
      source line does now.

## 5. Blind review

- [ ] Upload `manuscript_anonymized.docx`. It has no author name, no project
      name, no URLs that point to you, and empty document metadata. If you edit
      it in Word, check File > Info > Inspect Document before you upload it.
- [ ] Keep self-identifying details out of the prompts you quote in the AI
      disclosure as well.

## 6. Steps on the OJS site (ans-names.pitt.edu)

1. [ ] Register an account (Register, top right), or log in.
2. [ ] Optional: join the American Name Society. Membership is not required,
       but members' submissions get preference.
3. [ ] Start a new submission and choose the section for research articles.
4. [ ] Tick each item on the submission checklist:
       - the work is original and not under review anywhere else;
       - online references give URLs and access dates;
       - you have permission for any third-party material;
       - you confirm the AI-TT policy, the Publication Policy and the Ethical
         Standards.
5. [ ] Upload the anonymized manuscript as the main file. Upload each figure
       file and the two supplementary CSVs as separate files.
6. [ ] Enter the metadata in the form: title, abstract, keywords, your
       name, affiliation, email and ORCID. These are kept from reviewers.
7. [ ] Add a comment for the editor if you want one. For example, say that the
       Cree names are new coinages, not traditional toponyms, and say how
       speakers were involved.
8. [ ] Confirm and submit. Then expect these stages:
       - a preliminary editorial check;
       - double-blind peer review;
       - after acceptance, copyediting, with an Author Query Form and a
         Typographical Request Form for you to complete.

       The journal gives no turnaround time.
9. [ ] There are no submission, publication or page fees. Articles are
       published under CC BY 4.0.
