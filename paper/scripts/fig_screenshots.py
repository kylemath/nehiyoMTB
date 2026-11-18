"""Screenshots of the live artefacts, rendered from the repository's own docs/
folder by a local web server and headless Chromium (Playwright, driven from screenshots.cjs).

  site_sign_page.png   a sign's interpretive page (docs/kahkakiw/)
  app_*.png            the companion app's web build (docs/app/) at phone size

Third-party requests (map tiles, CDNs, Trailforks widgets) are blocked so the
result does not depend on the network; maps therefore render without a
basemap. If Node, Playwright or Chromium is unavailable, the committed copies in
paper/figures/static/ are used instead, so the paper still builds.
"""
from __future__ import annotations

import functools
import http.server
import shutil
import socketserver
import threading
from pathlib import Path

from common import DOCS, FIG, STATIC

SHOTS = [
    # (file, path, viewport, wait ms, text to click first, path to open after)
    ("site_sign_page.png", "/kahkakiw/", (1280, 1500), 2500, None, None),
    ("app_signin.png", "/app/", (390, 844), 5000, None, None),
    ("app_hunt.png", "/app/", (390, 844), 5000, "Explore without an account", "/app/hunt"),
    ("app_ride.png", "/app/", (390, 844), 5000, "Explore without an account", "/app/ride"),
    ("app_trail.png", "/app/", (390, 844), 5000, "Explore without an account", "/app/trail/kahkakiw"),
]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_head(self):
        # emulate GitHub Pages: unknown /app/* routes fall back to 404.html,
        # which boots the single-page app.
        path = self.translate_path(self.path)
        import os
        if not os.path.exists(path) and self.path.startswith("/app/"):
            self.path = "/404.html"
        return super().send_head()


def main():
    import json
    import os
    import subprocess

    handler = functools.partial(Quiet, directory=str(DOCS))
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{port}"
        shots = [[n, p, w, h, wait, c, t] for n, p, (w, h), wait, c, t in SHOTS]
        env = dict(os.environ)
        try:
            root = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
            env["NODE_PATH"] = os.pathsep.join(filter(None, [env.get("NODE_PATH"), root]))
            out = subprocess.run(["node", str(Path(__file__).with_name("screenshots.cjs")), base,
                                  str(FIG), json.dumps(shots)], capture_output=True, text=True,
                                 timeout=300, env=env)
            print(out.stdout.strip() or out.stderr.strip()[:400])
        except Exception as e:  # noqa: BLE001
            print("screenshots: node/playwright unavailable:", e)
        finally:
            httpd.shutdown()
    for name, *_ in SHOTS:
        if (FIG / name).exists() and (FIG / name).stat().st_mtime > _t0:
            shutil.copy(FIG / name, STATIC / name)      # refresh the committed fallback
        elif (STATIC / name).exists():
            shutil.copy(STATIC / name, FIG / name)
            print("screenshots: using committed copy of", name)


_t0 = __import__("time").time()

if __name__ == "__main__":
    main()
