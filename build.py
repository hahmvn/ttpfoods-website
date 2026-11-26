#!/usr/bin/env python3
"""Build the ttpfoods.vn static site (v2).

    python3 build.py            # build into docs/
    python3 build.py --check    # build + verify links/assets (exit 1 on problems)

Sources live in src/:
  layouts/   Jinja base layout (head, header, footer)
  pages/     one template per page; bilingual markup written once with
             <span class="l-vi">…</span><span class="l-en">…</span> (or class="… l-vi")
  partials/  shared fragments
  assets/    css, js, fonts, img  (copied to docs/assets, images also get .webp)
  static/    files copied to the site root (CNAME, favicon.ico, manifest)

Every page is rendered twice (vi at /…, en at /en/…); the build removes the other
language's markup, so the output pages are single-language and SEO friendly.
Requires: Python 3.9+, Jinja2, Pillow.
"""
import hashlib, json, os, re, shutil, sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup
from PIL import Image

ROOT = Path(__file__).resolve().parent
SRC, OUT = ROOT / "src", ROOT / "docs"
SITE = "https://ttpfoods.vn"
LANGS = ("vi", "en")

# ---------------------------------------------------------------------------
# Pages: key -> template, URL per language, <title>/<meta description> per language
# ---------------------------------------------------------------------------
PAGES = {
    "home": dict(tpl="home.html", url={"vi": "/", "en": "/en/"},
                 title={"vi": "TTP Foods | Nguyên liệu, phụ gia & tư vấn ngành thực phẩm",
                        "en": "TTP Foods | Food ingredients, additives & consulting"},
                 desc={"vi": "TTP Foods – nhà cung cấp nguyên liệu, phụ gia, sản phẩm và dịch vụ tư vấn cho ngành Công nghiệp Thực phẩm. Kết nối nguồn cung - cầu giữa Việt Nam và thế giới.",
                       "en": "TTP Foods supplies food ingredients, additives, foods and consulting services to the food industry, connecting Vietnam with global supply and demand."}),
    "about": dict(tpl="about.html", url={"vi": "/gioi-thieu/", "en": "/en/about/"},
                  title={"vi": "Giới thiệu TTP Foods | Sứ mệnh, tầm nhìn & giá trị",
                         "en": "About TTP Foods | Mission, vision & values"},
                  desc={"vi": "TTP Foods là nhà cung cấp nguyên liệu, phụ gia và dịch vụ cho ngành thực phẩm – đối tác tin cậy của các nhà sản xuất thực phẩm, dược phẩm Việt Nam và quốc tế.",
                        "en": "TTP Foods supplies ingredients, additives and services to the food industry – a trusted partner of Vietnamese and international food and pharmaceutical manufacturers."}),
    "leadership": dict(tpl="leadership.html", url={"vi": "/ban-lanh-dao/", "en": "/en/leadership/"},
                       title={"vi": "Ban lãnh đạo | TTP Foods", "en": "Leadership | TTP Foods"},
                       desc={"vi": "Đội ngũ lãnh đạo TTP Foods với nhiều năm kinh nghiệm tại Nestlé, Mondelez, Cục An toàn thực phẩm, Sữa Hà Nội và các doanh nghiệp hàng đầu.",
                             "en": "TTP Foods' leadership team, with years of experience at Nestlé, Mondelez, the Vietnam Food Administration, Hanoi Milk and other leading companies."}),
    "products": dict(tpl="products.html", url={"vi": "/san-pham/", "en": "/en/products/"},
                     title={"vi": "Sản phẩm – Nguyên liệu thực phẩm | TTP Foods", "en": "Products – Food ingredients | TTP Foods"},
                     desc={"vi": "Kem đặc MILKA, gelatin & collagen E-King, nhân bánh, mứt, chất nhũ hoá, kem trang trí Farina, non-dairy creamer và đậu tương cho ngành bánh kẹo, sữa, đồ uống, dược phẩm.",
                           "en": "MILKA condensed cream, E-King gelatin & collagen, filling pastes, fruit jams, cake gel, Farina topping cream, non-dairy creamer and soybean for the food and pharma industries."}),
    "services": dict(tpl="services.html", url={"vi": "/dich-vu/", "en": "/en/services/"},
                     title={"vi": "Dịch vụ tư vấn ngành thực phẩm | TTP Foods", "en": "Food industry consulting services | TTP Foods"},
                     desc={"vi": "Tư vấn ISO 22000, HACCP, GMP; tối ưu hoá nhà máy; công bố chất lượng, đăng ký sản phẩm; xúc tiến xuất khẩu thực phẩm.",
                           "en": "Consulting on ISO 22000, HACCP and GMP, factory optimization, product declaration and registration, and food export promotion."}),
    "contact": dict(tpl="contact.html", url={"vi": "/lien-he/", "en": "/en/contact/"},
                    title={"vi": "Liên hệ | TTP Foods", "en": "Contact | TTP Foods"},
                    desc={"vi": "Liên hệ TTP Foods: 14B Hàn Thuyên, Phường Hai Bà Trưng, Hà Nội · 0904 004 199 · 0968 383 499 · info@ttpfoods.vn",
                          "en": "Contact TTP Foods: 14B Han Thuyen St., Hai Ba Trung Ward, Hanoi · +84 904 004 199 · +84 968 383 499 · info@ttpfoods.vn"}),
}
NAV = ["about", "leadership", "products", "services", "contact"]
NAV_LABEL = {"home": ("Trang chủ", "Home"), "about": ("Giới thiệu", "About us"), "leadership": ("Ban lãnh đạo", "Leadership"),
             "products": ("Sản phẩm", "Products"), "services": ("Dịch vụ tư vấn", "Consulting"), "contact": ("Liên hệ", "Contact")}

# Old CMS URLs (still in search engines/bookmarks) -> new pages
LEGACY = {
    "/vi/": "home", "/vi/gioi-thieu/": "about", "/vi/su-menh/": "about", "/vi/tam-nhin/": "about",
    "/vi/lien-he/": "contact", "/vi/tu-van-san-xuat/": "services", "/vi/search/": "products",
    "/en/gioi-thieu/": "about", "/en/su-menh/": "about", "/en/tam-nhin/": "about",
    "/en/lien-he/": "contact", "/en/tu-van-san-xuat/": "services", "/en/search/": "products",
}


# ---------------------------------------------------------------------------
# Language stripping
# ---------------------------------------------------------------------------
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
TAG_RE = re.compile(r"<!--.*?-->|<(/?)([a-zA-Z][\w-]*)((?:[^>\"']|\"[^\"]*\"|'[^']*')*)>", re.S)
CLASS_RE = re.compile(r"""\sclass=(["'])(.*?)\1""", re.S)


def strip_lang(html, lang):
    """Remove elements marked with the other language; unwrap/clean the current one."""
    other = "l-en" if lang == "vi" else "l-vi"
    mine = "l-" + lang
    out, pos, stack, skip_depth = [], 0, [], None
    for m in TAG_RE.finditer(html):
        if m.start() < pos:  # inside a <script>/<style> block already copied
            continue
        if m.group(0).startswith("<!--"):
            if skip_depth is None:
                out.append(html[pos:m.end()])
            pos = m.end()
            continue
        closing, name, attrs = m.group(1), m.group(2).lower(), m.group(3)
        if skip_depth is None:
            out.append(html[pos:m.start()])
        pos = m.end()
        if name in ("script", "style") and not closing:
            # copy raw text untouched up to the closing tag
            end = html.lower().find(f"</{name}", m.end())
            end = html.find(">", end) + 1
            if skip_depth is None:
                out.append(html[m.start():end])
            pos = end
            continue
        if closing:
            if not stack:
                continue
            tag, action = stack.pop()
            if skip_depth is not None:
                if len(stack) < skip_depth:
                    skip_depth = None
                continue
            if action != "unwrap":
                out.append(m.group(0))
            continue
        selfclosing = name in VOID or attrs.rstrip().endswith("/")
        if skip_depth is not None:
            if not selfclosing:
                stack.append((name, "skip"))
            continue
        cm = CLASS_RE.search(attrs)
        classes = cm.group(2).split() if cm else []
        if other in classes:
            if not selfclosing:
                stack.append((name, "skip"))
                skip_depth = len(stack)
            continue
        tag_text = m.group(0)
        action = "keep"
        if mine in classes:
            rest = [c for c in classes if c != mine]
            if name == "span" and not rest and len(CLASS_RE.sub("", attrs).strip()) == 0:
                action = "unwrap"
                tag_text = ""
            else:
                new_attr = f' class="{" ".join(rest)}"' if rest else ""
                tag_text = tag_text.replace(cm.group(0), new_attr, 1)
        out.append(tag_text)
        if not selfclosing:
            stack.append((name, action))
    if skip_depth is None:
        out.append(html[pos:])
    return "".join(out)


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------
def build_assets():
    shutil.copytree(SRC / "assets", OUT / "assets")
    made = 0
    for p in (OUT / "assets" / "img").rglob("*"):
        if p.suffix.lower() in (".png", ".jpg", ".jpeg") and "icon" not in p.name and "favicon" not in p.name:
            im = Image.open(p)
            im.save(p.with_suffix(".webp"), "WEBP", quality=82, method=6)
            made += 1
    for f in (SRC / "static").iterdir():
        shutil.copy(f, OUT / f.name)
    (OUT / ".nojekyll").write_text("")
    return made


def file_hash(rel):
    return hashlib.md5((OUT / rel.lstrip("/")).read_bytes()).hexdigest()[:8]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def make_env():
    env = Environment(loader=FileSystemLoader(str(SRC)), autoescape=True, undefined=StrictUndefined,
                      trim_blocks=True, lstrip_blocks=True)
    return env


def picture(src, alt, cls="", sizes=None, lazy=True, width=None, height=None):
    """<picture> with WebP + original fallback. src is relative to /assets/img/."""
    base = "/assets/img/" + src
    webp = re.sub(r"\.(png|jpe?g)$", ".webp", base)
    attrs = f' class="{cls}"' if cls else ""
    dims = ""
    if width is None:
        try:
            w, h = Image.open(SRC / "assets" / "img" / src).size
            dims = f' width="{w}" height="{h}"'
        except Exception:
            pass
    else:
        dims = f' width="{width}" height="{height}"'
    loading = ' loading="lazy" decoding="async"' if lazy else ""
    return Markup(f'<picture><source srcset="{webp}" type="image/webp">'
                  f'<img src="{base}" alt="{Markup.escape(alt)}"{attrs}{dims}{loading}></picture>')


def render_all(env, versions):
    built = []
    today = date.today().isoformat()
    for key, page in PAGES.items():
        for lang in LANGS:
            other = "en" if lang == "vi" else "vi"
            ctx = dict(
                lang=lang, other_lang=other, page_key=key, page=page, pages=PAGES, nav=NAV, nav_label=NAV_LABEL,
                site=SITE, year=date.today().year, v=versions,
                url=lambda k, l=lang: PAGES[k]["url"][l],
                t=lambda vi, en, l=lang: vi if l == "vi" else en,
                picture=picture,
            )
            html = env.get_template("pages/" + page["tpl"]).render(**ctx)
            html = strip_lang(html, lang)
            html = re.sub(r"\n\s*\n+", "\n", html)
            dest = OUT / page["url"][lang].lstrip("/") / "index.html"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html, encoding="utf-8")
            built.append((key, lang, page["url"][lang]))
    # 404 (served for any missing path, so it is bilingual on one page)
    html = env.get_template("pages/404.html").render(
        lang="vi", other_lang="en", page_key="404", page=dict(url={"vi": "/404.html", "en": "/404.html"},
        title={"vi": "Không tìm thấy trang | TTP Foods", "en": "Page not found | TTP Foods"}, desc={"vi": "", "en": ""}),
        pages=PAGES, nav=NAV, nav_label=NAV_LABEL, site=SITE, year=date.today().year, v=versions,
        url=lambda k: PAGES[k]["url"]["vi"], t=lambda vi, en: vi, picture=picture)
    (OUT / "404.html").write_text(re.sub(r"\n\s*\n+", "\n", html), encoding="utf-8")
    # Legacy redirects (old CMS pages + old product/category URLs -> new pages)
    legacy = {old: (PAGES[key]["url"]["en" if old.startswith("/en/") else "vi"]) for old, key in LEGACY.items()}
    lp = SRC / "legacy-products.json"
    if lp.exists():
        for old, info in json.loads(lp.read_text(encoding="utf-8")).items():
            legacy[old] = PAGES["products"]["url"][info["lang"]] + (("#" + info["hash"]) if info["hash"] else "")
    for old, target in legacy.items():
        lang = "en" if old.startswith("/en/") else "vi"
        d = OUT / old.lstrip("/")
        if (d / "index.html").exists():
            continue
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>TTP Foods</title>'
            f'<meta name="robots" content="noindex"><link rel="canonical" href="{SITE}{target.split("#")[0]}">'
            f'<meta http-equiv="refresh" content="0; url={target}"></head>'
            f'<body><a href="{target}">{SITE}{target}</a></body></html>', encoding="utf-8")
    # sitemap + robots
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for key, page in PAGES.items():
        for lang in LANGS:
            sm.append(f"  <url><loc>{SITE}{page['url'][lang]}</loc><lastmod>{today}</lastmod>")
            for l2 in LANGS:
                sm.append(f'    <xhtml:link rel="alternate" hreflang="{l2}" href="{SITE}{page["url"][l2]}"/>')
            sm.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{page["url"]["vi"]}"/>')
            sm.append("  </url>")
    sm.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    return built, len(legacy)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------
def check():
    problems = []
    for f in OUT.rglob("*.html"):
        html = f.read_text(encoding="utf-8")
        rel = "/" + str(f.relative_to(OUT)).replace("index.html", "")
        if re.search(r'class="[^"]*\bl-(vi|en)\b', html):
            problems.append(f"{rel}: leftover language class")
        if "Đang cập nhật" in html or "To be updated" in html:
            problems.append(f"{rel}: placeholder text")
        for attr, ref in re.findall(r'(href|src|srcset)="([^"#?]+)', html):
            if ref.startswith(("http", "mailto:", "tel:", "data:")) or not ref.startswith("/"):
                continue
            target = OUT / ref.lstrip("/")
            if ref.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                problems.append(f"{rel}: missing {attr} {ref}")
        if f.name == "index.html" and "/vi/" not in rel and "noindex" not in html:
            if html.count("<h1") != 1:
                problems.append(f"{rel}: expected exactly one <h1>, found {html.count('<h1')}")
            for img in re.findall(r"<img\b[^>]*>", html):
                if "alt=" not in img:
                    problems.append(f"{rel}: <img> without alt")
    for css in (OUT / "assets").rglob("*.css"):
        for ref in re.findall(r'url\(["\']?(/[^"\')]+)', css.read_text()):
            if not (OUT / ref.lstrip("/")).exists():
                problems.append(f"{css.name}: missing url {ref}")
    return problems


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    webps = build_assets()
    versions = {"css": file_hash("/assets/css/style.css"), "js": file_hash("/assets/js/main.js")}
    built, n_legacy = render_all(make_env(), versions)
    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"Built {len(built)} pages + 404 + {n_legacy} legacy redirects, {webps} webp images, {total // 1024} KB -> {OUT}")
    if "--check" in sys.argv:
        problems = check()
        for p in problems:
            print("  ✗", p)
        print("Check:", "OK" if not problems else f"{len(problems)} problem(s)")
        sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
