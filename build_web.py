"""Inline vocab_turkish.txt and web/grammar.js into web/index.html.

The web app is a single self-contained HTML file with no build system and no
server -- the vocab lives inside it in a <script type="application/json"> block
so the page works from file:// and offline. Run this after editing
vocab_turkish.txt (or add_vocab.py), web/grammar.js or web/sounds/ to refresh
those blocks:

    py -3 build_web.py

Only the vocab, grammar and sound blocks are rewritten; the UI code in web/index.html
is untouched.

Pass --fragment PATH to also write a <head>-less copy (used when publishing the
page to a host that supplies its own document skeleton).
"""

import base64
import csv
import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOCAB_FILE = os.path.join(BASE_DIR, "vocab_turkish.txt")
WEB_FILE = os.path.join(BASE_DIR, "web", "index.html")

START = '<script id="vocab-data" type="application/json">'
GRAMMAR_FILE = os.path.join(BASE_DIR, "web", "grammar.js")
GRAMMAR_START = '<script id="grammar">'
# Answer sound effects, embedded as base64 so the page stays one file and plays
# offline. A missing file just means that effect stays silent.
SOUNDS = {
    "correct": os.path.join(BASE_DIR, "web", "sounds", "correct.mp3"),
    "wrong": os.path.join(BASE_DIR, "web", "sounds", "wrong.mp3"),
}
SOUND_START = '<script id="sound-data" type="application/json">'
END = "</script>"


def replace_block(html, start, payload):
    """Swap the contents of the <script> that opens with `start`."""
    i = html.index(start) + len(start)
    j = html.index(END, i)
    return html[:i] + payload + html[j:]


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

    payload = json.dumps(vocab, ensure_ascii=False, separators=(",", ":"))
    html = replace_block(html, START, payload)

    with open(GRAMMAR_FILE, "r", encoding="utf-8") as f:
        grammar = f.read()
    if END in grammar:
        sys.exit("web/grammar.js must not contain a closing script tag")
    html = replace_block(html, GRAMMAR_START, "\n" + grammar + "\n")

    sounds = {}
    for name, sound_path in SOUNDS.items():
        if os.path.exists(sound_path):
            with open(sound_path, "rb") as f:
                sounds[name] = base64.b64encode(f.read()).decode("ascii")
    html = replace_block(html, SOUND_START, json.dumps(sounds))

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
