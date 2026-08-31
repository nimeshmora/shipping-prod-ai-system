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
/* ---------------------------------------------------------------------------
   Buildr Labs house style.

   Tokens are taken from the live site's theme bundle
   (wp-content/themes/buildrlabs/assets/css/redesign.css), which defines them
   in OKLCH. Converted to hex here because print CSS in browsers is safer with
   hex, and a PDF has no dark mode to track.

       --primary   oklch(68% .19 42)     -> #f46622   the orange
       --background oklch(96.7% .008 95) -> #f6f4ee   warm off-white
       --foreground oklch(18% 0 0)       -> #121212   near-black ink
       --muted      oklch(94% .005 95)   -> #ecebe7
       --border     oklch(88% .005 95)   -> #d8d7d4
       --radius     .5rem

   Typefaces are the site's: DM Sans for text, Space Mono for code. Both are
   loaded from Google Fonts with full local fallbacks, so the file still prints
   correctly on a machine with no network.
--------------------------------------------------------------------------- */

@page { size: A4; margin: 18mm 16mm 20mm 16mm; }

:root {
  --brand:      #f46622;
  --brand-deep: #c74d15;
  --ink:        #121212;
  --muted:      #555555;
  --paper:      #f6f4ee;
  --card:       #ffffff;
  --rule:       #d8d7d4;
  --soft:       #ecebe7;
  --radius:     0.5rem;

  --sans: "DM Sans", "Helvetica Neue", Arial, sans-serif;
  --mono: "Space Mono", "SF Mono", Menlo, Consolas, monospace;
}

* { box-sizing: border-box; }

body {
  font: 10.6pt/1.6 var(--sans);
  color: var(--ink);
  max-width: 175mm;
  margin: 0 auto;
  padding: 12mm 6mm;
  background: var(--card);
  -webkit-font-smoothing: antialiased;
}

/* ---- headings ---------------------------------------------------------- */
/* Each week opens a new page with a rule in the brand orange. */
h1 {
  font-family: var(--sans);
  font-size: 21pt;
  font-weight: 700;
  letter-spacing: -0.015em;
  margin: 0 0 5mm;
  padding-bottom: 2.5mm;
  border-bottom: 2.5px solid var(--brand);
  page-break-before: always;
  page-break-after: avoid;
}
h1.first { page-break-before: avoid; }

h2 {
  font-family: var(--sans);
  font-size: 13.5pt;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin: 8mm 0 2.5mm;
  padding-bottom: 1.2mm;
  border-bottom: 1px solid var(--rule);
  page-break-after: avoid;
}

/* h3 carries a small orange tick in the margin - the site uses the accent
   the same way, as a marker rather than as a fill. */
h3 {
  font-family: var(--sans);
  font-size: 11.5pt;
  font-weight: 700;
  margin: 6mm 0 1.5mm;
  padding-left: 3.5mm;
  border-left: 2.5px solid var(--brand);
  page-break-after: avoid;
}

p, li { orphans: 3; widows: 3; }
p { margin: 0 0 2.6mm; }
ul, ol { margin: 0 0 3mm; padding-left: 6mm; }
li { margin-bottom: 1.2mm; }
li::marker { color: var(--brand-deep); }
strong { font-weight: 700; }
em { font-style: italic; }

a { color: var(--brand-deep); text-decoration: none; }

/* ---- instructor notes -------------------------------------------------- */
/* The one place the brand colour fills rather than accents, so an instructor
   can find their own notes by eye while teaching. */
blockquote {
  margin: 3.5mm 0;
  padding: 3mm 4mm;
  background: #fdf3ec;
  border-left: 3.5px solid var(--brand);
  border-radius: 0 var(--radius) var(--radius) 0;
  font-size: 9.6pt;
  line-height: 1.55;
  page-break-inside: avoid;
}
blockquote p { margin: 0 0 1.6mm; }
blockquote p:last-child { margin-bottom: 0; }
blockquote code { background: #f6e3d6; }
blockquote strong { color: var(--brand-deep); }
/* A quote nested in a quote is a student-facing aside inside an instructor
   note; drop the fill so the two do not stack into mud. */
blockquote blockquote {
  background: transparent;
  border-left-color: var(--rule);
}

/* ---- code -------------------------------------------------------------- */
code {
  font-family: var(--mono);
  font-size: 8.6pt;
  background: var(--soft);
  padding: 0.4mm 1.1mm;
  border-radius: 3px;
}
pre {
  background: var(--paper);
  border: 1px solid var(--rule);
  border-left: 2.5px solid var(--brand);
  border-radius: var(--radius);
  padding: 3mm 3.5mm;
  margin: 3mm 0;
  overflow-x: auto;
  page-break-inside: avoid;
}
pre code {
  background: none;
  padding: 0;
  font-size: 8.4pt;
  line-height: 1.5;
  white-space: pre;
}

/* ---- tables ------------------------------------------------------------ */
table {
  border-collapse: collapse;
  width: 100%;
  margin: 3.5mm 0;
  font-size: 9.3pt;
  page-break-inside: avoid;
}
th, td {
  border: 1px solid var(--rule);
  padding: 1.8mm 2.5mm;
  text-align: left;
  vertical-align: top;
}
th {
  background: var(--ink);
  color: var(--paper);
  font-weight: 700;
  letter-spacing: 0.02em;
}
tbody tr:nth-child(even) { background: var(--paper); }

hr { border: 0; border-top: 1px solid var(--rule); margin: 6mm 0; }

/* ---- cover ------------------------------------------------------------- */
.cover {
  padding-top: 45mm;
  page-break-after: always;
}
.cover .brand {
  font-family: var(--mono);
  font-size: 10pt;
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--brand);
  margin-bottom: 14mm;
}
.cover .title {
  font-family: var(--sans);
  font-size: 34pt;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.08;
  margin-bottom: 6mm;
}
.cover .sub {
  font-size: 13pt;
  color: var(--muted);
  margin-bottom: 4mm;
}
.cover .rule {
  width: 42mm;
  border-top: 3px solid var(--brand);
  margin: 12mm 0;
}
.cover .meta {
  font-size: 9.8pt;
  color: var(--muted);
  line-height: 1.95;
}
.cover .meta strong { color: var(--ink); }

/* ---- contents ---------------------------------------------------------- */
.contents { page-break-after: always; }
.contents h1 { page-break-before: avoid; }
.contents ol {
  list-style: none;
  padding-left: 0;
  margin-top: 6mm;
  counter-reset: wk -1;
}
.contents li {
  margin-bottom: 3.4mm;
  padding-left: 11mm;
  position: relative;
}
/* The numbers run 00-08: "how to use this" is 00, then one per week. */
.contents li::before {
  counter-increment: wk;
  content: "0" counter(wk);
  position: absolute;
  left: 0;
  top: 0.2mm;
  font-family: var(--mono);
  font-size: 9pt;
  font-weight: 700;
  color: var(--brand);
}
.contents .wk { font-weight: 700; font-size: 11pt; }
.contents .what { color: var(--muted); font-size: 9.8pt; }

/* ---- screen-only helper ------------------------------------------------ */
.screen-note {
  background: #fdf3ec;
  border: 1px solid var(--brand);
  border-radius: var(--radius);
  padding: 3mm 4mm;
  margin-bottom: 6mm;
  font-size: 9.5pt;
}
@media print { .screen-note { display: none; } }
"""

# --- webfonts -------------------------------------------------------------
# The brand faces are DM Sans and Space Mono (the same two the site loads).
# We fetch them once and inline them as base64 so the HTML is self-contained:
# headless Chrome otherwise prints before a network font arrives, and the PDF
# silently falls back to Arial. Cached in teaching/.fonts.css after the first
# run; delete that file to re-fetch. With no network we skip the inlining and
# the CSS fallback stack (Helvetica/Arial) takes over, which still prints fine.
FONT_CSS_URL = (
    "https://fonts.googleapis.com/css2"
    "?family=DM+Sans:wght@400;500;700&family=Space+Mono:wght@400;700&display=swap"
)
FONT_CACHE = os.path.join(HERE, ".fonts.css")
_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def _inline_fonts():
    """Return @font-face rules with the woff2 files embedded, or "" if offline."""
    if os.path.exists(FONT_CACHE):
        return open(FONT_CACHE, encoding="utf-8").read()

    import base64
    import urllib.request

    def _get(url):
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read()

    try:
        css = _get(FONT_CSS_URL).decode("utf-8")
        for url in sorted(set(re.findall(r"https://fonts\.gstatic\.com[^)]+?\.woff2", css))):
            b64 = base64.b64encode(_get(url)).decode("ascii")
            css = css.replace(url, f"data:font/woff2;base64,{b64}")
    except Exception as e:                       # offline, or Google is down
        print(f"  note: could not fetch webfonts ({type(e).__name__}); "
              f"falling back to system fonts")
        return ""

    open(FONT_CACHE, "w", encoding="utf-8").write(css)
    return css



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
    font_css = _inline_fonts()
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
<style>{font_css}</style>
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
  <div class="brand">Buildr Labs</div>
  <div class="title">Ship Production<br>AI&nbsp;Systems</div>
  <div class="sub">Phase 2 · Teaching Guide</div>
  <div class="rule"></div>
  <div class="meta">
    Eight weeks, from a loop in a file<br>
    to something a company can run.<br><br>
    <strong>Instructor notes included.</strong><br>
    Every command in this guide has been run;<br>
    the output shown is the output it printed.
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
