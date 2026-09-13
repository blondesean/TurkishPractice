"""Inline vocab_turkish.txt into web/index.html.

The web app is a single self-contained HTML file with no build system and no
server -- the vocab lives inside it in a <script type="application/json"> block
so the page works from file:// and offline. Run this after editing
vocab_turkish.txt (or add_vocab.py) to refresh that block:

    py -3 build_web.py

Only the data block is rewritten; the UI code in web/index.html is untouched.

Pass --fragment PATH to also write a <head>-less copy (used when publishing the
page to a host that supplies its own document skeleton).
"""

import csv
import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOCAB_FILE = os.path.join(BASE_DIR, "vocab_turkish.txt")
WEB_FILE = os.path.join(BASE_DIR, "web", "index.html")

START = '<script id="vocab-data" type="application/json">'
END = "</script>"


def load_vocab():
    """{category: {focus: [[eng, tur], ...]}} -- same shape as load_csv()."""
    data = {}
    with open(VOCAB_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # header: Category / Focus / English / Turkish
        for row in reader:
            if len(row) < 4:
                continue
            cat, sub, eng, tur = (c.strip() for c in row[:4])
            data.setdefault(cat, {}).setdefault(sub, []).append([eng, tur])
    return data


def strip_document(html):
    """Return the page without its doctype/html/head/body wrapper."""
    head = re.search(r"<head[^>]*>(.*?)</head>", html, re.S)
    body = re.search(r"<body[^>]*>(.*?)</body>", html, re.S)
    if not (head and body):
        return html
    keep = "".join(
        m.group(0)
        for m in re.finditer(r"<(title|style)\b.*?</\1>", head.group(1), re.S)
    )
    return keep + "\n" + body.group(1)


def main():
    vocab = load_vocab()
    words = sum(len(w) for subs in vocab.values() for w in subs.values())
    modules = sum(len(subs) for subs in vocab.values())

    with open(WEB_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    i = html.index(START) + len(START)
    j = html.index(END, i)
    payload = json.dumps(vocab, ensure_ascii=False, separators=(",", ":"))
    html = html[:i] + payload + html[j:]

    with open(WEB_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"web/index.html <- {words} words, {modules} modules, "
          f"{len(vocab)} categories ({len(html) / 1024:.0f} KB)")

    if "--fragment" in sys.argv:
        out = sys.argv[sys.argv.index("--fragment") + 1]
        with open(out, "w", encoding="utf-8") as f:
            f.write(strip_document(html))
        print(f"{out} <- fragment copy")


if __name__ == "__main__":
    main()
