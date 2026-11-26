#!/usr/bin/env python3
"""Pre-release quality checks on the built site (docs/). Run after build.py:

    python3 tools/qa.py

Checks every page for: unbalanced/misnested tags, duplicate ids, broken in-page anchors and
aria references, form controls without labels, heading level jumps, missing lang/title/description,
links opening a new tab without rel=noopener, and colour contrast of the brand colour pairs.
"""
import re, sys
from html.parser import HTMLParser
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
OPTIONAL_END = {"p", "li", "dt", "dd", "option", "tr", "td", "th", "thead", "tbody"}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors, self.ids, self.refs, self.anchors = [], [], [], [], []
        self.labels_for, self.controls, self.headings, self.blank_targets = set(), [], [], []
        self.in_label = 0
        self.title = self.desc = None
        self.lang = None
        self._title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if "id" in a:
            self.ids.append(a["id"])
        for k in ("aria-labelledby", "aria-describedby", "aria-controls"):
            if a.get(k):
                self.refs.extend((k, r) for r in a[k].split())
        if tag == "a" and (a.get("href") or "").startswith("#") and len(a["href"]) > 1:
            self.anchors.append(a["href"][1:])
        if tag == "a" and a.get("target") == "_blank" and "noopener" not in (a.get("rel") or ""):
            self.blank_targets.append(a.get("href"))
        if tag == "label":
            self.in_label += 1
            if a.get("for"):
                self.labels_for.add(a["for"])
        if tag in ("input", "select", "textarea"):
            t = a.get("type", "")
            if t not in ("hidden", "submit", "button") and "hp" not in (a.get("class") or ""):
                self.controls.append((a.get("id"), bool(a.get("aria-label") or a.get("aria-labelledby")) or self.in_label > 0))
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "title":
            self._title = True
        if tag == "meta" and a.get("name") == "description":
            self.desc = a.get("content")
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1][0] == tag:
            self.stack.pop()

    def handle_endtag(self, tag):
        if tag == "label":
            self.in_label -= 1
        if tag == "title":
            self._title = False
        if tag in VOID:
            return
        while self.stack and self.stack[-1][0] != tag and self.stack[-1][0] in OPTIONAL_END:
            self.stack.pop()
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
        else:
            self.errors.append(f"unexpected </{tag}> at line {self.getpos()[0]} (open: {[t for t, _ in self.stack[-3:]]})")

    def handle_data(self, data):
        if self._title:
            self.title = (self.title or "") + data


def luminance(hex_):
    rgb = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def main():
    problems = []
    pages = [p for p in DOCS.rglob("*.html") if "noindex" not in p.read_text(encoding="utf-8") or p.name == "404.html"]
    for f in sorted(pages):
        rel = "/" + str(f.relative_to(DOCS)).replace("index.html", "")
        p = Page()
        p.feed(f.read_text(encoding="utf-8"))
        leftover = [t for t, _ in p.stack if t not in OPTIONAL_END and t not in ("html", "body", "head")]
        for e in p.errors:
            problems.append(f"{rel}: {e}")
        if leftover:
            problems.append(f"{rel}: unclosed {leftover}")
        dups = {i for i in p.ids if p.ids.count(i) > 1}
        if dups:
            problems.append(f"{rel}: duplicate id {sorted(dups)}")
        ids = set(p.ids)
        for k, r in p.refs:
            if r not in ids:
                problems.append(f"{rel}: {k} -> missing #{r}")
        for a in p.anchors:
            if a not in ids and a not in ("top",):
                problems.append(f"{rel}: link to missing #{a}")
        for cid, wrapped in p.controls:
            if not wrapped and cid not in p.labels_for:
                problems.append(f"{rel}: form control #{cid} has no label")
        prev = 0
        for h in p.headings:
            if prev and h > prev + 1:
                problems.append(f"{rel}: heading jumps h{prev} -> h{h}")
                break
            prev = h
        if not p.lang:
            problems.append(f"{rel}: missing lang")
        if not (p.title or "").strip():
            problems.append(f"{rel}: missing <title>")
        if f.name != "404.html" and not p.desc:
            problems.append(f"{rel}: missing meta description")
        for href in p.blank_targets:
            problems.append(f"{rel}: target=_blank without noopener ({href})")
    # Brand colour pairs (text on background) – WCAG AA: 4.5 normal text, 3.0 large/bold UI
    pairs = [("#ffffff", "#a32015", "white on TTP red (buttons, hero)", 4.5),
             ("#a32015", "#ffffff", "TTP red text on white (links, eyebrow)", 4.5),
             ("#55575c", "#ffffff", "secondary text on white", 4.5),
             ("#55575c", "#f6f5f4", "secondary text on light grey", 4.5),
             ("#ffffff", "#2c2d31", "white on charcoal", 4.5),
             ("#ffffff", "#0068ff", "white on Zalo blue (button label)", 3.0),
             ("#7e180f", "#fbeae8", "dark red on pink (tags, errors)", 4.5)]
    print("Contrast (WCAG AA):")
    for fg, bg, what, need in pairs:
        c = contrast(fg, bg)
        flag = "OK" if c >= need else "FAIL"
        print(f"  {flag:4} {c:5.2f}:1  {what}")
        if c < need:
            problems.append(f"contrast {what}: {c:.2f} < {need}")
    print(f"Checked {len(pages)} pages")
    for x in problems:
        print("  ✗", x)
    print("QA:", "OK" if not problems else f"{len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
