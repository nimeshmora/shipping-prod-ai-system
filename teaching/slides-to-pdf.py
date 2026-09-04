#!/usr/bin/env python3
"""Print a slide deck to PDF, one slide per landscape page, exactly as shown.

The deck is a JS slideshow: only the slide with .on is visible, and a scaler
transform fits it to the window. For print we override both - every slide
visible, at its true 1280x720, one per page - then let Chrome paginate.

    python3 teaching/slides-to-pdf.py teaching/week-01-slides-v2.html

Writes <same-name>.pdf beside it. Needs Google Chrome.
"""
import os, re, subprocess, sys, tempfile

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# 1280x720 at 96dpi = 13.333in x 7.5in. Chrome's --print-to-pdf honours @page.
PRINT_CSS = """
<style id="print-only">
@media print {
  /* the stage and scaler exist to fit ONE slide to the window; undo both */
  html, body { height:auto !important; overflow:visible !important;
               background:#0d0d0f !important; }
  #stage { position:static !important; display:block !important; inset:auto !important; }
  #scaler { width:1280px !important; height:auto !important;
            transform:none !important; }
  /* every slide visible, at true size, one per page */
  section.slide { display:flex !important; position:relative !important;
                  width:1280px !important; height:720px !important;
                  opacity:1 !important; visibility:visible !important;
                  page-break-after:always; break-after:page;
                  transform:none !important; }
  section.slide:last-of-type { page-break-after:auto; break-after:auto; }
  /* chrome that is not part of a slide */
  #notes, #help, #hint { display:none !important; }
  @page { size: 1280px 720px; margin: 0; }
}
</style>
<script>
// The deck's own script re-applies .on and a scaler transform on load and on
// resize. For printing we neutralise it once the page is ready.
window.addEventListener('load', function () {
  document.querySelectorAll('section.slide').forEach(function (s) {
    s.classList.add('on');
  });
  var sc = document.getElementById('scaler');
  if (sc) { sc.style.transform = 'none'; sc.style.height = 'auto'; }
  document.title = 'READY';
});
</script>
"""

def main(src):
    html = open(src, encoding='utf-8').read()
    n = len(re.findall(r'<section class="slide', html))
    out = os.path.splitext(src)[0] + '.pdf'
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False,
                                     dir=os.path.dirname(os.path.abspath(src)),
                                     encoding='utf-8') as f:
        f.write(html + PRINT_CSS)
        tmp = f.name
    try:
        subprocess.run(
            [CHROME, '--headless', '--disable-gpu', '--no-pdf-header-footer',
             '--virtual-time-budget=30000', '--print-to-pdf=' + out,
             'file://' + tmp],
            capture_output=True, timeout=300)
    finally:
        os.unlink(tmp)
    if not os.path.exists(out):
        print('failed - no PDF written'); return 1
    size = os.path.getsize(out)
    print('%s\n  %d slides in the deck\n  %.1f MB' % (out, n, size / 1e6))
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else 'teaching/week-01-slides-v2.html'))
