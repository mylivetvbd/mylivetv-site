# -*- coding: utf-8 -*-
"""My Live TV সাইট-রোবট v2
কাজ: (১) দৈনিক খেলার সূচি পেজ (২) ২ দিন পরপর ভাণ্ডার (draft) থেকে ১টা লেখা প্রকাশ
(৩) blog তালিকা (৪) sitemap/robots (৫) প্রকাশের আগে স্ব-পরীক্ষা"""
import json, os, re, glob, shutil, urllib.request, datetime

EV_URL = "https://api.github.com/repos/mylivetvbd/mylivetv/contents/events.json?ref=main"
PUB_GAP_DAYS = 2   # কত দিন পরপর নতুন লেখা প্রকাশ হবে

# ---------- সাধারণ ----------
BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
MONTH = ["", "জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন", "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"]
DAY = {"Mon": "সোমবার", "Tue": "মঙ্গলবার", "Wed": "বুধবার", "Thu": "বৃহস্পতিবার", "Fri": "শুক্রবার", "Sat": "শনিবার", "Sun": "রবিবার"}
CSS = open("common.css.txt", encoding="utf-8").read()
GA = """<script async src="https://www.googletagmanager.com/gtag/js?id=G-MP1LHB6N0R"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-MP1LHB6N0R');</script>"""

def bd_now():
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=6)

def bd(ts):
    return datetime.datetime.fromtimestamp(ts, datetime.timezone.utc) + datetime.timedelta(hours=6)

def bn_time(dt):
    h, m = dt.hour, dt.minute
    ap = "রাত" if h < 4 else "ভোর" if h < 6 else "সকাল" if h < 12 else "দুপুর" if h < 15 else "বিকাল" if h < 18 else "সন্ধ্যা" if h < 20 else "রাত"
    h12 = h % 12 or 12
    return f"{ap} {h12}:{m:02d}".translate(BN)

def bn_date(dt):
    return f"{dt.day} {MONTH[dt.month]} {dt.year}".translate(BN)

def base_url():
    if os.path.exists("CNAME"):
        return "https://" + open("CNAME").read().strip().rstrip("/")
    repo = os.environ.get("GITHUB_REPOSITORY", "mylivetvbd/mylivetv-site")
    owner, name = repo.split("/")
    return f"https://{owner}.github.io/{name}"

def header(depth=0):
    p = "../" * depth
    return f"""<div class="topbar"><div class="in">
<img src="{p}logo.png" alt="My Live TV"><b>My <span>Live</span> TV</b>
<nav><a href="{p}index.html">হোম</a><a href="{p}khela.html">খেলার সূচি</a><a href="{p}blog.html">লেখা</a><a href="{p}index.html#dl">ডাউনলোড</a></nav>
</div></div>"""

def footer(depth=0):
    p = "../" * depth
    return f"""<footer>© My Live TV — বাংলাদেশের ফ্রি লাইভ TV অ্যাপ<br>
<a href="{p}about.html">আমাদের সম্পর্কে</a> • <a href="{p}contact.html">যোগাযোগ</a> • <a href="{p}privacy.html">প্রাইভেসি পলিসি</a> • <a href="{p}terms.html">ব্যবহারের শর্তাবলি</a> • <a href="{p}khela.html">আজকের খেলা</a> • <a href="{p}blog.html">সব লেখা</a></footer>"""

def wrap_page(title, desc, body, canon, depth=0):
    return f"""<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canon}">
{GA}
<style>{CSS}</style>
</head>
<body>
{header(depth)}
<div class="wrap">
{body}
</div>
{footer(depth)}
</body>
</html>"""

# ---------- স্ব-পরীক্ষা ----------
def check_page(path, must=("</html>", "wrap", "footer")):
    s = open(path, encoding="utf-8").read()
    assert len(s) > 1500, f"{path}: খুব ছোট"
    for m in must:
        assert m in s, f"{path}: '{m}' নেই"
    assert s.count("<h1") >= 1 or path.endswith(("sitemap.xml", "robots.txt")), f"{path}: h1 নেই"
    return True

# ---------- ১) খেলার সূচি ----------
def match_html(e):
    dt = bd(e["t"])
    sp = "🏏" if e.get("sp") == "c" else "⚽"
    st = e.get("st", "pre")
    badge = '<span style="color:#f87171;font-weight:800;">🔴 এই মুহূর্তে চলছে</span>' if st == "in" else ('<span style="color:#64748b;">✔ শেষ</span>' if st == "post" else bn_time(dt) + " • " + bn_date(dt))
    bc = e.get("bc") or ""
    bch = f'<div style="background:#0f2540;border-radius:8px;padding:8px 10px;font-size:13px;color:#bae6fd;margin-top:6px;">📺 <b style="color:var(--gold);">যে চ্যানেলে দেখাবে:</b> {bc}</div>' if bc else ""
    note = f'<div style="color:#fbbf24;font-size:12px;margin-top:6px;">ℹ️ {e["note"]}</div>' if e.get("note") else ""
    return (f'<div class="card"><div style="color:var(--mut);font-size:12px;">{sp} {e.get("lg","")}</div>'
            f'<div style="font-size:17px;font-weight:800;color:#fff;margin:4px 0 6px;">{e.get("h","")} vs {e.get("a","")}</div>'
            f'<div style="font-size:14px;">{badge}</div>{bch}{note}</div>')

def build_khela():
    req = urllib.request.Request(EV_URL, headers={"Accept": "application/vnd.github.raw", "User-Agent": "mlv-seo-bot"})
    data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
    evs = sorted(data.get("events", []), key=lambda x: x.get("t", 0))
    now = bd_now(); today = now.date()
    t_ev = [e for e in evs if bd(e["t"]).date() == today or e.get("st") == "in"]
    up_ev = [e for e in evs if bd(e["t"]).date() > today and e.get("st") != "in"]
    date_bn, day_bn = bn_date(now), DAY.get(now.strftime("%a"), "")
    base = base_url()
    body = f"""<h1>🏏 আজকের খেলার সূচি — <span style="color:var(--gold);">{date_bn}</span> ({day_bn})</h1>
<p class="lead">আজ কোন খেলা কোন চ্যানেলে দেখাবে — ক্রিকেট ও ফুটবলের লাইভ ম্যাচের সময়, বাংলাদেশ সময়ে। এই পেজ প্রতিদিন স্বয়ংক্রিয়ভাবে হালনাগাদ হয়।</p>
<h2>আজকের ম্যাচ</h2>
{''.join(match_html(e) for e in t_ev) or '<p class="lead">আজ বড় কোনো ম্যাচ নেই।</p>'}
<a class="cta" href="index.html#dl">📲 সব খেলা ফ্রিতে দেখুন — My Live TV অ্যাপ ডাউনলোড করুন</a>
<h2>আগামী ম্যাচ</h2>
{''.join(match_html(e) for e in up_ev[:12]) or '<p class="lead">সূচি শিগগিরই আসছে।</p>'}
<p class="lead" style="margin-top:18px;">সূত্র: প্রকাশ্য ক্রীড়াসূচি। সময় পরিবর্তন হতে পারে — চূড়ান্ত তথ্যের জন্য সম্প্রচারকারী চ্যানেল দেখুন।
আরও পড়ুন: <a href="blog.html" style="color:#93c5fd;">খেলা ও লাইভ TV নিয়ে আমাদের সব লেখা</a>।</p>"""
    title = f"আজকের খেলার সূচি ({date_bn}) — কোন খেলা কোন চ্যানেলে | My Live TV"
    desc = f"আজকের ({date_bn}) ক্রিকেট ও ফুটবল ম্যাচের সময়সূচি বাংলাদেশ সময়ে — কোন খেলা কোন টিভি চ্যানেলে দেখাবে জানুন।"
    open("khela.html", "w", encoding="utf-8").write(wrap_page(title, desc, body, f"{base}/khela.html"))
    os.makedirs("archive", exist_ok=True)
    aname = f"archive/khela-{today.isoformat()}.html"
    open(aname, "w", encoding="utf-8").write(wrap_page(title, desc, body, f"{base}/{aname}", depth=1).replace('href="index.html', 'href="../index.html').replace('href="blog.html', 'href="../blog.html'))
    check_page("khela.html"); check_page(aname)
    print(f"✔ খেলার সূচি: আজ {len(t_ev)}টি, আগামী {len(up_ev)}টি")

# ---------- ২) ভাণ্ডার থেকে লেখা প্রকাশ ----------
def publish_from_queue():
    drafts = sorted(glob.glob("draft-*.html"))
    if not drafts:
        print("✔ ভাণ্ডারে নতুন লেখা নেই"); return
    last = None
    if os.path.exists(".pubstate"):
        last = datetime.date.fromisoformat(open(".pubstate").read().strip())
    today = bd_now().date()
    if last and (today - last).days < PUB_GAP_DAYS:
        print(f"✔ অপেক্ষা: শেষ প্রকাশ {last}, {PUB_GAP_DAYS} দিন পরপর নিয়ম"); return
    d = drafts[0]
    s = open(d, encoding="utf-8").read()
    assert "</html>" in s and "<h1" in s and len(s) > 4000, f"{d}: লেখা অসম্পূর্ণ — প্রকাশ বাতিল"
    slug = re.sub(r"^draft-\d+-", "", os.path.basename(d))
    os.makedirs("blog", exist_ok=True)
    shutil.move(d, f"blog/{slug}")
    open(".pubstate", "w").write(today.isoformat())
    print(f"✔ প্রকাশিত: blog/{slug}")

# ---------- ৩) blog তালিকা ----------
def build_blog_index():
    base = base_url()
    items = []
    for f in sorted(glob.glob("blog/*.html"), key=os.path.getmtime, reverse=True):
        s = open(f, encoding="utf-8").read()
        t = re.search(r"<title>(.*?)</title>", s, re.S)
        dsc = re.search(r'name="description" content="(.*?)"', s)
        t = (t.group(1).split("|")[0].strip() if t else os.path.basename(f))
        dsc = dsc.group(1) if dsc else ""
        items.append(f'<div class="card"><a href="{f}" style="color:#fff;text-decoration:none;font-weight:800;font-size:16px;">{t}</a><p style="font-size:13px;margin:6px 0 0;color:var(--mut);">{dsc}</p></div>')
    body = f"""<h1>📝 সব লেখা</h1>
<p class="lead">খেলা, লাইভ TV আর ইন্টারনেট — দরকারি বিষয়গুলো সহজ বাংলায়। নতুন লেখা নিয়মিত যোগ হয়।</p>
{''.join(items) or '<p class="lead">প্রথম লেখা আসছে শিগগিরই।</p>'}
<a class="cta" href="index.html#dl">📲 My Live TV ফ্রি ডাউনলোড করুন</a>"""
    open("blog.html", "w", encoding="utf-8").write(wrap_page(
        "সব লেখা — খেলা ও লাইভ TV গাইড | My Live TV",
        "খেলা, লাইভ TV, ইন্টারনেট সাশ্রয় — দরকারি গাইডগুলো সহজ বাংলায়, My Live TV-র ব্লগে।",
        body, f"{base}/blog.html"))
    check_page("blog.html")
    print(f"✔ blog তালিকা: {len(items)}টি লেখা")

# ---------- ৪) sitemap + robots ----------
def build_sitemap():
    base = base_url(); today = bd_now().date().isoformat()
    pages = ["index.html", "khela.html", "blog.html", "about.html", "contact.html", "privacy.html", "terms.html"]
    pages += sorted(glob.glob("blog/*.html"), reverse=True)
    pages += sorted(glob.glob("archive/*.html"), reverse=True)[:60]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        sm.append(f"<url><loc>{base}/{p}</loc><lastmod>{today}</lastmod></url>")
    sm.append("</urlset>")
    open("sitemap.xml", "w", encoding="utf-8").write("\n".join(sm))
    open("robots.txt", "w", encoding="utf-8").write(f"User-agent: *\nAllow: /\nDisallow: /draft-\nSitemap: {base}/sitemap.xml\n")
    print(f"✔ sitemap: {len(pages)} পেজ")

if __name__ == "__main__":
    build_khela()
    publish_from_queue()
    build_blog_index()
    build_sitemap()
    print("✅ রোবটের সব কাজ শেষ, স্ব-পরীক্ষা পাস")
