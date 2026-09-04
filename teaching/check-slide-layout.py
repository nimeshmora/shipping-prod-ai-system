#!/usr/bin/env python3
"""Check every slide in a deck actually fits its stage, by rendering it.

A height-only check is not enough: it misses text wrapping inside a too-narrow
grid column, and it misses content drawn on top of the bottom progress rail.
Both of those happened, and both were invisible to a scrollHeight check.

    python3 teaching/check-slide-layout.py teaching/week-01-slides-v2.html

Needs Google Chrome. Exits non-zero if any slide is cramped.
"""
import re, subprocess, sys, tempfile, os

PROBE = r"""
<script>
window.addEventListener('load',()=>{
  const ss=document.querySelectorAll('section.slide');
  const bad=[];
  ss.forEach((s,i)=>{
    ss.forEach(x=>x.classList.remove('on')); s.classList.add('on');
    const sr=s.getBoundingClientRect();
    const rail=s.querySelector('.rail');
    const railTop = rail ? rail.getBoundingClientRect().top : sr.bottom;
    let lowest=-1, lowestCls='', widest=-1, widestCls='', leftmost=1e9, leftCls='';
    s.querySelectorAll('.body *, h1, h2').forEach(el=>{
      const r=el.getBoundingClientRect();
      if(r.width<2||r.height<2) return;
      if(el.closest('.say')) return;
      const cls=(el.className||el.tagName).toString().trim().slice(0,22);
      if(r.bottom>lowest){lowest=r.bottom;lowestCls=cls;}
      if(r.right>widest){widest=r.right;widestCls=cls;}
      if(r.left<leftmost){leftmost=r.left;leftCls=cls;}
    });
    const railGap=railTop-lowest, rightGap=sr.right-widest, leftGap=leftmost-sr.left;
    const p=[];
    if(railGap<6)  p.push('hits the bottom rail (gap '+railGap.toFixed(0)+'px) ['+lowestCls+']');
    if(rightGap<0) p.push('past the right edge ('+(-rightGap).toFixed(0)+'px) ['+widestCls+']');
    if(leftGap<0)  p.push('past the left edge ('+(-leftGap).toFixed(0)+'px) ['+leftCls+']');
    if(s.scrollHeight>722) p.push('taller than the stage ('+s.scrollHeight+'px)');
    if(p.length) bad.push('  slide '+(i+1)+': '+p.join('; '));
  });
  const pre=document.createElement('pre'); pre.id='out';
  pre.textContent='SLIDES='+ss.length+'\nBAD='+bad.length+'\n'+bad.join('\n');
  document.body.appendChild(pre);
});
</script>
"""

CHROME = ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")

def main(path):
    html = open(path, encoding='utf-8').read()
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False,
                                     encoding='utf-8') as f:
        f.write(html + PROBE)
        probe = f.name
    try:
        out = subprocess.run(
            [CHROME, '--headless', '--disable-gpu', '--virtual-time-budget=20000',
             '--window-size=1400,900', '--dump-dom', 'file://' + probe],
            capture_output=True, text=True, timeout=180).stdout
    finally:
        os.unlink(probe)
    m = re.search(r'<pre id="out">([\s\S]*?)</pre>', out)
    if not m:
        print('probe did not run - is Chrome installed?'); return 2
    report = m.group(1)
    print(report)
    n = re.search(r'BAD=(\d+)', report)
    return 1 if n and int(n.group(1)) else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else 'teaching/week-01-slides-v2.html'))
