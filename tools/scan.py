#!/usr/bin/env python3
"""The Cozy Desk scanner. Fetches public feeds, writes data/feed.json,
bakes an SEO block + ItemList JSON-LD into index.html, regenerates
feed.xml and sitemap.xml. Per-section failure keeps previous data."""
import json, os, re, subprocess, sys, time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
SITE = "https://bishowpratap7.github.io/thecozydesk/"
CONFIG = json.loads(r'''{"sections": {"tonight": {"title": "🕯️ Tonight, Gently", "type": "bank", "banks": {"Tonight's journaling prompt": ["Write down three small things that went right today, even tiny ones. Especially tiny ones.", "Describe your perfect slow Sunday morning, in as much detail as you can. Then steal one piece of it for tomorrow.", "Write a letter to yourself one year from now. Seal it in an envelope or a notes app and set a date.", "List five sounds, smells and textures that instantly make you feel safe. Keep the list in your wallet.", "Write about a place where you once felt completely at peace. What was the light like?", "Make a 'someday, gently' list: things you'd like to try when your heart feels lighter. No deadlines allowed.", "Write down a compliment you've received and never let yourself believe. Read it back twice.", "Describe your dream reading nook: the chair, the blanket, the drink, the view.", "List ten things that cost nothing and reliably make your evening better.", "Write about a meal someone made for you that felt like love. Who, where, what was on the plate?", "Note three songs that feel like a warm blanket. Make the playlist real tonight.", "Write a thank-you note to a past version of you who got you through a hard month.", "Describe the coziest outfit you own, piece by piece. Plan a day to wear it for no reason.", "Write about the last time you laughed properly. Who were you with?", "Make a list of tiny luxuries under five dollars you can give yourself this week.", "Write down what 'rest' actually means to you — not sleep, rest.", "Describe your ideal tiny garden or windowsill, plant by plant.", "List the people who feel like home. Send one of them a message today.", "Write about a book, show or film that kept you company through a rough patch.", "Note five things your future self will thank you for starting small today.", "Describe a rainy-day ritual: soup, socks, a film, a chapter. Put it on the calendar.", "Write down a worry, then write the kindest possible reply to it, like you'd answer a friend.", "List your comfort films. Pick one for this weekend and make it an event.", "Write about a stranger's small kindness you still think about.", "Describe your perfect cup of tea or coffee, made slowly, step by step.", "Make a 'soft goals' list for the season: warm, kind, unhurried things only.", "Write down three places in your own home you could make ten percent cozier this week.", "List the smells of your childhood kitchen. Which one would you bottle?", "Write a bedtime story for yourself — one paragraph is plenty.", "Note one thing you can forgive yourself for tonight, in writing."], "A tiny comfort ritual": ["Light a candle, make something warm to drink, and read ten pages of anything that isn't a screen.", "Run a hot shower, put on your softest clothes, and let the evening be unproductive on purpose.", "Warm a blanket in the dryer for five minutes. Trust us on this one.", "Make soup or toast something golden, and eat it slowly by a window.", "Put your phone in another room for one hour. Music on, lights low.", "Stretch gently for five minutes, then lie down somewhere soft with no agenda.", "Brew tea like it's a ceremony: warm the pot, watch the steam, wait.", "Write one page by hand — anything. The slowness is the point.", "Step outside for one minute of cold air, then come back in and enjoy the warm twice as much.", "Rewatch the first episode of a comfort show. Notice how good familiar feels.", "Tidy one tiny surface — a nightstand, a desk corner — and light a candle beside it.", "Make hot chocolate properly, with real cocoa and a pinch of salt."], "A line to keep": ["Almost everything will work again if you unplug it for a few minutes. Including you. — Anne Lamott", "Rest is not idleness, and to lie sometimes on the grass is by no means a waste of time. — John Lubbock", "There is a crack in everything, that's how the light gets in. — Leonard Cohen", "You are braver than you believe, stronger than you seem, and smarter than you think. — A. A. Milne", "This is a wonderful day. I have never seen this one before. — Maya Angelou", "Nature does not hurry, yet everything is accomplished. — Lao Tzu", "The time to relax is when you don't have time for it. — Sydney J. Harris"]}}, "places": {"title": "🏡 Cozy Places to Daydream About", "type": "reddit", "sub": "CozyPlaces", "limit": 9}, "cute": {"title": "🐾 A Little Comfort Break", "type": "reddit", "sub": "aww", "limit": 9}, "finds": {"title": "🧣 Warm Little Finds", "type": "slickdeals", "queries": ["candle sale", "throw blanket", "tea kettle", "journal notebook", "fairy lights"], "limit": 10}}, "itemlist_name": "Today's cozy places, breaks and finds on The Cozy Desk", "feed_title": "The Cozy Desk — Tonight's Comforts", "feed_desc": "Cozy places, comfort breaks and warm little finds, refreshed around the clock."}''')

def fetch(url, timeout=25):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        out = subprocess.run(["curl", "-s", "--max-time", str(timeout), "-A", UA, url],
                             capture_output=True, text=True)
        if out.returncode == 0 and out.stdout:
            return out.stdout
        raise

def strip_tags(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    return re.sub(r"\s+", " ", t).strip()

def first_img(html):
    m = re.search(r'<img[^>]+src="([^"]+)"', html or "")
    return m.group(1) if m else ""

def price_of(title):
    m = re.search(r"\$\s?(\d+(?:\.\d{2})?)", title or "")
    return float(m.group(1)) if m else None

def scan_slickdeals(cfg):
    items, seen = [], set()
    for q in cfg["queries"]:
        url = "https://slickdeals.net/newsearch.php?rss=1&searchin=title&q=" + urllib.parse.quote(q) if False else \
              "https://slickdeals.net/newsearch.php?rss=1&searchin=title&q=" + q.replace(" ", "+")
        try:
            root = ET.fromstring(fetch(url))
        except Exception as e:
            print(f"  slickdeals '{q}': {e}", file=sys.stderr); continue
        for it in root.iter("item"):
            title = strip_tags(it.findtext("title"))
            link = (it.findtext("link") or "").strip()
            if not title or not link or link in seen:
                continue
            seen.add(link)
            enc = ""
            for ch in it:
                if ch.tag.endswith("encoded"):
                    enc = ch.text or ""
            items.append({"title": title, "url": link, "img": first_img(enc),
                          "price": price_of(title), "source": "Slickdeals community deal",
                          "meta": q})
        time.sleep(0.3)
    cap = cfg.get("max_price")
    if cap:
        cheap = [i for i in items if i["price"] is not None and i["price"] <= cap]
        items = cheap + [i for i in items if i not in cheap]
    return items[: cfg.get("limit", 12)]

def scan_reddit(cfg):
    sub = cfg["sub"]
    raw = fetch(f"https://www.reddit.com/r/{sub}/hot/.rss?limit=30")
    ns = {"a": "http://www.w3.org/2005/Atom", "m": "http://search.yahoo.com/mrss/"}
    root = ET.fromstring(raw)
    items = []
    for e in root.findall("a:entry", ns):
        title = strip_tags(e.findtext("a:title", default="", namespaces=ns))
        link, img = "", ""
        for l in e.findall("a:link", ns):
            if l.get("rel") in (None, "alternate"):
                link = l.get("href", "")
        th = e.find("m:thumbnail", ns)
        if th is not None:
            img = th.get("url", "")
        if not img:
            img = first_img(e.findtext("a:content", default="", namespaces=ns))
        if title and link:
            items.append({"title": title, "url": link, "img": img, "price": None,
                          "source": f"r/{sub}", "meta": "Community post"})
        if len(items) >= cfg.get("limit", 10):
            break
    return items

def scan_mealdb(cfg):
    import random
    cats = cfg["categories"]
    day = datetime.now(timezone.utc).timetuple().tm_yday
    rng = random.Random(day)
    items = []
    picks = [cats[day % len(cats)]] + rng.sample(cats, min(2, len(cats) - 1))
    seen = set()
    for cat in picks:
        try:
            data = json.loads(fetch(f"https://www.themealdb.com/api/json/v1/1/filter.php?c={cat}"))
        except Exception as e:
            print(f"  mealdb {cat}: {e}", file=sys.stderr); continue
        meals = data.get("meals") or []
        rng.shuffle(meals)
        for m in meals[:4]:
            if m["idMeal"] in seen:
                continue
            seen.add(m["idMeal"])
            items.append({"title": m["strMeal"], "img": m.get("strMealThumb", ""),
                          "url": f"https://www.themealdb.com/meal/{m['idMeal']}",
                          "price": None, "source": "TheMealDB", "meta": cat})
    return items[: cfg.get("limit", 10)]

def scan_bank(cfg):
    day = datetime.now(timezone.utc).timetuple().tm_yday
    out = []
    for kind, bank in cfg["banks"].items():
        out.append({"title": bank[day % len(bank)], "url": "", "img": "",
                    "price": None, "source": "The Cozy Desk", "meta": kind})
    return out

SCANNERS = {"slickdeals": scan_slickdeals, "reddit": scan_reddit,
            "mealdb": scan_mealdb, "bank": scan_bank}

def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def main():
    prev = {}
    pdata = os.path.join(ROOT, "data", "feed.json")
    if os.path.exists(pdata):
        try:
            prev = json.load(open(pdata))
        except Exception:
            prev = {}
    out = {"generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
           "sections": {}}
    for key, cfg in CONFIG["sections"].items():
        try:
            items = SCANNERS[cfg["type"]](cfg)
            if not items:
                raise RuntimeError("empty")
            out["sections"][key] = {"title": cfg["title"], "items": items, "stale": False}
            print(f"{key}: {len(items)} items")
        except Exception as e:
            old = (prev.get("sections") or {}).get(key)
            if old:
                out["sections"][key] = {**old, "stale": True}
                print(f"{key}: FAILED ({e}); kept previous")
            else:
                out["sections"][key] = {"title": cfg["title"], "items": [], "stale": True}
                print(f"{key}: FAILED ({e}); no previous data")
    with open(pdata, "w") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    bake(out)
    return 0

def bake(out):
    ipath = os.path.join(ROOT, "index.html")
    html = open(ipath).read()
    lines, items, pos = [], [], 1
    for key, sec in out["sections"].items():
        lines.append(f"<h3>{esc(sec['title'])}</h3><ul>")
        for it in sec["items"]:
            price = f" — {('$' + format(it['price'], 'g')) if it.get('price') else ''}" if it.get("price") else ""
            lines.append(f"<li><a href=\"{esc(it['url'])}\">{esc(it['title'])}</a>{price} "
                         f"<span>({esc(it.get('source',''))})</span></li>")
            if it.get("url"):
                items.append({"@type": "ListItem", "position": pos, "name": it["title"][:110], "url": it["url"]})
                pos += 1
        lines.append("</ul>")
    block = "\n".join(lines)
    ld = {"@context": "https://schema.org", "@type": "ItemList",
          "name": CONFIG["itemlist_name"], "itemListElement": items}
    ld_html = '<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False) + "\n</script>"
    new = re.sub(r"<!--FEED:START-->.*?<!--FEED:END-->",
                 "<!--FEED:START-->\n" + block + "\n<!--FEED:END-->", html, flags=re.S)
    new = re.sub(r"<!--ITEMLIST:START-->.*?<!--ITEMLIST:END-->",
                 "<!--ITEMLIST:START-->\n" + ld_html + "\n<!--ITEMLIST:END-->", new, flags=re.S)
    if new != html:
        open(ipath, "w").write(new)
        write_feed(out); write_sitemap(out)
        print("baked: changed")
    else:
        print("baked: unchanged")

def write_feed(out):
    items = ""
    for sec in out["sections"].values():
        for it in sec["items"][:4]:
            if not it.get("url"):
                continue
            items += (f"<item><title>{esc(it['title'])}</title><link>{esc(it['url'])}</link>"
                      f"<guid>{esc(it['url'])}</guid><pubDate>{out['generated_at']}</pubDate></item>\n")
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
            f"<title>{esc(CONFIG['feed_title'])}</title><link>{SITE}</link>"
            f"<description>{esc(CONFIG['feed_desc'])}</description>\n" + items + "</channel></rss>")
    open(os.path.join(ROOT, "feed.xml"), "w").write(feed)

def write_sitemap(out):
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
          f"<url><loc>{SITE}</loc><lastmod>{out['generated_at']}</lastmod>"
          "<changefreq>hourly</changefreq><priority>1.0</priority></url></urlset>")
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(sm)

if __name__ == "__main__":
    sys.exit(main())
