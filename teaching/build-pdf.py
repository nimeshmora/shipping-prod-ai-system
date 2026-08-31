"""Build a single printable HTML file from the weekly teaching guides.

    python teaching/build-pdf.py

Then open teaching/phase-2-teaching-guide.html and print it to PDF
(Cmd+P on a Mac, Ctrl+P elsewhere -> Save as PDF).

No pandoc or LaTeX needed - the CSS handles page breaks, and instructor
notes keep their box on paper.
"""
import os
import re

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "phase-2-teaching-guide.html")

FILES = [
    ("00-how-to-use-this.md", "How to use this"),
    ("week-01.md", "Week 1 · Package"),
    ("week-02.md", "Week 2 · Deploy"),
    ("week-03.md", "Week 3 · Automate and lock"),
    ("week-04.md", "Week 4 · Cap"),
    ("week-05.md", "Week 5 · See"),
    ("week-06.md", "Week 6 · Debug and survive"),
    ("week-07.md", "Week 7 · Attack"),
    ("week-08.md", "Week 8 · Gate, roll back and port"),
]

CSS = """
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }

:root {
  --ink: #1a1a1a;
  --muted: #555;
  --rule: #d8d8d8;
  --box: #f4f6f8;
  --box-edge: #2b6cb0;
  --code-bg: #f6f6f4;
}

* { box-sizing: border-box; }

body {
  font: 10.8pt/1.55 Georgia, "Times New Roman", serif;
  color: var(--ink);
  max-width: 175mm;
  margin: 0 auto;
  padding: 12mm 6mm;
  background: #fff;
}

/* ---- headings ---- */
h1 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 20pt;
  margin: 0 0 4mm;
  padding-bottom: 2mm;
  border-bottom: 2px solid var(--ink);
  page-break-before: always;
  page-break-after: avoid;
}
h1.first { page-break-before: avoid; }

h2 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 13.5pt;
  margin: 7mm 0 2.5mm;
  padding-bottom: 1mm;
  border-bottom: 1px solid var(--rule);
  page-break-after: avoid;
}

h3 {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 11.5pt;
  margin: 5mm 0 1.5mm;
  page-break-after: avoid;
}

p, li { orphans: 3; widows: 3; }
p { margin: 0 0 2.5mm; }
ul, ol { margin: 0 0 3mm; padding-left: 6mm; }
li { margin-bottom: 1mm; }
strong { font-weight: 700; }

/* ---- instructor notes: the boxed asides ---- */
blockquote {
  margin: 3mm 0;
  padding: 2.5mm 4mm;
  background: var(--box);
  border-left: 3.5px solid var(--box-edge);
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 9.6pt;
  line-height: 1.5;
  page-break-inside: avoid;
}
blockquote p { margin: 0 0 1.5mm; }
blockquote p:last-child { margin-bottom: 0; }
blockquote code { background: #e6eaee; }

/* ---- code ---- */
code {
  font-family: "SF Mono", Menlo, Consolas, monospace;
  font-size: 9pt;
  background: var(--code-bg);
  padding: 0.5mm 1mm;
  border-radius: 2px;
}
pre {
  background: var(--code-bg);
  border: 1px solid var(--rule);
  border-radius: 3px;
  padding: 2.5mm 3mm;
  margin: 2.5mm 0 3mm;
  overflow-x: auto;
  page-break-inside: avoid;
}
pre code {
  background: none;
  padding: 0;
  font-size: 8.6pt;
  line-height: 1.45;
  white-space: pre;
}

/* ---- tables ---- */
table {
  border-collapse: collapse;
  width: 100%;
  margin: 3mm 0;
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 9.4pt;
  page-break-inside: avoid;
}
th, td {
  border: 1px solid var(--rule);
  padding: 1.5mm 2.5mm;
  text-align: left;
  vertical-align: top;
}
th { background: var(--box); font-weight: 700; }

hr { border: 0; border-top: 1px solid var(--rule); margin: 5mm 0; }

/* ---- cover + contents ---- */
.cover {
  text-align: center;
  padding-top: 55mm;
  page-break-after: always;
}
.cover .title {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 30pt;
  font-weight: 700;
  line-height: 1.15;
  margin-bottom: 5mm;
}
.cover .sub {
  font-size: 13pt;
  color: var(--muted);
  margin-bottom: 3mm;
}
.cover .rule {
  width: 60mm;
  border-top: 2px solid var(--ink);
  margin: 10mm auto;
}
.cover .meta {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 9.5pt;
  color: var(--muted);
  line-height: 1.9;
}

.contents { page-break-after: always; }
.contents h1 { page-break-before: avoid; }
.contents ol { list-style: none; padding-left: 0; font-size: 11pt; }
.contents li { margin-bottom: 2.5mm; }
.contents .wk {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-weight: 700;
}
.contents .what { color: var(--muted); font-size: 10pt; }

.screen-note {
  background: #fffbe6;
  border: 1px solid #e0d060;
  border-radius: 4px;
  padding: 3mm 4mm;
  margin-bottom: 6mm;
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 9.5pt;
}

@media print { .screen-note { display: none; } }
"""

CONTENTS = [
    ("How to use this", "the five beats, the branch model, what to prepare"),
    ("Week 1 · Package", "an agent with an address, that streams, in a container"),
    ("Week 2 · Deploy", "a public URL, and memory that survives a restart"),
    ("Week 3 · Automate and lock", "git push deploys it; strangers get a 401"),
    ("Week 4 · Cap", "it cannot run forever or run up a bill"),
    ("Week 5 · See", "one trace per turn, and whether it is healthy"),
    ("Week 6 · Debug and survive", "find a bug from traces; survive an outage"),
    ("Week 7 · Attack", "injection, cost, SSRF and load"),
    ("Week 8 · Gate, roll back and port", "a bad change cannot reach users"),
]


def build():
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])

    parts = []
    for name, _title in FILES:
        path = os.path.join(HERE, name)
        text = open(path).read()
        md.reset()
        html = md.convert(text)
        # The first h1 of each file starts a new page, except the very first.
        parts.append(html)

    body = "\n<hr class='sec'>\n".join(parts)
    # first h1 on the page should not force a blank page before it
    body = body.replace("<h1>", "<h1 class='first'>", 1)

    contents_html = "\n".join(
        f'<li><span class="wk">{w}</span><br>'
        f'<span class="what">{d}</span></li>'
        for w, d in CONTENTS
    )

    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Ship Production AI Systems — Phase 2 Teaching Guide</title>
<style>{CSS}</style>
</head>
<body>

<div class="screen-note">
  <strong>To make a PDF:</strong> press <strong>Cmd&nbsp;+&nbsp;P</strong>
  (Mac) or <strong>Ctrl&nbsp;+&nbsp;P</strong>, then choose
  <em>Save as PDF</em> as the destination. Set margins to <em>Default</em> and
  tick <em>Background graphics</em> so the instructor boxes keep their shading.
  This yellow note does not print.
</div>

<div class="cover">
  <div class="title">Ship Production<br>AI&nbsp;Systems</div>
  <div class="sub">Phase 2 · Teaching Guide</div>
  <div class="rule"></div>
  <div class="meta">
    Eight weeks, from a loop in a file<br>
    to something a company can run<br><br>
    Instructor notes included<br>
    KodeKloud
  </div>
</div>

<div class="contents">
<h1 class="first">Contents</h1>
<ol>{contents_html}</ol>
</div>

{body}

</body>
</html>
"""
    open(OUT, "w").write(doc)
    kb = os.path.getsize(OUT) / 1024
    print(f"wrote {OUT}  ({kb:.0f} KB)")
    print("\nOpen it and press Cmd+P -> Save as PDF.")
    print("Tick 'Background graphics' so the instructor boxes keep their shading.")


if __name__ == "__main__":
    build()
