"""Strict audit of built site in docs/: links, anchors, meta, hreflang, images, JSON-LD, lang pairing, sitemap, sizes.
Usage: python3 tools/audit.py"""
import re, json, sys, os
from pathlib import Path
from html.parser import HTMLParser
D = Path(__file__).resolve().parent.parent / "docs"
pages = sorted(p for p in D.rglob("index.html"))
pages.append(D/"404.html")
issues = []
def add(sev, page, msg): issues.append((sev, str(page.relative_to(D)) if isinstance(page, Path) else page, msg))

class P(HTMLParser):
    def __init__(s): super().__init__(); s.tags=[]; s.ids=set(); s.text=[]; s.in_script=False; s.title=""; s._t=False
    def handle_starttag(s, t, a):
        a=dict(a); s.tags.append((t,a))
        if 'id' in a: s.ids.add(a['id'])
        if t=='title': s._t=True
        if t in('script','style'): s.in_script=True
    def handle_endtag(s,t):
        if t=='title': s._t=False
        if t in('script','style'): s.in_script=False
    def handle_data(s,d):
        if s._t: s.title+=d
        elif not s.in_script: s.text.append(d)

parsed={}
for p in pages:
    h=p.read_text(); x=P(); x.feed(h); parsed[p]=(h,x)

def url_to_file(u):
    u=u.split('#')[0].split('?')[0]
    if not u.startswith('/'): return None
    f=D/u.lstrip('/')
    if u.endswith('/'): f=f/'index.html'
    return f

titles={}; descs={}
for p,(h,x) in parsed.items():
    legacy = 'http-equiv="refresh"' in h
    if legacy: continue
    t=x.title.strip()
    if not t: add('HIGH',p,'missing <title>')
    elif len(t)>65: add('LOW',p,f'title {len(t)} chars: {t}')
    titles.setdefault(t,[]).append(p)
    metas={a.get('name') or a.get('property'):a.get('content') for tg,a in x.tags if tg=='meta'}
    d=metas.get('description')
    if not d: add('MED',p,'missing meta description')
    else:
        descs.setdefault(d,[]).append(p)
        if len(d)>165: add('LOW',p,f'description {len(d)} chars')
        if len(d)<70: add('LOW',p,f'description short {len(d)}')
    for k in ['og:title','og:description','og:image','og:url']:
        if not metas.get(k): add('MED',p,f'missing {k}')
    can=[a.get('href') for tg,a in x.tags if tg=='link' and a.get('rel')=='canonical']
    if p.name!='404.html':
        if not can: add('MED',p,'missing canonical')
        alts={a.get('hreflang'):a.get('href') for tg,a in x.tags if tg=='link' and a.get('rel')=='alternate'}
        if not ('vi' in alts and 'en' in alts): add('MED',p,f'hreflang incomplete {list(alts)}')
        for hl,u in alts.items():
            if u and u.startswith('https://ttpfoods.vn'):
                f=url_to_file(u.replace('https://ttpfoods.vn',''))
                if f and not f.exists(): add('HIGH',p,f'hreflang {hl} -> missing {u}')
    hl=[a for tg,a in x.tags if tg=='html']
    lang=hl[0].get('lang') if hl else None
    exp='en' if '/en/' in '/'+str(p.relative_to(D)) else 'vi'
    if lang!=exp: add('HIGH',p,f'html lang={lang} expected {exp}')
    # links
    for tg,a in x.tags:
        for attr in ('href','src','srcset'):
            v=a.get(attr)
            if not v: continue
            for u in ([s.strip().split(' ')[0] for s in v.split(',')] if attr=='srcset' else [v]):
                if u.startswith(('mailto:','tel:','javascript:','data:')): 
                    if u.startswith('tel:') and u!='tel:+84904004199': add('HIGH',p,f'unexpected tel {u}')
                    continue
                if u.startswith('#'):
                    if len(u)>1 and u[1:] not in x.ids: add('HIGH',p,f'broken in-page anchor {u}')
                    continue
                if u.startswith('http'):
                    if tg=='a' and a.get('target')=='_blank' and 'noopener' not in (a.get('rel') or ''): add('MED',p,f'target=_blank without noopener {u}')
                    if u.startswith('http://'): add('MED',p,f'insecure http link {u}')
                    continue
                f=url_to_file(u)
                if f is None: add('MED',p,f'relative url {u}'); continue
                if not f.exists(): add('HIGH',p,f'broken link {u}')
                elif '#' in u and f.suffix=='.html':
                    frag=u.split('#')[1]
                    if frag and frag not in parsed.get(f,(None,P()))[1].ids:
                        hh=f.read_text()
                        if f'id="{frag}"' not in hh: add('HIGH',p,f'broken anchor {u}')
        if tg=='img':
            if 'alt' not in a: add('HIGH',p,f'img without alt {a.get("src")}')
            if not (a.get('width') and a.get('height')): add('LOW',p,f'img without dimensions {a.get("src")}')
        if tg=='a' and not a.get('href'): add('MED',p,'a without href')
        if tg=='iframe' and not a.get('title'): add('MED',p,'iframe without title')
    # JSON-LD
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',h,re.S):
        try: json.loads(m.group(1))
        except Exception as e: add('HIGH',p,f'invalid JSON-LD: {e}')
    txt=' '.join(x.text)
    for bad in ['0968','383 499','Đang cập nhật','TODO','Lorem','undefined','None','{{','{%','đại diện pháp luật','Hai Bà Trưng']:
        if bad in txt or (bad in ('{{','{%') and bad in h): add('HIGH',p,f'forbidden text "{bad}"')
    # lang leftovers
    if exp=='en' and re.search(r'[ạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỷỹỵđ]{1}',txt):
        sample=re.findall(r'\S*[ạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỷỹỵđ]\S*',txt)[:6]
        add('MED',p,f'Vietnamese text on EN page: {sample}')
    h1=[1 for tg,a in x.tags if tg=='h1']
    if len(h1)!=1: add('HIGH',p,f'{len(h1)} h1')
    kb=len(h.encode())/1024
    if kb>120: add('LOW',p,f'html {kb:.0f} KB')
for t,ps in titles.items():
    if len(ps)>1: add('MED',ps[0],f'duplicate title on {len(ps)} pages: {t}')
for d,ps in descs.items():
    if len(ps)>1: add('LOW',ps[0],f'duplicate description on {[str(q.relative_to(D)) for q in ps]}')
# sitemap
sm=(D/'sitemap.xml').read_text(); locs=re.findall(r'<loc>([^<]+)',sm)
for u in locs:
    f=url_to_file(u.replace('https://ttpfoods.vn',''))
    if not f or not f.exists(): add('HIGH','sitemap.xml',f'missing {u}')
real=[p for p in parsed if 'http-equiv="refresh"' not in parsed[p][0] and p.name!='404.html']
if len(locs)!=len(real): add('MED','sitemap.xml',f'{len(locs)} locs vs {len(real)} pages')
rb=(D/'robots.txt').read_text()
if 'Sitemap:' not in rb: add('MED','robots.txt','no Sitemap line')
# big assets
for f in D.rglob('*'):
    if f.is_file() and f.suffix in ('.jpg','.png','.webp') and f.stat().st_size>250*1024: add('LOW',f,f'large image {f.stat().st_size//1024} KB')
order={'HIGH':0,'MED':1,'LOW':2}
for s,p,m in sorted(issues,key=lambda i:(order[i[0]],i[1])): print(f'{s:4} {p}: {m}')
print(f'\n{len(real)} pages audited, {sum(1 for i in issues if i[0]=="HIGH")} high, {sum(1 for i in issues if i[0]=="MED")} med, {sum(1 for i in issues if i[0]=="LOW")} low')
