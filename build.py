#!/usr/bin/env python3
"""Build the Chicago guide into two self-contained targets.

  build/index.html     full standalone document  -> GitHub Pages
  build/artifact.html  head+body content only    -> Claude Artifact (it supplies the skeleton)

Both inline the subsetted woff2 faces as data URIs, so neither makes an external request.
"""
import base64, pathlib, re, sys

ROOT = pathlib.Path(__file__).parent
SRC, BUILD = ROOT / "src", ROOT / "build"
TEMPLATE = SRC / "page.html"


def section(text, name):
    m = re.search(rf"<!-- @{name} -->(.*?)<!-- @/{name} -->", text, re.S)
    if not m:
        sys.exit(f"FAIL: missing @{name} section in {TEMPLATE.name}")
    return m.group(1).strip()


def main():
    html = TEMPLATE.read_text(encoding="utf-8")

    for key, fname in (("{{INTER_WOFF2}}", "inter-var.woff2"), ("{{MONO_WOFF2}}", "mono.woff2")):
        if key not in html:
            sys.exit(f"FAIL: placeholder {key} not found")
        html = html.replace(key, base64.b64encode((SRC / fname).read_bytes()).decode("ascii"))

    leftover = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", html)))
    if leftover:
        sys.exit(f"FAIL: unreplaced placeholders: {leftover}")

    head, body = section(html, "HEAD"), section(html, "BODY")

    BUILD.mkdir(exist_ok=True)
    (BUILD / "artifact.html").write_text(head + "\n" + body + "\n", encoding="utf-8")
    (BUILD / "index.html").write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        + head
        + "\n</head>\n<body>\n"
        + body
        + "\n</body>\n</html>\n",
        encoding="utf-8",
    )

    for f in ("index.html", "artifact.html"):
        p = BUILD / f
        print(f"  {f:16s} {p.stat().st_size/1024:7.1f} KB")
    print("build OK")


if __name__ == "__main__":
    main()
