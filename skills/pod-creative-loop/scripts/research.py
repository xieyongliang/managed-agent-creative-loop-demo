"""Market-research helpers: US gifting calendar, public storefront catalogs and evidence validation."""
import argparse
from collections import Counter
from datetime import date, timedelta
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

AGENT = "PODCreativeStudio-Research/1.0 (public catalog summary; respects robots.txt)"
CHANNELS = ("amazon", "etsy", "competitor_store", "tiktok", "pinterest", "meta_ads", "trends", "industry", "other")
REQUIRED_COVERAGE = ("amazon", "etsy", "competitor_store", "tiktok", "trends")
COVERAGE = ("covered", "limited", "unavailable")
ACCESS = ("fetched", "search_result", "helper")
MIN_SOURCES = 8
MIN_CHANNELS = 3
SECTIONS = {
    "competitor_designs": ("brand", "why_it_works"),
    "keywords": ("term", "note"),
    "opportunities": ("title", "design_direction"),
    "seasonal_focus": ("occasion", "why"),
}
STOPWORDS = set("a an and are as at be by for from gift gifts in is it of on or personalized custom the this to with your you my our".split())
PERSONAL = ("personal", "custom", "name", "photo", "monogram", "engrav", "initial")


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def nth_weekday(year, month, weekday, n):
    first = date(year, month, 1)
    return first + timedelta((weekday - first.weekday()) % 7 + 7 * (n - 1))


def last_weekday(year, month, weekday):
    final = date(year + (month == 12), month % 12 + 1, 1) - timedelta(1)
    return final - timedelta((final.weekday() - weekday) % 7)


def easter(year):
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    g = (8 * b + 13) // 25
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 19 * l) // 433
    month = (h + l - 7 * m + 90) // 25
    return date(year, month, (h + l - 7 * m + 33 * month + 19) % 32)


# Lunisolar dates cannot be derived with simple arithmetic.
HANUKKAH = {2025: (12, 14), 2026: (12, 4), 2027: (12, 24), 2028: (12, 12), 2029: (12, 1), 2030: (12, 20)}
LUNAR_NEW_YEAR = {2026: (2, 17), 2027: (2, 6), 2028: (1, 26), 2029: (2, 13), 2030: (2, 3)}


def occasions(year):
    thanks = nth_weekday(year, 11, 3, 4)
    labor = nth_weekday(year, 9, 0, 1)
    teacher = nth_weekday(year, 5, 0, 1)
    rows = [
        ("new_year", "New Year's Day", date(year, 1, 1), "medium", "fresh starts, planners, family keepsakes"),
        ("galentines", "Galentine's Day", date(year, 2, 13), "medium", "best friends, sisters"),
        ("valentines", "Valentine's Day", date(year, 2, 14), "peak", "couples, spouses, long-distance partners"),
        ("womens_day", "International Women's Day", date(year, 3, 8), "medium", "mothers, mentors, colleagues"),
        ("st_patricks", "St. Patrick's Day", date(year, 3, 17), "medium", "party wear, Irish heritage"),
        ("easter", "Easter", easter(year), "high", "children, families, grandparents"),
        ("siblings_day", "National Siblings Day", date(year, 4, 10), "medium", "brothers and sisters"),
        ("pet_day", "National Pet Day", date(year, 4, 11), "medium", "dog and cat owners"),
        ("teacher_week", "Teacher Appreciation Week", teacher, "high", "teachers, from parents and students"),
        ("nurses_week", "National Nurses Week", date(year, 5, 6), "high", "nurses and healthcare staff"),
        ("mothers_day", "Mother's Day", nth_weekday(year, 5, 6, 2), "peak", "mothers, grandmothers, new moms"),
        ("graduation", "Graduation season", date(year, 5, 15), "high", "graduates, proud parents"),
        ("memorial_day", "Memorial Day", last_weekday(year, 5, 0), "medium", "military families, summer kickoff"),
        ("best_friends_day", "National Best Friends Day", date(year, 6, 8), "medium", "best friends"),
        ("fathers_day", "Father's Day", nth_weekday(year, 6, 6, 3), "peak", "fathers, grandfathers, stepdads"),
        ("juneteenth", "Juneteenth", date(year, 6, 19), "medium", "community and family celebrations"),
        ("independence_day", "Independence Day", date(year, 7, 4), "high", "families, patriotic apparel"),
        ("back_to_school", "Back-to-school season", date(year, 8, 1), "high", "students, teachers, parents"),
        ("dog_day", "National Dog Day", date(year, 8, 26), "medium", "dog owners"),
        ("grandparents_day", "Grandparents Day", labor + timedelta(6), "medium", "grandparents"),
        ("bosses_day", "Boss's Day", date(year, 10, 16), "medium", "managers, from teams"),
        ("halloween", "Halloween", date(year, 10, 31), "high", "families, pet owners, party hosts"),
        ("veterans_day", "Veterans Day", date(year, 11, 11), "medium", "veterans and military families"),
        ("thanksgiving", "Thanksgiving", thanks, "high", "hosts, families"),
        ("black_friday", "Black Friday", thanks + timedelta(1), "peak", "deal-driven gift shoppers"),
        ("cyber_monday", "Cyber Monday", thanks + timedelta(4), "peak", "online gift shoppers"),
        ("christmas", "Christmas", date(year, 12, 25), "peak", "families, couples, coworkers, pet owners"),
        ("kwanzaa", "Kwanzaa", date(year, 12, 26), "medium", "families"),
    ]
    for key, name, table, audience in (("hanukkah", "Hanukkah (first night)", HANUKKAH, "Jewish families"),
                                       ("lunar_new_year", "Lunar New Year", LUNAR_NEW_YEAR, "Asian American families")):
        if year in table:
            rows.append((key, name, date(year, *table[year]), "high" if key == "hanukkah" else "medium", audience))
    return rows


def calendar(today, days=150):
    """Upcoming US gifting occasions with planning windows. Lead times are planning heuristics, not carrier guarantees."""
    listing = {"peak": 56, "high": 42, "medium": 28}
    ads = {"peak": 42, "high": 21, "medium": 14}
    found = []
    for year in (today.year, today.year + 1):
        for key, name, when, intensity, audience in occasions(year):
            left = (when - today).days
            if not 0 <= left <= days:
                continue
            # Sale days are shopping moments, not delivery deadlines.
            sale = key in ("black_friday", "cyber_monday")
            live, push, cutoff = when - timedelta(listing[intensity]), when - timedelta(ads[intensity]), when - timedelta(0 if sale else 14)
            window = "plan" if today < live else "launch_now" if today < push else "in_market" if today < cutoff else "last_call"
            found.append({"id": key, "name": name, "kind": "sale_event" if sale else "occasion", "date": when.isoformat(), "days_until": left,
                          "gift_intensity": intensity, "audiences": audience, "listing_live_by": live.isoformat(), "ads_start_by": push.isoformat(),
                          "order_cutoff_estimate": None if sale else cutoff.isoformat(), "window": window})
    return sorted(found, key=lambda x: x["days_until"])


def public_host(value):
    host = value.strip().lower()
    host = urllib.parse.urlparse(host if "//" in host else "https://" + host).hostname or ""
    if not re.fullmatch(r"[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+", host) or re.fullmatch(r"[0-9.]+", host):
        raise ValueError("Provide a public storefront domain such as example.com")
    if host.endswith((".local", ".internal", ".localhost", ".test")):
        raise ValueError("Private hostnames are not storefronts")
    return host


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read(6 * 1024 * 1024).decode("utf-8", "replace"))


def product_row(host, p):
    tags = p.get("tags") or []
    return {"title": p.get("title"), "url": "https://%s/products/%s" % (host, p.get("handle")), "product_type": p.get("product_type") or None,
            "published": (p.get("published_at") or "")[:10] or None,
            "image": ((p.get("images") or [{}])[0]).get("src"), "tags": (tags.split(", ") if isinstance(tags, str) else tags)[:8]}


def storefront(domain, limit=60):
    """Summarise what a Shopify storefront publishes to every visitor. No login, no pagination sweeps."""
    host = public_host(domain)
    rules = urllib.robotparser.RobotFileParser("https://%s/robots.txt" % host)
    try:
        rules.read()
    except Exception:
        rules = None
    result = {"store": host, "retrieved": date.today().isoformat(), "access": "helper", "requests": []}

    def read(path):
        url = "https://%s%s" % (host, path)
        if rules and not rules.can_fetch(AGENT, url):
            result["requests"].append({"url": url, "status": "skipped: disallowed by robots.txt"})
            return None
        try:
            data = fetch(url)
            result["requests"].append({"url": url, "status": "ok"})
            return data.get("products") or []
        except urllib.error.HTTPError as error:
            result["requests"].append({"url": url, "status": "HTTP %d" % error.code})
        except Exception as error:
            result["requests"].append({"url": url, "status": type(error).__name__})
        return None

    newest = read("/products.json?limit=%d" % max(1, min(limit, 250)))
    if newest is None:
        result["status"] = "unavailable"
        result["note"] = "The storefront does not publish a readable catalog feed. Do not retry or work around the block."
        return result
    featured = None
    for handle in ("best-sellers", "bestsellers", "best-seller", "best-selling"):
        time.sleep(1)
        featured = read("/collections/%s/products.json?limit=20" % handle)
        if featured:
            result["best_seller_collection"] = handle
            break
    rows = [product_row(host, p) for p in newest]
    words = Counter(w for r in rows for w in re.findall(r"[a-z][a-z'-]{2,}", (r["title"] or "").lower()) if w not in STOPWORDS)
    result.update({
        "status": "ok", "products_read": len(rows),
        "personalized_share": round(sum(any(k in (r["title"] or "").lower() for k in PERSONAL) for r in rows) / len(rows), 2) if rows else None,
        # Cite these pages, never the JSON feeds: customers open the links.
        "store_url": "https://%s/collections/all" % host,
        "best_sellers_url": "https://%s/collections/%s" % (host, result["best_seller_collection"]) if featured else None,
        "product_types": Counter(r["product_type"] for r in rows if r["product_type"]).most_common(8),
        "title_keywords": words.most_common(20),
        "tags": Counter(t.lower() for r in rows for t in r["tags"]).most_common(15),
        "newest": sorted(rows, key=lambda r: r["published"] or "", reverse=True)[:8],
        "merchant_best_sellers": [product_row(host, p) for p in (featured or [])[:10]],
        "limits": "Catalog order and a merchant-curated best-seller collection are public merchandising signals, not sales figures.",
    })
    return result


def host_of(url):
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def validate(value, own_store=None):
    """Shape and honesty checks: every claim cites a recorded source, and thin research is labelled as such.
    own_store is the customer's own shop; it can be studied but is never a competitor."""
    own = public_host(own_store) if own_store else None
    if not isinstance(value, dict) or not nonempty(value.get("summary")):
        raise ValueError("research needs a summary")
    sources = value.get("sources")
    if not isinstance(sources, list) or len(sources) > 60:
        raise ValueError("research.sources must be a list of at most 60 entries")
    ids = set()
    for s in sources:
        if not isinstance(s, dict) or not all(nonempty(s.get(k)) for k in ("id", "title", "url", "finding", "retrieved")):
            raise ValueError("Each source needs id, title, url, finding and retrieved date")
        if s["id"] in ids:
            raise ValueError("Duplicate source id " + s["id"])
        ids.add(s["id"])
        if not s["url"].startswith("https://") or s.get("channel") not in CHANNELS or s.get("access") not in ACCESS:
            raise ValueError("Source %s needs an https url, a known channel and access fetched|search_result|helper" % s["id"])
        if re.search(r"\.json(\?|$)", s["url"]):
            raise ValueError("Source %s links to a data feed; cite the web page a person can open (store_url, best_sellers_url or a product page)" % s["id"])
        if own and s["channel"] == "competitor_store" and host_of(s["url"]).endswith(own):
            raise ValueError("Source %s is the customer's own store %s, not a competitor; use channel other" % (s["id"], own))
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s["retrieved"]):
            raise ValueError("Source %s retrieved date must be YYYY-MM-DD" % s["id"])
        metric = s.get("metric")
        if metric is not None and (not isinstance(metric, dict) or not nonempty(metric.get("label")) or not nonempty(str(metric.get("value", "")))):
            raise ValueError("Source %s metric needs label and value, or must be omitted" % s["id"])
    coverage = value.get("coverage")
    if not isinstance(coverage, list) or {c.get("channel") for c in coverage if isinstance(c, dict)} < set(REQUIRED_COVERAGE):
        raise ValueError("research.coverage must report every channel: " + ", ".join(REQUIRED_COVERAGE))
    used = Counter(s["channel"] for s in sources)
    for c in coverage:
        if c.get("channel") not in CHANNELS or c.get("status") not in COVERAGE or not nonempty(c.get("note")):
            raise ValueError("Each coverage entry needs channel, status covered|limited|unavailable and a note")
        if c["status"] == "covered" and not used[c["channel"]]:
            raise ValueError("Channel %s is marked covered without any recorded source" % c["channel"])
    for section, keys in SECTIONS.items():
        rows = value.get(section, [])
        if not isinstance(rows, list) or len(rows) > 30:
            raise ValueError("research.%s must be a list of at most 30 entries" % section)
        for row in rows:
            if not isinstance(row, dict) or not all(nonempty(row.get(k)) for k in keys):
                raise ValueError("research.%s entries need %s" % (section, " and ".join(keys)))
            cited = row.get("source_ids")
            if not isinstance(cited, list) or any(x not in ids for x in cited):
                raise ValueError("research.%s cites an unknown source id" % section)
            if not cited and row.get("basis") != "hypothesis":
                raise ValueError("research.%s entries without sources must set basis to hypothesis" % section)
            if own and section == "competitor_designs" and (own.split(".")[0] in re.sub(r"[^a-z0-9]", "", row["brand"].lower()) or host_of(row.get("url") or "").endswith(own)):
                raise ValueError("research.competitor_designs lists the customer's own store %s" % own)
    if not isinstance(value.get("risks", []), list) or any(not nonempty(x) for x in value.get("risks", [])):
        raise ValueError("research.risks must be a list of strings")
    thin = len(sources) < MIN_SOURCES or len(used) < MIN_CHANNELS
    if thin and (value.get("status") != "limited" or not nonempty(value.get("limitations"))):
        raise ValueError("Fewer than %d sources or %d channels: set research.status to limited and explain in research.limitations" % (MIN_SOURCES, MIN_CHANNELS))
    if value.get("status") not in ("complete", "limited"):
        raise ValueError("research.status must be complete or limited")
    return {"sources": len(sources), "channels": len(used), "by_channel": dict(used), "status": value["status"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["calendar", "storefront", "validate"])
    parser.add_argument("--store")
    parser.add_argument("--input")
    parser.add_argument("--today")
    parser.add_argument("--days", type=int, default=150)
    parser.add_argument("--own-store")
    args = parser.parse_args()
    try:
        if args.command == "calendar":
            today = date.fromisoformat(args.today) if args.today else date.today()
            output = {"market": "US", "today": today.isoformat(), "horizon_days": args.days, "occasions": calendar(today, args.days),
                      "note": "Dates are computed. Planning windows are heuristics; confirm production and carrier cutoffs with your print provider."}
        elif args.command == "storefront":
            output = storefront(args.store or "")
        else:
            with open(args.input) as handle:
                output = {"valid": True, **validate(json.load(handle), args.own_store)}
        print(json.dumps(output, ensure_ascii=False))
    except Exception as error:
        print(json.dumps({"status": "error", "error": str(error)[:600]}))
        sys.exit(1)
