#!/usr/bin/env python3
"""
N.E.A.T Microcredit – static site generator.

Plain static HTML is written to ./html (no framework needed to host it).
Header, footer, navigation and every page live here so they stay consistent.

    python3 build.py          # regenerate all pages in ./html
    cd html && python3 -m http.server 8080   # preview at http://localhost:8080

Legal pages (privacy / terms / disclaimer) and the About story are pulled
verbatim from ./_original-version so no wording is invented or lost.
Requires:  pip install beautifulsoup4 lxml
"""
import re
import html as html_lib
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
OUT = ROOT / "html"
ORIG = ROOT / "_original-version"
BASE = "https://neatmicrocredit.com.ng/"   # assumption: site is served from the domain root

# ----------------------------------------------------------------------------
# Verified-from-existing-site company facts (single source of truth)
# ----------------------------------------------------------------------------
CO = dict(
    name="N.E.A.T Microcredit",
    legal="New Extension Allround Trust Limited",
    tagline="…Changing the face of business in Africa",
    address="NF 5 Oyo Road CBD, 800242 Kaduna, Nigeria.",
    phone_display="+234 803 081 1412", phone_tel="+2348030811412",
    wa_display="09096852944", wa_link="https://wa.me/2347061421985",   # NOTE: display number and link differ in the original site – flagged
    email_general="info@neatmicrocredit.com.ng", email_alt="neatmicrocredit@gmail.com",
    email_careers="careers@neatmicrocredit.com.ng",
    maps="https://www.google.com/maps/search/?api=1&query=NF+5+Oyo+Road+CBD+800242+Kaduna+Nigeria",
    webmail="https://webmail.neatmicrocredit.com.ng/",
    social=[("facebook", "Facebook", "https://www.facebook.com/share/1BA9upktqi/?mibextid=wwXIfr"),
            ("instagram", "Instagram", "https://www.instagram.com/neatmicrocredit?igsh=MWMyY2UwajEyZnI0MQ=="),
            ("x", "X (Twitter)", "https://x.com/neatmicrocred?s=11"),
            ("youtube", "YouTube", "https://youtube.com/@n.e.a.tmicroredit7136?si=1igF5Of6gig_DaMt")],
)

PRODUCTS = [  # slug, title, nav blurb, icon
    ("microFund.html", "Micro Fund", "Quick funding for urgent needs", "banknote"),
    ("sme.html", "S.M.E Fund", "Grow and expand your business", "briefcase"),
    ("assetFund.html", "Asset Fund", "Own the assets your business needs", "box"),
    ("saving.html", "Savings", "Savings, current and fixed deposit", "landmark"),
    ("advisory.html", "Business Advisory", "Guidance and capacity building", "compass"),
    ("equity.html", "Equity Investment", "Risk capital for growth", "trend"),
    ("termDeposit.html", "Term Deposit", "Fixed-term deposits, rate agreed", "clock"),
]
PRODUCT_FILES = {p[0] for p in PRODUCTS} | {"products.html"}

BRANCHES = [  # label, region, address, phone — exactly as published on the old contact page
    ("Kaduna 1", "Kaduna State", "G19 NUT Building, Mogadishu Layout, Kaduna. Nigeria", "08032901870"),
    ("Kaduna 2", "Kaduna State", "No. 83 Opposite KAPSUDA, Kachia Road, Sabon Tasha, Kaduna. Nigeria", "07064177711"),
    ("Gonin Gora (Kaduna)", "Kaduna State", "No. 2 Lamige Road, End of Sarki Obadia Junction Flat, Flat B No.5 Sarki Street, Gonin Gora, Kaduna. Nigeria", "09035991639"),
    ("Zaria Office (Kaduna)", "Kaduna State", "No. 14, No.2C Traders Plaza, Sokoto Road, MTD, Zaria", "09031897555"),
    ("Kawo (Kaduna)", "Kaduna State", "No. 5 Alhaji Sani Usman Plaza, Opp. Kawo Football Field, Sabon Birni Street, Kawo. Kaduna. Nigeria", "08141440391"),
    ("Karu Office (Abuja)", "Abuja area", "First Floor, Suite 24, Sifa Plaza, Abuja-Keffi Express Way, Sharp Corner, Mararaba Karu, Nasarawa State. Abuja. Nigeria", "08118472602"),
    ("Gwagwalada (Abuja)", "Abuja area", "Suite 22 Ojuku Ojeje Plaza, Secretariat Road, Gwagwalada, FCT, Abuja. Nigeria", "08100030640"),
    ("Suleja (Abuja)", "Abuja area", "M. Sani Plaza, Off old Barracks Road, Ungwan Gwari Junction, Suleja. Abuja. Nigeria", "08118472645"),
    ("Ilorin Office 1 (Kwara State)", "Kwara State", "Madawaki Estate, Opp Mrs. Filling Station, Beside Mabifu Diagnostic Centre, Taiwo Isale Ilorin, Kwara State.", "09116905568"),
    ("Ilorin Office 2 (Kwara State)", "Kwara State", "Close to Aflaman Petroleum, Opposite Redeemed Church, Danialu Area, Kwara State.", "07064177711"),
    ("Offa (Kwara State)", "Kwara State", "Second Floor, Abimbola Plaza, Traffic Junction, Omu-Aran Kwara State. No. 47 Olofa Way, Behind Femtech, Omu-Aran Kwara State.", "09132764430"),
    ("Omu-Aran (Kwara State)", "Kwara State", "Dr. E.A Oladipo’s House, Oasis School Building, Alakaka, Omu-Aran, Kwara State.", "08075976330"),
    ("Hadejia Rd, Kano State (1)", "Kano State", "Duplex No. 9, 11/12 Helu Plaza, France Road by Galadima, Kano State.", "09069710182"),
    ("Sabon-Gari, Kano State (2)", "Kano State", "Suite No. 2, Last Floor, Ummi Plaza Kabuga by Northwest Road, Kano State.", "09069561098"),
    ("Zoo Rd, Kano State (3)", "Kano State", "Suite No. 7, First Floor Musa Baba Plaza, Adjacent Taj Bank, Zoo Road, Kano State.", "08082306070"),
    ("Kabuga, Kano State (4)", "Kano State", "Suite No. 6, Last Floor, Khadija BBK Plaza, Along Yankaba Motor Park, Hadejia Road, Kano State.", "09071151845"),
]

# ----------------------------------------------------------------------------
# Icons (one inline sprite per page, used via <use>) – single consistent style
# ----------------------------------------------------------------------------
ICONS = {
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="M6 6l12 12M18 6L6 18"/>',
    "chev": '<path d="M6 9l6 6 6-6"/>',
    "phone": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "pin": '<path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "chat": '<path d="M21 11.5a8.5 8.5 0 0 1-12.6 7.4L3 21l2.1-5.2A8.5 8.5 0 1 1 21 11.5z"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7"/>',
    "sprout": '<path d="M12 21v-8"/><path d="M12 13c0-4 3-6 7-6 0 4-3 6-7 6z"/><path d="M12 15c0-3-2.5-5-6-5 0 3 2.5 5 6 5z"/>',
    "award": '<circle cx="12" cy="9" r="6"/><path d="M8.5 14L7 21l5-3 5 3-1.5-7"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/>',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    "banknote": '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M6 12h.01M18 12h.01"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>',
    "box": '<path d="M21 8l-9-5-9 5v8l9 5 9-5V8z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
    "landmark": '<path d="M3 10l9-6 9 6"/><path d="M5 10v8M9 10v8M15 10v8M19 10v8M3 20h18"/>',
    "compass": '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5 5-2z"/>',
    "trend": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "users": '<path d="M16 20v-1a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1"/><circle cx="9.5" cy="8" r="3.5"/><path d="M21 20v-1a4 4 0 0 0-3-3.9M16 4.1a3.5 3.5 0 0 1 0 6.8"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "book": '<path d="M4 5.5C4 4.7 4.7 4 5.5 4H12v16H5.5c-.8 0-1.5-.7-1.5-1.5v-13z"/><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H12v16h6.5c.8 0 1.5-.7 1.5-1.5v-13z"/>',
    "facebook": '<path d="M14 8h3V4h-3a4 4 0 0 0-4 4v3H7v4h3v6h4v-6h3l1-4h-4V8.5c0-.3.2-.5.5-.5z"/>',
    "instagram": '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><path d="M17.5 6.5h.01"/>',
    "x": '<path d="M4 4l16 16M20 4L4 20"/>',
    "youtube": '<rect x="2" y="6" width="20" height="12" rx="4"/><path d="M10 9.5l5 2.5-5 2.5z"/>',
    "map": '<path d="M9 4L3 6v14l6-2 6 2 6-2V4l-6 2-6-2zM9 4v14M15 6v14"/>',
}
SPRITE = ('<svg xmlns="http://www.w3.org/2000/svg" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true" focusable="false"><defs>'
          + "".join(f'<symbol id="i-{k}" viewBox="0 0 24 24">{v}</symbol>' for k, v in ICONS.items()) + "</defs></svg>")


def ic(name, extra=""):
    return f'<svg class="i {extra}" aria-hidden="true" focusable="false"><use href="#i-{name}"/></svg>'


def tel(num):  # 08031234567 -> +2348031234567
    n = re.sub(r"\D", "", num)
    return "+234" + n[1:] if n.startswith("0") else "+" + n


# ----------------------------------------------------------------------------
# Shared layout: <head>, header/nav, footer, search dialog
# ----------------------------------------------------------------------------
def head(title, desc, fname, noindex=False):
    url = BASE if fname == "index.html" else BASE + fname
    full = title if "N.E.A.T" in title else f"{title} | N.E.A.T Microcredit"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{full}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#071D3B">
<meta property="og:type" content="website">
<meta property="og:site_name" content="N.E.A.T Microcredit">
<meta property="og:title" content="{full}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}images/opt/og-share.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="images/logo.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@600;700;800&display=swap">
<link rel="stylesheet" href="css/neat.css">
<script>document.documentElement.classList.add('js')</script>
</head>"""


def header(fname):
    def cur(f):
        return ' aria-current="page"' if f == fname else ""
    in_products = fname in PRODUCT_FILES
    sub = [f'<li class="subnav__all"><a href="products.html"{cur("products.html")}>{ic("map")}<span><b>All products</b><small>Funding, savings, advisory and investment</small></span></a></li>']
    for f, t, d, icn in PRODUCTS:
        sub.append(f'<li><a href="{f}"{cur(f)}>{ic(icn)}<span><b>{t}</b><small>{d}</small></span></a></li>')
    links = [("index.html", "Home"), ("about.html", "About Us")]
    nav = ""
    for f, t in links:
        nav += f'<li><a class="nav__link" href="{f}"{cur(f)}>{t}</a></li>'
    nav += (f'<li class="has-sub"><button class="nav__trigger{" is-current" if in_products else ""}" type="button" aria-expanded="false" aria-controls="sub-products">'
            f'N.E.A.T Products {ic("chev")}</button><ul class="subnav" id="sub-products">{"".join(sub)}</ul></li>')
    for f, t in [("career.html", "Career"), ("contact.html", "Contact Us")]:
        nav += f'<li><a class="nav__link" href="{f}"{cur(f)}>{t}</a></li>'
    return f"""<a class="skip-link" href="#main">Skip to main content</a>
<div class="topbar"><div class="container">
  <p class="topbar__tagline">{CO["tagline"]}</p>
  <div class="topbar__group">
    <a href="tel:{CO["phone_tel"]}">{ic("phone")}{CO["phone_display"]}</a>
    <a href="contact.html#branches">Find Us</a>
    <a href="faqs.html">Help Center</a>
    <a href="{CO["webmail"]}">Email Login</a>
  </div>
</div></div>
<header class="site-header">
  <div class="container header-bar">
    <a class="brand" href="index.html" aria-label="N.E.A.T Microcredit – home">
      <span class="brand__mark"><img src="images/logo.png" alt="" width="52" height="70"></span>
      <span class="brand__text"><span class="brand__name">N.E.A.T</span><span class="brand__sub">Microcredit</span></span>
    </a>
    <nav id="site-nav" class="nav" aria-label="Primary">
      <ul class="nav__list">{nav}</ul>
      <div class="nav__extras">
        <a class="btn btn--primary" href="get.html">Get a Loan {ic("arrow")}</a>
        <a href="faqs.html">Help Center (FAQs)</a>
        <a href="contact.html#branches">{ic("pin")} Find a branch</a>
        <a href="tel:{CO["phone_tel"]}">{ic("phone")} {CO["phone_display"]}</a>
        <a href="{CO["webmail"]}">{ic("mail")} Email Login</a>
      </div>
    </nav>
    <button class="icon-btn" type="button" data-open-search aria-label="Search the site">{ic("search")}</button>
    <a class="btn btn--primary btn--sm header-cta" href="get.html">Get a Loan</a>
    <button class="icon-btn nav-toggle" id="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" aria-label="Open menu">{ic("menu", "i-menu")}{ic("close", "i-close")}</button>
  </div>
</header>
<div class="nav-backdrop" aria-hidden="true"></div>"""


def footer():
    prod = "".join(f'<li><a href="{f}">{t}</a></li>' for f, t, _, _ in PRODUCTS)
    social = "".join(f'<a href="{u}" target="_blank" rel="noopener noreferrer" aria-label="{n}">{ic(i)}</a>' for i, n, u in CO["social"])
    return f"""<footer class="site-footer">
  <div class="container">
    <div class="footer-top">
      <div class="footer-brand">
        <a class="brand" href="index.html" aria-label="N.E.A.T Microcredit – home"><span class="brand__mark"><img src="images/logo.png" alt="" width="52" height="70" loading="lazy"></span>
          <span class="brand__text"><span class="brand__name">N.E.A.T</span><span class="brand__sub">Microcredit</span></span></a>
        <p>Funding and technical support for entrepreneurs, helping businesses across Nigeria grow. {CO["tagline"]}</p>
        <div class="social">{social}</div>
      </div>
      <div class="footer-cols">
        <div><h3>Products</h3><ul>{prod}</ul></div>
        <div><h3>Company</h3><ul>
          <li><a href="about.html">About Us</a></li><li><a href="products.html">All Products</a></li><li><a href="get.html">Get a Loan</a></li><li><a href="investment.html">Investment Form</a></li>
          <li><a href="career.html">Career</a></li><li><a href="contact.html">Contact</a></li><li><a href="faqs.html">FAQ’s</a></li><li><a href="{CO["webmail"]}">Email Login</a></li></ul>
          <h3 style="margin-top:28px">Legal</h3><ul><li><a href="privacyPolicy.html">Privacy Policy</a></li><li><a href="termsOfService.html">Terms of Service</a></li><li><a href="disclaimer.html">Disclaimer</a></li></ul></div>
        <div><h3>Contact</h3><ul class="contact-list">
          <li>{ic("pin")}<div><address>{CO["address"]}</address><a href="{CO["maps"]}" target="_blank" rel="noopener noreferrer">Open in Maps</a></div></li>
          <li>{ic("phone")}<div><small>Hotline</small><a href="tel:{CO["phone_tel"]}">{CO["phone_display"]}</a></div></li>
          <li>{ic("chat")}<div><small>WhatsApp</small><a href="{CO["wa_link"]}" target="_blank" rel="noopener noreferrer">{CO["wa_display"]}</a></div></li>
          <li>{ic("mail")}<div><small>General inquiries</small><a href="mailto:{CO["email_general"]}">{CO["email_general"]}</a><br><a href="mailto:{CO["email_alt"]}">{CO["email_alt"]}</a></div></li>
          <li>{ic("mail")}<div><small>Careers</small><a href="mailto:{CO["email_careers"]}">{CO["email_careers"]}</a></div></li></ul></div>
      </div>
    </div>
    <div class="compliance"><span><b>{CO["legal"]}</b></span><span>NDP Act, 2023 audit — acknowledgement of statutory filing of compliance audit returns, 2025.</span></div>
    <div class="footer-bottom"><span>© 2026 N.E.A.T Microcredit. All rights reserved.</span>
      <nav aria-label="Legal"><a href="privacyPolicy.html">Privacy Policy</a><a href="termsOfService.html">Terms of Service</a><a href="disclaimer.html">Disclaimer</a></nav></div>
  </div>
</footer>
<dialog id="search-dialog" aria-label="Search the site"><div class="search-box">
  <div class="search-box__field">{ic("search")}<input id="search-input" type="search" placeholder="Search pages and products…" aria-label="Search the site" autocomplete="off">
    <button class="icon-btn" type="button" data-close-search aria-label="Close search">{ic("close")}</button></div>
  <ul id="search-results" class="search-results" aria-live="polite"></ul></div></dialog>
<script src="js/neat.js" defer></script>
</body>
</html>"""


def page(fname, title, desc, body):
    html = head(title, desc, fname) + "\n<body>\n" + SPRITE + "\n" + header(fname) + '\n<main id="main">\n' + body + "\n</main>\n" + footer()
    (OUT / fname).write_text(html, encoding="utf-8")
    print("wrote", fname, f"{len(html)//1024} KB")


# ----------------------------------------------------------------------------
# Reusable page fragments
# ----------------------------------------------------------------------------
def hero_inner(title, lead, crumb, eyebrow="N.E.A.T Microcredit"):
    return f"""<section class="page-hero"><div class="container">
  <ol class="crumbs" aria-label="Breadcrumb"><li><a href="index.html">Home</a></li>{crumb}<li aria-current="page">{title}</li></ol>
  <span class="eyebrow">{eyebrow}</span>
  <h1>{title}</h1>
  <p>{lead}</p>
</div></section>"""


PROD_CRUMB = '<li><a href="products.html">Products</a></li>'


def checklist(items, cols=False):
    lis = "".join(f"<li>{ic('check')}<span>{t}</span></li>" for t in items)
    return f'<ul class="checklist{" checklist--cols" if cols else ""}">{lis}</ul>'


def calculator(min_amt=50000, max_amt=1000000, heading="Estimate your repayments", uid="c"):
    return f"""<div class="calc" data-calc data-rate="30">
  <h2>{heading}</h2>
  <div class="calc__field">
    <div class="calc__label"><label for="{uid}-amt">Amount you need</label><output for="{uid}-amt" data-out-amount>₦50,000</output></div>
    <input class="range" id="{uid}-amt" data-amount type="range" min="{min_amt}" max="{max_amt}" step="10000" value="50000">
    <div class="calc__scale"><span>₦{min_amt:,}</span><span>₦{max_amt:,}</span></div>
  </div>
  <div class="calc__field">
    <div class="calc__label"><label for="{uid}-wk">Repayment period</label><output for="{uid}-wk" data-out-weeks>6 weeks</output></div>
    <input class="range" id="{uid}-wk" data-weeks type="range" min="1" max="24" step="1" value="6">
    <div class="calc__scale"><span>1 week</span><span>24 weeks</span></div>
  </div>
  <div class="calc__result" aria-live="polite">
    <div class="calc__row"><span>Estimated weekly repayment</span><b data-out-weekly>₦10,833</b></div>
    <div class="calc__row calc__row--total"><span>Estimated total to repay</span><b data-out-total>₦65,000</b></div>
  </div>
  <p class="calc__note">Estimate only: a flat 30% is added to the amount and the total is spread evenly across the weeks you choose. This is not an offer. Final terms are confirmed by N.E.A.T Microcredit.</p>
</div>"""


def cta_band(title="Your Next Stage of Growth Starts Here.", text="Explore our services or talk to our team about the support your business needs.",
             b1=("products.html", "Explore Our Services"), b2=("contact.html", "Contact Our Team")):
    return f"""<section class="cta"><div class="container cta__inner">
  <h2 class="reveal">{title}</h2>
  <div class="reveal" style="--d:.1s"><p>{text}</p>
    <div class="btn-row"><a class="btn btn--primary" href="{b1[0]}">{b1[1]} {ic("arrow")}</a><a class="btn btn--ghost" href="{b2[0]}">{b2[1]}</a></div>
    <small>Funding is subject to N.E.A.T Microcredit’s assessment and approval.</small></div>
</div></section>"""


def img(src, alt, w, h, cls="", lazy=True):
    return f'<img src="images/opt/{src}" alt="{alt}" width="{w}" height="{h}"{" loading=lazy decoding=async" if lazy else ""}{f" class={cls}" if cls else ""}>'


# ----------------------------------------------------------------------------
# Text pulled verbatim from the previous build
# ----------------------------------------------------------------------------
FIXES = [("Copywright", "Copyright"), ("neatmicreocredit.com.ng", "neatmicrocredit.com.ng"), ("neatmicrocrdit.com.ng", "neatmicrocredit.com.ng"),
         ("MICROREDIT", "MICROCREDIT")]


def load_orig(fname):
    s = (ORIG / fname).read_text(encoding="utf-8", errors="ignore")
    return BeautifulSoup(re.sub(r"data:[^\"')]+", "DATA", s), "lxml"), s


def clean_inline(el):
    parts = []
    for c in el.children:
        if getattr(c, "name", None) is None:
            parts.append(html_lib.escape(str(c), quote=False))
        elif c.name in ("strong", "b", "em", "i", "u"):
            parts.append(f"<{'strong' if c.name in ('b','strong') else c.name}>{clean_inline(c)}</{'strong' if c.name in ('b','strong') else c.name}>")
        elif c.name == "br":
            parts.append("<br>")
        elif c.name == "a" and c.get("href"):
            parts.append(f'<a href="{c["href"]}">{clean_inline(c)}</a>')
        else:
            parts.append(clean_inline(c))
    out = re.sub(r"[ \t\r\n]+", " ", "".join(parts)).strip()
    out = re.sub(r"(<br> ?){2,}", "<br>", out)
    for a, b in FIXES:
        out = out.replace(a, b)
    return out


def legal_html(fname, title):
    b, _ = load_orig(fname)
    h = [x for x in b.find_all("h1") if x.get_text(strip=True).lower() != title.lower()][0]
    cont = h.parent
    skip = {title.lower(), "we are moving africa forward", "n.e.a.t microcredit", "n.e.a.t microredit"}
    out = []
    for el in cont.find_all(["h1", "h2", "h3", "p", "ul", "ol"], recursive=False):
        txt = el.get_text(" ", strip=True)
        if not txt or txt.lower() in skip:
            continue
        if el.name in ("h1", "h2", "h3"):
            out.append(f"<h2>{clean_inline(el).title() if clean_inline(el).isupper() else clean_inline(el)}</h2>")
        elif el.name in ("ul", "ol"):
            out.append("<ul>" + "".join(f"<li>{clean_inline(li)}</li>" for li in el.find_all("li")) + "</ul>")
        else:
            out.append(f"<p>{clean_inline(el)}</p>")
    return "\n".join(out)


def about_story():
    b, _ = load_orig("about.html")
    cont = b.find(string=re.compile("It is born out of")).parent.parent
    ps = [clean_inline(p) for p in cont.find_all("p")]
    first, rest = ps[0], ps[1]
    sents = re.split(r"(?<=[.!?])\s+(?=[A-Z“‘])", rest)
    chunks, cur = [], []
    for s in sents:
        cur.append(s)
        if len(" ".join(cur)) > 380:
            chunks.append(" ".join(cur)); cur = []
    if cur:
        chunks.append(" ".join(cur))
    return first, chunks


# ============================================================================
# PAGES
# ============================================================================
def build_home():
    prod_tiles = f"""
<a class="tile tile--feature reveal" href="microFund.html">
  <div class="tile__bg">{img("trader-wide-1400.webp", "", 1400, 937)}</div>
  <span class="tile__icon">{ic("banknote")}</span>
  <h3>Micro Fund</h3>
  <p>A quick fund designed for urgent financing needs. Available at the branch: clients visit and are disbursed.</p>
  <span class="tile__go">Explore Micro Fund {ic("arrow")}</span>
</a>
<a class="tile tile--sme tile--tint reveal" style="--d:.08s" href="sme.html">
  <span class="tile__icon">{ic("briefcase")}</span><h3>S.M.E Fund</h3>
  <p>Grow and expand your business with a range of easily accessible SME funding.</p><span class="tile__go">Discover SME Funding {ic("arrow")}</span></a>
<a class="tile tile--asset reveal" style="--d:.16s" href="assetFund.html">
  <span class="tile__icon">{ic("box")}</span><h3>Asset Fund</h3>
  <p>Financial support for business owners who want to own the assets they need to grow.</p><span class="tile__go">Learn About Asset Funding {ic("arrow")}</span></a>
<a class="tile tile--sav tile--accent reveal" href="saving.html">
  <span class="tile__icon">{ic("landmark")}</span><h3>Savings</h3>
  <p>Accounts with unlimited access to your money, for individuals and corporate bodies.</p><span class="tile__go">View savings {ic("arrow")}</span></a>
<a class="tile tile--adv tile--blue reveal" style="--d:.08s" href="advisory.html">
  <span class="tile__icon">{ic("compass")}</span><h3>Business Advisory</h3>
  <p>Professional guidance and capacity building for customers starting and growing small businesses.</p><span class="tile__go">See advisory services {ic("arrow")}</span></a>
<a class="tile tile--eq tile--tint reveal" style="--d:.16s" href="equity.html">
  <span class="tile__icon">{ic("trend")}</span><h3>Equity Investment</h3>
  <p>Risk capital through equity investment, supporting businesses and promoting African shareholding.</p><span class="tile__go">Explore equity {ic("arrow")}</span></a>
<a class="tile tile--wide reveal" href="termDeposit.html">
  <span class="tile__icon">{ic("clock")}</span><div><h3>Term Deposit</h3><p>Fixed tenures with a rate agreed for the term you choose.</p></div><span class="tile__go">View term deposits {ic("arrow")}</span></a>"""

    body = f"""
<section class="hero">
  <div class="hero__rings" aria-hidden="true"></div>
  <div class="container hero__grid">
    <div class="hero__copy">
      <span class="eyebrow">Financial support for business growth</span>
      <h1>Empowering Businesses. <em>Building Africa’s Future.</em></h1>
      <p>N.E.A.T Microcredit provides funding and technical support to help entrepreneurs and businesses grow, from quick micro funds to SME and asset financing.</p>
      <div class="btn-row"><a class="btn btn--primary" href="products.html">Explore Our Services {ic("arrow")}</a><a class="btn btn--ghost" href="contact.html">Get in Touch</a></div>
      <p class="hero__note">Funding is subject to N.E.A.T Microcredit’s assessment and approval.</p>
    </div>
    <div class="hero__visual">
      <span class="hero__accent" aria-hidden="true"></span>
      <div class="hero__frame">
        <img src="images/opt/hero-trader-960.webp" srcset="images/opt/hero-trader-560.webp 560w, images/opt/hero-trader-960.webp 960w" sizes="(min-width: 960px) 480px, 90vw"
             alt="A market trader in a bright blue outfit sitting in front of her clothing stall" width="960" height="1200" fetchpriority="high">
      </div>
      <div class="hero__panels">
        <div class="panel panel--a"><span class="panel__icon">{ic("calendar")}</span><div><b>Since 2017</b><span>In business, supporting entrepreneurs</span></div></div>
        <div class="panel panel--b"><span class="panel__icon">{ic("pin")}</span><div><b>16 branch offices</b><span>Kaduna, Abuja area, Kwara &amp; Kano</span></div></div>
      </div>
    </div>
  </div>
</section>

<section class="trust" aria-label="Company highlights"><div class="container"><div class="trust__card reveal">
  <div class="trust__item">{ic("calendar")}<div><b>Operating since 2017</b><span>Funding and business support for entrepreneurs.</span></div></div>
  <div class="trust__item">{ic("pin")}<div><b>16 branch offices</b><span>Across Kaduna, the Abuja area, Kwara and Kano.</span></div></div>
  <div class="trust__item">{ic("book")}<div><b>Training included</b><span>Clients get the basic knowledge to keep and improve their business.</span></div></div>
  <div class="trust__item">{ic("banknote")}<div><b>Funding for every stage</b><span>Group, individual, special, SME and product financing.</span></div></div>
</div></div></section>

<section class="section" id="about">
  <div class="container split">
    <div class="photo-stack reveal">
      <div class="photo-stack__main">{img("team-yellow.webp", "N.E.A.T Microcredit staff in yellow and blue branded shirts posing together in a branch office", 1024, 768)}</div>
      <div class="photo-stack__inset">{img("growth.webp", "A hand watering young seedlings", 479, 343)}</div>
    </div>
    <div class="reveal" style="--d:.1s">
      <span class="eyebrow">Company’s story</span>
      <h2>We are building the Africa of our dreams</h2>
      <p class="lead">N.E.A.T Microcredit is poised to become the leading financial and investment institution in Africa. We offer entrepreneurs the opportunity to easily access loans and investment.</p>
      <div class="mv">
        <div class="mv__card mv__card--mission"><h3>Our Mission</h3><p>To empower entrepreneurs through funding and technical support in order to move Nigeria, and by extension Africa, into an economically strong and successful nation.</p></div>
        <div class="mv__card mv__card--vision"><h3>Our Vision</h3><p>To be the biggest, best and most respected funding and investment institution in Africa by giving exceptional financial and technical support to the next generation of African entrepreneurs.</p></div>
      </div>
      <h3 style="margin-top:32px;font-size:1rem;color:var(--muted);font-weight:600;letter-spacing:0">Our core values</h3>
      <div class="values" style="margin-top:12px">
        <div class="value">{ic("sprout")}<b>Nurturing</b></div><div class="value">{ic("award")}<b>Excellence</b></div>
        <div class="value">{ic("shield")}<b>Accountability</b></div><div class="value">{ic("eye")}<b>Transparency</b></div>
      </div>
      <p style="margin-top:30px"><a class="link-arrow" href="about.html">Read our full story {ic("arrow")}</a></p>
    </div>
  </div>
</section>

<section class="section section--tint" id="services">
  <div class="container">
    <div class="section-head reveal"><span class="eyebrow">Our products</span><h2>Financial products built around your business</h2>
      <p>From quick micro funding to savings, advisory and investment, choose the support that fits your stage of growth.</p></div>
    <div class="bento">{prod_tiles}</div>
    <div class="cats reveal"><h3>Funding categories we offer:</h3>
      <ul class="chips"><li class="chip">Group Financing</li><li class="chip">Individual Financing</li><li class="chip">Special Funding</li><li class="chip">SME Financing</li><li class="chip">Product Financing</li></ul></div>
    <p class="hero__note" style="color:var(--muted)">Eligibility, requirements and terms differ by product. See each product page for details.</p>
  </div>
</section>

<section class="section" id="why">
  <div class="container split split--reverse">
    <div class="why-visual reveal">
      <figure>{img("market-women.webp", "Women traders measuring grain at a busy market", 313, 171, lazy=True)}</figure>
      <figure>{img("seamstress.webp", "A seamstress smiling while working at a sewing machine in a workshop", 281, 213)}</figure>
      <p class="why-quote">When you grow, we grow.</p>
    </div>
    <div class="reveal" style="--d:.1s">
      <span class="eyebrow">Why choose N.E.A.T</span>
      <h2>Funding backed by knowledge and care</h2>
      <ol class="why-list">
        <li><div><h3>Built for the informal sector</h3><p>We believe getting the African economy right means focusing on the informal sector, and on hardworking people who need access to funds.</p></div></li>
        <li><div><h3>Funding with technical support</h3><p>Beyond funding, we give clients the basic knowledge required to keep and improve their businesses.</p></div></li>
        <li><div><h3>Evaluation and peer review</h3><p>We periodically evaluate clients’ progress and compare them with their peers to foster healthy competition.</p></div></li>
        <li><div><h3>Small, simple and low-cost</h3><p>We keep overheads low and operations simple so our funds improve lives without putting the burden on clients.</p></div></li>
      </ol>
    </div>
  </div>
</section>

<section class="section section--tint" id="funding">
  <div class="container">
    <div class="section-head reveal"><span class="eyebrow">Featured funding</span><h2>Funding solutions at a glance</h2>
      <p>Key details from our product pages. Terms differ by product and are confirmed by N.E.A.T Microcredit.</p></div>
    <div class="fund-layout">
      <div class="fund-rows">
        <article class="fund-row reveal"><div><h3>Micro Fund</h3><p>A quick fund for urgent financing needs, available in the branch.</p>
          <ul class="facts"><li>Business owners</li><li>₦50,000 – ₦300,000</li><li>Weekly repayment</li><li>6 months</li></ul></div>
          <a class="btn btn--outline btn--sm" href="microFund.html">Explore Micro Fund {ic("arrow")}</a></article>
        <article class="fund-row reveal" style="--d:.08s"><div><h3>S.M.E Fund</h3><p>Funding to grow and expand your business, with documentation requirements set out on the product page.</p>
          <ul class="facts"><li>Application form</li><li>Sales records</li><li>Guarantors</li></ul></div>
          <a class="btn btn--outline btn--sm" href="sme.html">Discover SME Funding {ic("arrow")}</a></article>
        <article class="fund-row reveal" style="--d:.16s"><div><h3>Asset Fund</h3><p>Support for business owners who want to own the assets they need.</p>
          <ul class="facts"><li>Business owners</li><li>Weekly repayment</li><li>6 months</li><li>30% markup</li></ul></div>
          <a class="btn btn--outline btn--sm" href="assetFund.html">Learn About Asset Funding {ic("arrow")}</a></article>
        <p class="reveal" style="margin:6px 0 0"><a class="link-arrow" href="get.html">Express your interest {ic("arrow")}</a></p>
      </div>
      <div class="reveal" style="--d:.1s">{calculator(uid="home")}</div>
    </div>
  </div>
</section>

<section class="section section--navy on-navy" id="impact">
  <div class="container">
    <div class="stats-head"><div><span class="eyebrow">Achievement milestones</span><h2 style="margin:0">Growing with the communities we serve</h2></div>
      <p style="margin:0;color:#AFC3DD">We are excited to share our milestones. Your ongoing support means so much to us as we work to empower even more communities through microfinance.</p></div>
    <div class="stats">
      <div class="stat"><div class="stat__num" data-count="5" data-prefix="₦" data-suffix="B+">₦5B+</div><div class="stat__label">Fund disbursed</div></div>
      <div class="stat"><div class="stat__num" data-count="45000" data-suffix="+">45,000+</div><div class="stat__label">Satisfied customers base</div></div>
      <div class="stat"><div class="stat__num" data-count="150" data-suffix="+">150+</div><div class="stat__label">Dedicated team members</div></div>
      <div class="stat"><div class="stat__num" data-count="16">16</div><div class="stat__label">Branch offices</div></div>
    </div>
    <p class="branches-list"><b>Locations:</b> Kaduna 1, Kaduna 2, Zaria, Gonin-Gora, Kawo, Karu, Gwagwalada, Suleja, Ilorin 1, Ilorin 2, Omu-Aran, Offa, Kano 1, Kano 2, Kano 3 and Kano 4. <a href="contact.html#branches" style="color:var(--yellow)">See addresses</a></p>
  </div>
</section>

<section class="section" id="feedback">
  <div class="container">
    <div class="section-head reveal"><span class="eyebrow">Customer feedback</span><h2>What our customers say</h2></div>
    <div class="quotes">
      <figure class="quote quote--lead reveal"><blockquote>They have wonderful workers that even if you don’t want to associate with them, you will have no choice because they’re very good.</blockquote>
        <figcaption><span aria-hidden="true">RZ</span><div>Rasheedat Zubairu<small>N.E.A.T Microcredit customer</small></div></figcaption></figure>
      <figure class="quote reveal" style="--d:.08s"><blockquote>NEAT inspired me to grow.</blockquote>
        <figcaption><span aria-hidden="true">MY</span><div>Muhammad Sani Yau<small>N.E.A.T Microcredit customer</small></div></figcaption></figure>
      <figure class="quote reveal" style="--d:.16s"><blockquote>A major come back! Thanks to NEAT Microcredit.</blockquote>
        <figcaption><span aria-hidden="true">PE</span><div>Patricia Kingsley Edeh<small>N.E.A.T Microcredit customer</small></div></figcaption></figure>
    </div>
  </div>
</section>

<section class="partners" aria-labelledby="partners-h"><div class="container">
  <h2 id="partners-h">Our partners</h2>
  <ul class="partners__row">
    <li><img src="images/zenith.png" alt="Zenith Bank" loading="lazy" width="92" height="93"></li><li><img src="images/providus.png" alt="Providus Bank" loading="lazy" width="117" height="96"></li>
    <li><img src="images/cascador.png" alt="Cascador" loading="lazy" width="131" height="98"></li><li><img src="images/gt.png" alt="GTBank" loading="lazy" width="85" height="69"></li>
    <li><img src="images/clique.png" alt="Clique Nigeria" loading="lazy" width="106" height="82"></li><li><img src="images/access.png" alt="Access Bank" loading="lazy" width="118" height="82"></li>
    <li><img src="images/sunTrust.png" alt="SunTrust Bank" loading="lazy" width="104" height="93"></li><li><img src="images/union.png" alt="Union Bank" loading="lazy" width="104" height="96"></li>
    <li><img src="images/sterling.png" alt="Sterling Bank" loading="lazy" width="106" height="92"></li><li><img src="images/marble.png" alt="Marble Capital" loading="lazy" width="104" height="90"></li>
    <li><img src="images/coat.png" alt="Central Bank of Nigeria emblem" loading="lazy" width="111" height="79"></li><li><img src="images/taj.png" alt="TAJ Bank" loading="lazy" width="87" height="78"></li>
  </ul></div></section>
{cta_band()}"""
    page("index.html", "N.E.A.T Microcredit | Funding and Business Support in Nigeria",
         "N.E.A.T Microcredit provides funding and technical support to help entrepreneurs and businesses grow: Micro Fund, SME Fund, Asset Fund, savings, advisory and investment.", body)


def build_products():
    def card(f, t, d, icn, image, alt):
        return f"""<a class="product-card reveal" href="{f}">{img(image, alt, 560, 350)}<div class="product-card__body"><h3>{t}</h3><p>{d}</p><span class="tile__go">View {t} {ic("arrow")}</span></div></a>"""
    funding = "".join([
        card("microFund.html", "Micro Fund", "A quick fund designed for urgent financing needs. Immediately available in the branch: our clients and customers just go there and are disbursed.", "banknote", "market-stall.webp", "A busy market stall with traders and goods"),
        card("sme.html", "S.M.E Fund", "Grow and expand your business with us. A range of easily accessible SME funding.", "briefcase", "team-table.webp", "N.E.A.T staff and clients gathered around a table in a branch"),
        card("assetFund.html", "Asset Fund", "Purchase productive assets for your business through our flexible Asset Fund packages.", "box", "seamstress.webp", "A seamstress working at a sewing machine"),
    ])
    other = "".join([
        card("saving.html", "Savings", "Accounts that give you unlimited access to your money, available to individuals and corporate bodies.", "landmark", "coins-plant.webp", "A plant growing from a jar of coins"),
        card("advisory.html", "Business Advisory", "Professional advisory services and capacity building to help customers start and grow their businesses.", "compass", "advisory.webp", "Three colleagues reviewing a project on a laptop"),
        card("equity.html", "Equity Investment", "Risk capital through equity investment, delivered with deep local and Africa-wide insight.", "trend", "planning.webp", "A professional planning at a desk next to an hourglass"),
        card("termDeposit.html", "Term Deposit", "Plan ahead with fixed tenures of six months or one year and a rate agreed for your chosen term.", "clock", "laptop.webp", "A person using a smartphone beside a laptop"),
    ])
    body = hero_inner("N.E.A.T Products", "Funding, savings, advisory and investment services designed to help entrepreneurs and businesses grow.", "", "We are moving Africa forward") + f"""
<section class="section"><div class="container">
  <div class="section-head"><span class="eyebrow">Funding</span><h2>Funds for every stage of your business</h2></div>
  <div class="product-list">{funding}</div>
</div></section>
<section class="section section--tint"><div class="container">
  <div class="section-head"><span class="eyebrow">Savings, advisory &amp; investment</span><h2>More ways to build</h2></div>
  <div class="product-list">{other}</div>
  <p class="callout" style="margin-top:32px">Eligibility, requirements and terms differ by product. Expressing interest does not guarantee funding; approval is subject to N.E.A.T Microcredit’s assessment.</p>
</div></section>""" + cta_band("Ready to take the next step?", "Tell us which product interests you and a member of our team will follow up.", ("get.html", "Express Your Interest"), ("contact.html", "Contact Our Team"))
    page("products.html", "Products", "Explore N.E.A.T Microcredit products: Micro Fund, SME Fund, Asset Fund, savings, business advisory, equity investment and term deposits.", body)


def product_page(fname, title, lead, desc, req_title, req_html, intro_html, image, alt, calc=None, extra_aside="", cta=("get.html", "Apply Now")):
    aside = (calc or "") + extra_aside
    body = hero_inner(title, lead, PROD_CRUMB, "We are moving Africa forward") + f"""
<section class="section"><div class="container product-layout">
  <div class="stack">
    <div class="reveal">{intro_html}</div>
    <figure class="fig reveal">{img(image, alt, 960, 600)}</figure>
    <div class="reveal"><h2 style="font-size:clamp(1.4rem,1.1rem+1.4vw,2rem)">{req_title}</h2>{req_html}</div>
    <div class="btn-row reveal"><a class="btn btn--primary" href="{cta[0]}">{cta[1]} {ic("arrow")}</a><a class="btn btn--outline" href="contact.html">Talk to our team</a></div>
    <p class="callout reveal">Expressing interest does not guarantee funding. Eligibility and terms are confirmed by N.E.A.T Microcredit.</p>
  </div>
  <aside class="stack">{aside}</aside>
</div></section>
<section class="section section--tint"><div class="container"><div class="section-head" style="margin:0"><h2 style="font-size:clamp(1.4rem,1.1rem+1.4vw,2rem)">Explore more N.E.A.T products</h2></div>
  <ul class="chips" style="margin-top:20px">{"".join(f'<li><a class="chip" href="{f}" style="text-decoration:none">{t}</a></li>' for f, t, _, _ in PRODUCTS if f != fname)}</ul></div></section>"""
    page(fname, title, desc, body)


def build_product_pages():
    product_page("microFund.html", "Micro Fund", "A quick fund designed for urgent financing needs.",
                 "Micro Fund from N.E.A.T Microcredit is a quick fund for urgent financing needs, available in the branch to business owners.",
                 "Eligibility and requirements", checklist(["Must be a business owner", "Fund from ₦50,000 to ₦300,000", "Weekly repayment", "Duration: 6 months"], cols=True),
                 "<p class='lead'>Micro Fund is a quick fund designed for urgent financing needs. It is immediately available in the branch: our clients and customers just have to go there and be disbursed.</p>",
                 "market-stall.webp", "A busy market stall with traders and goods", calc=calculator(50000, 300000, "Estimate your repayments", "mf"))
    sme = ["Fully completed application form (signed)", "Account statement from 6 or 12 months’ sales record, purchase invoice, etc.",
           "Corporate Affairs Commission (C.A.C) certificate (applicable to corporate customers)", "Credit search reports of both guarantor and customer", "Detailed cash flow",
           "Tax Identification Number (T.I.N) certificate (applicable to corporate customers)",
           "Qualified and satisfied guarantor with stable income (works with a reputable organisation or owns a registered business)",
           "Duly completed guarantors’ form, 6-month statement and ID card of two guarantors", "100% stock collateral", "5% processing fee",
           "Updated and valid utility bill for the customer’s office/shop and house", "Rent receipt for the customer’s business place",
           "Six cheque leaflets from the client or guarantors, duly signed", "In the absence of a cheque, the guarantor can pledge stock"]
    product_page("sme.html", "S.M.E Fund", "Grow and expand your business with a range of easily accessible SME funding.",
                 "S.M.E Fund from N.E.A.T Microcredit helps small and medium businesses grow. See the full list of requirements and estimate repayments.",
                 "Requirements", checklist(sme, cols=True),
                 "<p class='lead'>Grow and expand your business with us. A range of easily accessible SME funding.</p>",
                 "team-table.webp", "N.E.A.T staff and clients gathered around a table in a branch", calc=calculator(50000, 1000000, "Estimate your repayments", "sme"))
    product_page("assetFund.html", "Asset Fund", "Financial support for business owners who want to own the assets their business needs.",
                 "Asset Fund from N.E.A.T Microcredit supports business owners who want to own the assets they need. Weekly repayment over six months.",
                 "Eligibility and requirements", checklist(["Must be a business owner", "Weekly repayment", "Duration: 6 months", "Markup on loan: 30%"], cols=True),
                 "<p class='lead'>N.E.A.T Asset Fund is designed to offer financial support to individuals, i.e. business owners, who want to own any asset of their dream. Purchase productive assets for your business through our flexible Asset Fund packages.</p>",
                 "seamstress.webp", "A seamstress working at a sewing machine", calc=calculator(50000, 1000000, "Estimate your repayments", "af"))

    # Savings
    sav_acc = """<div class="disclose">
<details open><summary>Savings Account</summary><div class="disclose__body"><p>Save for an emergency or for a specific project.</p><p><strong>Duration:</strong> 3 months, 6 months, 9 months or 12 months.</p></div></details>
<details><summary>Current Account</summary><div class="disclose__body"><p>Unlimited deposits and withdrawals with easy access to your money anytime.</p></div></details>
<details><summary>Fixed Deposit Account</summary><div class="disclose__body"><p>Earn higher returns by locking your funds for an agreed investment period.</p></div></details></div>"""
    product_page("saving.html", "N.E.A.T Savings", "A savings account with unlimited access to your money, for individuals and corporate bodies.",
                 "N.E.A.T Savings accounts give you unlimited access to your money. Open a savings, current or fixed deposit account.",
                 "Eligibility and requirements", checklist(["No interest payable, no deposit or management fees", "Must be above the age of 18 years"], cols=True) + "<h2 style='font-size:clamp(1.4rem,1.1rem+1.4vw,2rem);margin-top:36px'>N.E.A.T savings products</h2><p>With N.E.A.T you can save money for an emergency or for a specific project.</p>" + sav_acc,
                 "<p class='lead'>N.E.A.T Microcredit savings account provides you with unlimited access to your money at all times. You can manage your business, execute your payments and receive your salary through this account. It is available to both individuals and corporate bodies.</p>",
                 "coins-plant.webp", "A plant growing from a jar of coins", cta=("contact.html", "Open an Account"))
    product_page("advisory.html", "Business Advisory", "Professional guidance to help customers start, manage and grow small businesses.",
                 "N.E.A.T Business Consulting and Capacity Building: professional advisory services in financial management, HR management and training.",
                 "Areas of support", checklist(["Financial Management", "Human Resource Management", "Capacity Building"], cols=True) + """<div class="card card--tint" style="margin-top:28px"><h3>N.E.A.T Capacity Building</h3><p style="margin:0">This service is rendered to customers who require additional skills on how to properly manage their business. It involves the training of customers in areas of financial management, proper records keeping and funds management.</p></div>""",
                 "<h2 style='font-size:clamp(1.4rem,1.1rem+1.4vw,2rem)'>N.E.A.T Business Consulting</h2><p class='lead'>To customers who are intending to start up small-scale businesses, we offer professional advisory services to enable such customers to be aware of the inherent dangers, challenges and pitfalls they may encounter and how best to overcome such obstacles. Our team of seasoned staff will be on the ground to guide such customers to help them grow their businesses.</p>",
                 "advisory.webp", "Three colleagues reviewing a project on a laptop", cta=("contact.html", "Request Advisory Support"))
    product_page("equity.html", "Equity Investment", "Risk capital through equity investment, delivered with local and Africa-wide insight.",
                 "N.E.A.T Equity Investment provides risk capital through equity investment to drive business growth in Nigeria and Africa.",
                 "Investment areas", checklist(["Common Shares", "Equity Mutual Funds", "Preferred Shares", "Retained Earnings", "Private Equity Investments", "Financial Management"], cols=True)
                 + "<h2 style='font-size:clamp(1.4rem,1.1rem+1.4vw,2rem);margin-top:36px'>Our objectives</h2>" + checklist(["Promote the efficient use of resources", "Promote African shareholding in commercial enterprise", "Play a catalytic role in attracting other investors and lenders to financially viable projects, entities and organizations", "Promote new activities and investment ideas"]),
                 "<p class='lead'>N.E.A.T Microcredit’s ability to provide risk capital through equity investment is a key element of its resource mobilization role. Our equity investment specialists leverage deep insights from our local, global and Africa presence to deliver innovative solutions that drive your business growth and that of Nigeria.</p>",
                 "planning.webp", "A professional planning at a desk next to an hourglass",
                 extra_aside="""<div class="card card--navy"><h3>Request consultation</h3><p>Assess your business potential and find opportunities for bigger success.</p><a class="btn btn--primary" href="contact.html">Let’s Talk</a></div><div class="card card--tint"><h3>Ready to invest?</h3><p>Tell us how much you would like to invest.</p><a class="link-arrow" href="investment.html">Open the investment form</a></div>""",
                 cta=("contact.html", "Request Consultation"))
    product_page("termDeposit.html", "N.E.A.T Term Deposit", "Protect your returns and plan ahead.",
                 "N.E.A.T Term Deposits let you fix a rate on your savings for a term you choose: six months or one year.",
                 "Requirements", checklist(["High Net worth Individuals (HNIs)", "Individuals and corporate organizations can apply", "Filled Term Deposit Form", "One passport photograph", "Customer investment advice"], cols=True),
                 "<p class='lead'>N.E.A.T Microcredit can help you plan for the future with our range of Term Deposits. By fixing a high ROI on your savings, N.E.A.T Term Deposits can guarantee the rate on your savings for a term within a timeframe chosen by you.</p><p>N.E.A.T Term Deposit is made for the investor who requires more value for his money. It offers higher returns than the conventional term deposit and has fixed tenures of either 6 months or one year.</p>",
                 "laptop.webp", "A person using a smartphone beside a laptop",
                 extra_aside="""<div class="card card--tint"><h3>Questions about term deposits?</h3><p>Read our answers on minimum amounts and how interest is paid.</p><a class="link-arrow" href="faqs.html">Read the FAQs</a></div><div class="card card--navy"><h3>Ready to invest?</h3><p>Send us your details and amount.</p><a class="btn btn--primary" href="investment.html">Investment form</a></div>""",
                 cta=("investment.html", "Open the Investment Form"))


def build_about():
    first, chunks = about_story()
    story = "".join(f"<p>{c}</p>" for c in chunks)
    body = hero_inner("We Are Moving Africa Forward", "Who we are, why we exist and the people behind N.E.A.T Microcredit.", "", "About N.E.A.T Microcredit").replace("<li aria-current=\"page\">We Are Moving Africa Forward</li>", "<li aria-current=\"page\">About Us</li>") + f"""
<section class="section"><div class="container split split--wide-left" style="align-items:start">
  <div class="reveal"><span class="eyebrow">Our story</span><h2>Born from lived experience</h2><p class="lead">{first}</p>
    <div class="photo-stack" style="margin-top:28px"><div class="photo-stack__main">{img("team-yellow.webp", "N.E.A.T Microcredit staff in yellow and blue branded shirts", 1024, 768)}</div></div></div>
  <div class="prose reveal" style="--d:.1s">{story}<p><strong>— N.E.A.T Philosophy</strong></p></div>
</div></section>

<section class="section section--tint"><div class="container">
  <div class="mv" style="margin:0 0 48px">
    <div class="mv__card mv__card--mission"><h3>Our Mission</h3><p>To empower entrepreneurs through funding and technical support in order to move Nigeria, and by extension Africa, into an economically strong and successful nation.</p></div>
    <div class="mv__card mv__card--vision" style="background:var(--white)"><h3>Our Vision</h3><p>To be the biggest, best and most respected funding and investment institution in Africa by giving exceptional financial and technical support to the next generation of African entrepreneurs.</p></div>
  </div>
  <div class="section-head"><span class="eyebrow">Core values</span><h2>What guides us</h2></div>
  <div class="values values--big">
    <div class="value">{ic("sprout")}<div><b>Nurturing</b><small>Supporting entrepreneurs with the funding and knowledge to grow.</small></div></div>
    <div class="value">{ic("award")}<div><b>Excellence</b><small>Giving exceptional financial and technical support.</small></div></div>
    <div class="value">{ic("shield")}<div><b>Accountability</b><small>Owning our commitments to clients, funders and communities.</small></div></div>
    <div class="value">{ic("eye")}<div><b>Transparency</b><small>Being open about how we work and what our services involve.</small></div></div>
  </div>
</div></section>

<section class="section"><div class="container container--narrow">
  <div class="section-head"><span class="eyebrow">N.E.A.T Philosophy</span><h2>How we think about growth</h2></div>
  <div class="disclose">
    <details open><summary>01. Profitability</summary><div class="disclose__body"><p>We understand that the solution to the African problem cannot be found in charity and donations. We must build companies that can solve Africa’s problems at a profit. N.E.A.T Microcredit has been in business since 2017, and we have been profitable since then. This has been achieved by watching our cost closely and keeping our overhead very low without jeopardizing quality customer experience and staff welfare. Based on the experience of our investors over the years, we have given nothing less than 30% per annum on the funds invested with us. That makes it certain that our investors will make back their investment through profit sharing within 3 years. Our members/investors can receive returns on their investment on a monthly, quarterly, biannually or annual basis.</p></div></details>
    <details><summary>02. Growth Plan</summary><div class="disclose__body"><p>N.E.A.T Microcredit is poised to become the leading financial and investment institution in Africa. Our goal is to support the industrialization of our continent. We are starting at a microcredit level because we understand that we must pull more of our population out of extreme poverty and create strong middle-class families, as that will be required to support our industrialization plan. Therefore, 50% of all our profit are reinvested into the business to ensure accelerated growth and make funds available for more investment.</p></div></details>
  </div>
</div></section>

<section class="section section--tint"><div class="container">
  <div class="section-head"><span class="eyebrow">Leadership</span><h2>Board of Directors</h2>
    <p>The Board of Directors at N.E.A.T Microcredit is a diverse group of esteemed professionals dedicated to fostering sustainable economic development through innovative microfinance solutions. With their collective expertise, they ensure that the organization remains aligned with its mission to empower underserved communities.</p></div>
  <div class="board">
    <article class="person reveal">{img("chairman.webp", "Portrait of Dave Delucia, Board Chairman", 375, 374)}<div class="person__body"><h3>Dave Delucia</h3><span class="role">Board Chairman</span></div></article>
    <article class="person reveal" style="--d:.08s">{img("member1.webp", "Portrait of Dr. Oluseun Falope, Board Member", 381, 381)}<div class="person__body"><h3>Dr. Oluseun Falope</h3><span class="role">Board Member</span></div></article>
    <article class="person reveal" style="--d:.16s">{img("member2.webp", "Portrait of Haj. Hadiza Musa, Board Member", 375, 382)}<div class="person__body"><h3>Haj. Hadiza Musa</h3><span class="role">Board Member</span></div></article>
  </div>
</div></section>

<section class="section"><div class="container">
  <div class="section-head"><span class="eyebrow">Management</span><h2>Our team</h2>
    <p>At N.E.A.T Microcredit, our management team is dedicated to driving our mission forward with expertise and passion. We work collaboratively to empower communities and enhance financial accessibility across Africa.</p></div>
  <div class="people">
    <article class="person reveal">{img("ceo.webp", "Portrait of Omoniyi Rafiu Salami, Chief Executive Officer", 381, 381)}<div class="person__body"><h3>Omoniyi Rafiu Salami</h3><span class="role">Chief Executive Officer</span><p>He is dedicated to empowering underserved communities through microfinance. With extensive experience in finance and a strong commitment to financial inclusion, he has significantly enhanced the organization’s reach and impact. His leadership fosters economic growth and drives partnerships for sustainable development.</p></div></article>
    <article class="person reveal" style="--d:.08s">{img("coo.webp", "Portrait of Olubunmi Maryam Salami, Chief Operating Officer", 377, 380)}<div class="person__body"><h3>Olubunmi Maryam Salami</h3><span class="role">Chief Operating Officer</span><p>Her crucial role is overseeing daily operations and ensuring the efficient delivery of microfinance services. With a strong background in operations management and finance, Olubunmi works closely with the team to create impactful financial solutions for underserved populations.</p></div></article>
    <article class="person reveal" style="--d:.16s">{img("gbenga.webp", "Portrait of Ayodeji Gbenga, Head of IT", 349, 348)}<div class="person__body"><h3>Ayodeji Gbenga</h3><span class="role">Head of IT</span><p>He spearheads the development and implementation of technological solutions to enhance financial services. His innovative approach focuses on improving user experience and streamlining transactions, ensuring that clients have seamless access to microfinance services.</p></div></article>
  </div>
</div></section>
{cta_band("Join us on the journey.", "Explore our products or get in touch to see how N.E.A.T Microcredit can support your business.")}"""
    page("about.html", "About Us", "The story, mission, vision, values, board and management team behind N.E.A.T Microcredit, in business since 2017.", body)


def form_field(label, name, typ="text", req=False, ph="", autoc="", extra=""):
    r = ' <span class="req" aria-hidden="true">*</span>' if req else ""
    return f'<div class="field"><label for="f-{name}">{label}{r}</label><input id="f-{name}" name="{name}" data-label="{label}" type="{typ}"{" required" if req else ""}{f" placeholder=\"{ph}\"" if ph else ""}{f" autocomplete=\"{autoc}\"" if autoc else ""}{extra}></div>'


def build_contact():
    cards = f"""<div class="contact-cards">
  <div class="contact-card">{ic("pin")}<div><h3>Head office</h3><address>N.E.A.T Microcredit<br>NF5 Oyo Road, Central Business District,<br>Kaduna, Kaduna State, Nigeria.</address></div></div>
  <div class="contact-card">{ic("phone")}<div><h3>Phone</h3><p><a href="tel:{CO["phone_tel"]}">{CO["phone_display"]}</a></p></div></div>
  <div class="contact-card">{ic("chat")}<div><h3>WhatsApp</h3><p><a href="{CO["wa_link"]}" target="_blank" rel="noopener noreferrer">{CO["wa_display"]}</a></p></div></div>
  <div class="contact-card">{ic("mail")}<div><h3>Email</h3><p><a href="mailto:{CO["email_general"]}">{CO["email_general"]}</a><br><a href="mailto:{CO["email_alt"]}">{CO["email_alt"]}</a></p></div></div>
  <div class="contact-card">{ic("users")}<div><h3>Career</h3><p>Would you like to join our growing team?<br><a href="mailto:{CO["email_careers"]}">{CO["email_careers"]}</a></p></div></div>
</div>"""
    form = f"""<div class="form-card"><h2 style="font-size:clamp(1.4rem,1.1rem+1.4vw,2rem)">Send us a message</h2>
<form class="form" data-mailto data-to="{CO["email_general"]}" data-subject="Website enquiry – N.E.A.T Microcredit">
  <div class="form__row form__row--2">{form_field("Full name", "name", req=True, autoc="name")}{form_field("Your email address", "email", "email", True, autoc="email")}</div>
  <div class="form__row form__row--2">{form_field("Subject", "subject", req=True)}{form_field("Phone number", "phone", "tel", autoc="tel")}</div>
  <div class="field"><label for="f-product">Product of interest</label><select id="f-product" name="product" data-label="Product of interest"><option value="">Select a product</option>{"".join(f"<option>{t}</option>" for _, t, _, _ in PRODUCTS)}</select></div>
  <div class="field"><label for="f-message">Your message <span class="req" aria-hidden="true">*</span></label><textarea id="f-message" name="message" data-label="Message" required></textarea></div>
  <div class="check"><input id="f-agree" type="checkbox" name="agree" data-label="Accepted privacy policy" required><label for="f-agree">I am bound by the terms of the Service. I accept the <a href="privacyPolicy.html">Privacy Policy</a>.</label></div>
  <div class="form-status" role="status" hidden></div>
  <button class="btn btn--primary" type="submit">Send message {ic("arrow")}</button>
</form></div>"""
    regions = {}
    for lab, reg, addr, ph in BRANCHES:
        regions.setdefault(reg, []).append((lab, addr, ph))
    br = "".join(f'<article class="branch reveal"><span class="region">{reg}</span><h3>{lab}</h3><p>{addr}</p><a href="tel:{tel(ph)}">{ic("phone")}{ph}</a></article>'
                 for reg, items in regions.items() for lab, addr, ph in items)
    body = hero_inner("Have a question in mind? Let’s talk.", "How may we help you today? Reach our head office, visit a branch or send us a message.", "", "Get to know us").replace("<li aria-current=\"page\">Have a question in mind? Let’s talk.</li>", "<li aria-current=\"page\">Contact Us</li>") + f"""
<section class="section"><div class="container contact-grid"><div class="stack">{cards}</div><div>{form}</div></div></section>
<section class="section section--tint" id="branches"><div class="container">
  <div class="section-head"><span class="eyebrow">Branch offices</span><h2>Visit us in person</h2><p>Sixteen offices across Kaduna, the Abuja area, Kwara and Kano.</p></div>
  <div class="branches">{br}</div></div></section>
<section class="section"><div class="container"><div class="section-head"><span class="eyebrow">Head office</span><h2>Find us on the map</h2></div>
  <div class="map-embed"><iframe title="Map showing the N.E.A.T Microcredit head office, NF5 Oyo Road, Central Business District, Kaduna" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="https://maps.google.com/maps?q=NF5, Oyo Road, Central Business District, Kaduna&amp;t=&amp;z=13&amp;ie=UTF8&amp;iwloc=&amp;output=embed"></iframe></div>
  <p style="margin-top:16px"><a class="link-arrow" href="{CO["maps"]}" target="_blank" rel="noopener noreferrer">Open in Maps {ic("arrow")}</a></p></div></section>"""
    page("contact.html", "Contact Us", "Contact N.E.A.T Microcredit: head office in Kaduna, 16 branch offices across Kaduna, Abuja, Kwara and Kano, phone, WhatsApp, email and a message form.", body)


def build_career():
    form = f"""<div class="form-card"><form class="form" data-mailto data-to="{CO["email_careers"]}" data-subject="Job application – N.E.A.T Microcredit" data-note="Please attach your CV to that email.">
  <div class="form__row form__row--2">{form_field("First name", "first_name", req=True, autoc="given-name")}{form_field("Last name", "last_name", req=True, autoc="family-name")}</div>
  <div class="form__row form__row--2">{form_field("Phone", "phone", "tel", True, "0802 123 4567", "tel")}{form_field("Email", "email", "email", True, autoc="email")}</div>
  <div class="form__row form__row--2">{form_field("Location", "location", req=True)}{form_field("Position applying for", "position", req=True)}</div>
  <div class="field"><label for="cv-file">Upload CV</label><input id="cv-file" name="cv" type="file" accept=".pdf,.doc,.docx"><span class="hint">Accepted formats: PDF, DOC, DOCX. <span id="cv-name"></span></span></div>
  <div class="field"><label for="f-comments">Comments</label><textarea id="f-comments" name="comments" data-label="Comments"></textarea></div>
  <div class="form-status" role="status" hidden></div>
  <button class="btn btn--primary" type="submit">Submit application {ic("arrow")}</button>
</form></div>"""
    body = hero_inner("Career", "Explore opportunities to take your career to the next level at N.E.A.T Microcredit.", "", "We are moving Africa forward") + f"""
<section class="section"><div class="container split split--wide-left" style="align-items:start">
  <div class="reveal"><span class="eyebrow">Equal opportunities</span><h2>Build your career with us</h2>
    <p class="lead">N.E.A.T Microcredit is fully committed to the principles of equal opportunities in recruitment and employment and does not discriminate on the basis of any legally protected status or characteristic.</p>
    <p>If you’re ambitious, innovative and hardworking, a career with N.E.A.T Microcredit may be for you. New challenges are arising regularly as the microcredit terrain continues to develop in Nigeria. And new ideas, techniques, and solutions are needed. As the pursuit of value takes on greater significance in the financial sector, we have a multitude of career opportunities that will enable you to prove your abilities from the very first day of work.</p>
    <p><a class="link-arrow" href="mailto:{CO["email_careers"]}">{ic("mail")} {CO["email_careers"]}</a></p></div>
  <div class="photo-stack reveal" style="--d:.1s"><div class="photo-stack__main">{img("team-gathering.webp", "The N.E.A.T Microcredit team gathered together at an event", 484, 362)}</div></div>
</div></section>
<section class="section section--tint" id="apply"><div class="container container--narrow">
  <div class="section-head"><span class="eyebrow">Current vacancies</span><h2>Apply today</h2>
    <p>The organization is seeking to fill some positions. Kindly fill the form below. You will be contacted as soon as possible if you meet the requirements.</p></div>
  {form}</div></section>"""
    page("career.html", "Career", "Careers at N.E.A.T Microcredit: equal-opportunity employer. Apply for current vacancies using our application form.", body)


def build_faqs():
    qa = [("1. What are the requirements for account opening?", "<p>A valid ID-card, and a minimum balance of ₦1,000.</p>"),
          ("2. What kind of ID-card do you regard as valid?", "<p>National ID card, International Passport, Driver’s license, Permanent voter’s card etc. that has not yet expired.</p>"),
          ("3. How can I deposit without coming to your office premises?", "<p>Deposits can be made through various platforms available:</p><ul style='padding-left:1.2em;margin:0'><li>Correspondent bank from our partner banks</li><li>Internet banking transfer from all commercial banks in Nigeria</li><li>Electronic transfer</li></ul>"),
          ("4. What are the interest rates on term deposit?", "<p>The interest rate depends on the amount and maturity period. It is negotiable.</p>"),
          ("5. What is the minimum I can fix?", "<p>The minimum amount is ₦500,000.</p>"),
          ("6. How can I get my interests?", "<p>Interest can be paid into your account monthly or upon maturity.</p>")]
    items = "".join(f"<details{' open' if i == 0 else ''}><summary>{q}</summary><div class='disclose__body'>{a}</div></details>" for i, (q, a) in enumerate(qa))
    body = hero_inner("Frequently Asked Questions", "Quick answers about accounts, deposits and term deposits.", "", "Help center") + f"""
<section class="section"><div class="container container--narrow"><div class="disclose">{items}</div>
  <div class="card card--tint" style="margin-top:40px"><h3>Still have a question?</h3><p>Our team is happy to help. Call {CO["phone_display"]} or send us a message.</p><a class="btn btn--dark" href="contact.html">Contact Us {ic("arrow")}</a></div></div></section>"""
    page("faqs.html", "Frequently Asked Questions", "Answers to common questions about N.E.A.T Microcredit accounts, deposits and term deposits.", body)


def build_get():
    opts = "".join(f"<option>{b[0]}</option>" for b in BRANCHES)
    body = hero_inner("Expression of Interest", "Tell us who you are and which branch is nearest to you. A member of our team will follow up.", "", "Get a loan") + f"""
<section class="section"><div class="container product-layout"><div class="form-card"><form class="form" data-mailto data-to="{CO["email_general"]}" data-subject="Expression of interest – N.E.A.T Microcredit">
  {form_field("First name", "first_name", req=True, autoc="given-name")}{form_field("Middle name (optional)", "middle_name", autoc="additional-name")}{form_field("Last name", "last_name", req=True, autoc="family-name")}
  {form_field("Phone number", "phone", "tel", True, autoc="tel")}{form_field("Email address (optional)", "email", "email", autoc="email")}
  <div class="field"><label for="f-branch">Select a branch <span class="req" aria-hidden="true">*</span></label><select id="f-branch" name="branch" data-label="Branch" required><option value="">Select a branch</option>{opts}</select></div>
  <div class="form-status" role="status" hidden></div>
  <button class="btn btn--primary" type="submit">Submit interest {ic("arrow")}</button></form></div>
  <aside class="stack"><div class="card card--navy"><h3>What happens next?</h3><ol class="next-steps"><li>Send your details using the form.</li><li>Your nearest branch reviews your interest.</li><li>You are contacted about requirements and terms.</li></ol></div>
  <p class="callout">Expressing interest does not guarantee funding. Approval is subject to N.E.A.T Microcredit’s assessment.</p></aside></div></section>"""
    page("get.html", "Expression of Interest", "Express your interest in N.E.A.T Microcredit funding. Choose your nearest branch and we will follow up.", body)


def build_investment():
    states = "".join(f"<option>{s}</option>" for s in ["Abuja(FCT)", "Lagos", "Kaduna", "Kano", "Rivers", "Oyo"])
    body = hero_inner("Investment Form", "Tell us how much you would like to invest and how to reach you.", "", "Invest with N.E.A.T") + f"""
<section class="section"><div class="container container--narrow"><div class="form-card"><form class="form" data-mailto data-to="{CO["email_general"]}" data-subject="Investment enquiry – N.E.A.T Microcredit">
  <div class="form__row form__row--2">{form_field("First name", "first_name", req=True, autoc="given-name")}{form_field("Last name", "last_name", req=True, autoc="family-name")}</div>
  <div class="form__row form__row--2"><div class="field"><label for="f-state">Your location / state <span class="req" aria-hidden="true">*</span></label><select id="f-state" name="state" data-label="Location / State" required>{states}</select></div>{form_field("Phone", "phone", "tel", True, "0802 123 4567", "tel")}</div>
  {form_field("Email", "email", "email", True, autoc="email")}
  <fieldset class="field"><legend>Do you have an account with N.E.A.T?</legend><div class="choice-row">
    <div class="check"><input id="acc-yes" type="radio" name="has_account" value="Yes" data-label="Has N.E.A.T account"><label for="acc-yes">Yes</label></div>
    <div class="check"><input id="acc-no" type="radio" name="has_account" value="No" data-label="Has N.E.A.T account"><label for="acc-no">No</label></div></div></fieldset>
  {form_field("If yes, your N.E.A.T account number", "account_number")}
  <div class="field"><label for="f-amount">Amount you are willing to invest (₦) <span class="req" aria-hidden="true">*</span></label><input id="f-amount" name="amount" data-label="Amount to invest (NGN)" type="number" inputmode="numeric" min="500000" step="1000" required placeholder="Minimum ₦500,000"><span class="hint">Minimum ₦500,000.</span></div>
  <div class="field"><label for="f-remark">Comments / remark</label><textarea id="f-remark" name="remark" data-label="Comments"></textarea></div>
  <div class="check"><input id="f-18" type="checkbox" name="over18" value="Yes" data-label="Declares to be over 18" required><label for="f-18">I declare that I am more than 18 years old <span class="req" aria-hidden="true">*</span></label></div>
  <div class="check"><input id="f-news" type="checkbox" name="newsletter" value="Yes" data-label="Newsletter"><label for="f-news">I would like to sign up to the N.E.A.T newsletter and be informed on the latest news</label></div>
  <div class="form-status" role="status" hidden></div>
  <button class="btn btn--primary" type="submit">Submit application {ic("arrow")}</button></form></div></div></section>"""
    page("investment.html", "Investment Form", "Tell N.E.A.T Microcredit how much you would like to invest. Minimum investment ₦500,000.", body)


def build_legal():
    specs = [("privacyPolicy.html", "Privacy Policy", "How N.E.A.T Microcredit collects, uses and protects your personal data."),
             ("termsOfService.html", "Terms Of Service", "The terms that apply to your use of N.E.A.T Microcredit services and website."),
             ("disclaimer.html", "Disclaimer", "Website disclaimer, use of content, copyright and data protection information for N.E.A.T Microcredit.")]
    for f, t, d in specs:
        content = legal_html(f, t)
        title = t.replace("Of", "of")
        body = hero_inner(title, d, "", "Legal") + f'<section class="section"><div class="container"><article class="legal">{content}</article></div></section>'
        page(f, title, d, body)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    build_home(); build_products(); build_product_pages(); build_about(); build_contact(); build_career()
    build_faqs(); build_get(); build_investment(); build_legal()
