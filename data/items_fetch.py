#!/usr/bin/env python3
"""Step 1 of the item pipeline: fetch Deadlocker item data into a local snapshot.

Source: https://deadlocker.gg/items (list) and https://deadlocker.gg/items/<slug> (one page per item).
Both are Next.js pages; the data is read from the embedded React Server Component payload
(self.__next_f.push chunks) plus the rendered Stats / Built from / Upgrades into sections.

Outputs (committed, so the build works offline):
  data/items_src/deadlocker_snapshot.json   parsed items, shop records, hero usage
  assets/items/<slug>.webp                 official icons (Valve asset CDN via deadlock-api)

Run:  python3 data/items_fetch.py          (about 1 minute; needs internet and curl)
"""
import concurrent.futures as cf
import html as htmllib
import json
import os
import re
import subprocess
import sys
import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CACHE = '/tmp/deadlock_items_cache'
SNAP = os.path.join(ROOT, 'data', 'items_src', 'deadlocker_snapshot.json')
ICON_DIR = os.path.join(ROOT, 'assets', 'items')
UA = 'Mozilla/5.0'


def curl(url, out):
    r = subprocess.run(['curl', '-s', '-L', '-m', '90', '-A', UA, '-o', out, '-w', '%{http_code}', url],
                       capture_output=True, text=True)
    return r.stdout.strip()


def flight(path):
    s = open(path, encoding='utf-8', errors='ignore').read()
    chunks = re.findall(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)', s)
    return ''.join(json.loads('"' + c + '"') for c in chunks)


def strip_html(h):
    h = re.sub(r'<br\s*/?>', '\n', h)
    h = re.sub(r'<[^>]+>', '', h)
    return htmllib.unescape(re.sub(r'[ \t]+', ' ', h)).strip()


def list_slugs(list_html):
    anchors = re.findall(r'<a[^>]*href="(/items/[a-z0-9\-]+)"[^>]*>', list_html)
    out = []
    for href in anchors:
        sl = href.split('/')[-1]
        if sl not in out:
            out.append(sl)
    return out


def parse_page(slug):
    t = flight(os.path.join(CACHE, f'{slug}.html'))
    d = {'deadlockerSlug': slug}
    names = [n for n in re.findall(r'"h1",null,\{"className":"[^"]*","children":"([^"]+)"', t)
             if n != 'Page not found.']
    d['name'] = names[0] if names else None
    m = re.search(r'"children":"(Weapon|Vitality|Spirit)"\}', t)
    d['category'] = m.group(1) if m else None
    m = re.search(r'"Tier ",(\d)', t)
    d['tier'] = int(m.group(1)) if m else None
    m2 = re.search(r'"children":"([^"]+)"\}\],\["\$","span",null,\{"className":"font-mono text-\[10px\][^"]*","children":"Souls"', t)
    d['costText'] = m2.group(1) if m2 else None
    m3 = re.search(r'"children":"(Active|Passive)"\}\],\["\$","span",null,\{"className":"font-mono text-\[10px\][^"]*","children":"Type"', t)
    d['type'] = m3.group(1) if m3 else None

    # Named sections: description text and relationship lists
    sections = {}
    for hm in re.finditer(r'\["\$","h2",null,\{"className":"[^"]*","children":(?:"([^"]+)"|\[[^\]]*\])\}\]', t):
        title = hm.group(1)
        if not title:
            continue
        seg = t[hm.end():hm.end() + 2500]
        nxt = re.search(r'\["\$","h2"', seg)
        window = seg[:nxt.start()] if nxt else seg
        sections.setdefault(title, window)
    d['descriptionHtml'] = None
    for key in ('Passive', 'Ability'):
        if key in sections:
            pm = re.search(r'"__html":"((?:[^"\\]|\\.)*)"', sections[key])
            if pm:
                d.setdefault('descriptionBlocks', []).append(
                    {'label': key, 'text': strip_html(json.loads('"' + pm.group(1) + '"'))})

    # Stats rows (label + displayed value), in page order
    stats = []
    for rm in re.finditer(r'\["\$","div","([A-Za-z0-9_]+)",\{"className":"flex items-center justify-between gap-3[^"]*","children":\[\["\$","span",null,\{"className":"text-text-3 text-sm","children":"((?:[^"\\]|\\.)*)"\}\],\["\$","span",null,\{"className":"font-mono[^"]*","children":(.*?)\}\]\]\}\]', t):
        key, label, valraw = rm.group(1), rm.group(2), rm.group(3)
        try:
            val = json.loads(valraw)
        except Exception:
            val = valraw
        if isinstance(val, list):
            val = ''.join(str(x) for x in val)
        stats.append({'key': key, 'label': htmllib.unescape(label), 'value': str(val)})
    d['stats'] = stats

    # Relationship lists: Built from / Upgrades into / "Other <Cat> at Tier N"
    def item_links(title_pattern):
        m = re.search(title_pattern + r'.*?(?=\["\$","h2"|\Z)', t, flags=re.S)
        if not m:
            return None
        seg = m.group(0)[:20000]
        links = re.findall(r'\["\$","\$L\d+","[0-9]+",\{"href":"/items/([a-z0-9\-]+)".*?"alt":"([^"]+)".*?"children":"([0-9,]+)"', seg, flags=re.S)
        out = []
        for sl, nm, cost in links:
            out.append({'deadlockerSlug': sl, 'name': nm, 'cost': int(cost.replace(',', ''))})
        return out
    d['builtFrom'] = item_links(r'"children":"Built from"\}\]')
    d['upgradesInto'] = item_links(r'"children":"Upgrades into"\}\]')
    m = re.search(r'\["\$","h2",null,\{"className":"[^"]*","children":\[(?:"Other ",)?"[A-Za-z]+"[^\]]*\]\}\]', t)
    d['otherAtTierLabel'] = None
    mm = re.search(r'"children":\[\s*"Other ",\s*"(Weapon|Vitality|Spirit)",\s*" at Tier ",\s*(\d)\s*\]', t)
    if mm:
        d['otherAtTierLabel'] = f'Other {mm.group(1)} at Tier {mm.group(2)}'
    d['otherAtTier'] = item_links(r'"children":\[\s*"Other ",') or []
    return d


def parse_records(any_page):
    """Shop and hero records embedded in an item page's payload."""
    t = flight(any_page)
    dec = json.JSONDecoder()
    shop, heroes = [], []
    for m in re.finditer(r'\{"id":\d+,"class_name":"(upgrade_[a-z0-9_]+|hero_[a-z0-9_]+)"', t):
        try:
            obj, _ = dec.raw_decode(t, m.start())
        except Exception:
            continue
        if obj.get('class_name', '').startswith('hero_'):
            heroes.append(obj)
        elif obj.get('shop_version') is not None:
            shop.append(obj)
    return shop, heroes


def slim_shop(r):
    desc = r.get('description') or {}
    return {
        'gameItemId': r['id'],
        'id': r['class_name'],
        'name': r['name'],
        'category': (r.get('item_slot_type') or '').capitalize(),
        'tier': r.get('item_tier'),
        'cost': r.get('cost'),
        'activation': r.get('activation'),
        'isActiveItem': bool(r.get('is_active_item')),
        'iconUrl': r.get('shop_image_webp') or r.get('shop_image'),
        'descriptionFields': {k: strip_html(v) for k, v in desc.items() if isinstance(v, str) and v.strip()},
        'properties': {k: {kk: vv for kk, vv in v.items() if kk in ('value', 'label', 'prefix', 'postfix', 'tooltip_section')}
                       for k, v in (r.get('properties') or {}).items() if isinstance(v, dict)},
    }


def slim_hero(h):
    return {
        'id': h['class_name'],
        'name': h.get('name'),
        'popularItems': h.get('popular_items') or {},
    }


def main():
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(ICON_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(SNAP), exist_ok=True)
    list_path = os.path.join(CACHE, 'list.html')
    code = curl('https://deadlocker.gg/items', list_path)
    if code != '200':
        sys.exit(f'list page HTTP {code}')
    slugs = list_slugs(open(list_path, encoding='utf-8', errors='ignore').read())
    print('listed slugs:', len(slugs))

    def get(sl):
        return sl, curl(f'https://deadlocker.gg/items/{sl}', os.path.join(CACHE, f'{sl}.html'))
    with cf.ThreadPoolExecutor(10) as ex:
        codes = dict(ex.map(get, slugs))
    bad = [s for s, c in codes.items() if c != '200']
    if bad:
        sys.exit(f'failed item pages: {bad[:10]}')

    pages = [parse_page(sl) for sl in slugs]
    shop, _ = parse_records(list_path)
    _, heroes = parse_records(os.path.join(CACHE, f'{slugs[0]}.html'))
    shop_slim = [slim_shop(r) for r in shop]
    hero_slim = [slim_hero(h) for h in heroes]

    snapshot = {
        'source': 'deadlocker.gg',
        'fetchedAt': datetime.date.today().isoformat(),
        'listUrl': 'https://deadlocker.gg/items',
        'listTotal': len(slugs),
        'pages': pages,
        'shopRecords': shop_slim,
        'heroRecords': hero_slim,
    }
    with open(SNAP, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=1)
    print('pages:', len(pages), 'shop records:', len(shop_slim), 'hero records:', len(hero_slim))

    # Official icons: shop_image_webp per item (Valve asset CDN, served through deadlock-api)
    jobs = [(s['name'], s['iconUrl']) for s in shop_slim if s.get('iconUrl')]
    def dl_icon(job):
        name, url = job
        dst = os.path.join(ICON_DIR, slug_of(name) + '.webp')
        c = curl(url, dst)
        if c != '200' or os.path.getsize(dst) < 500:
            if os.path.exists(dst):
                os.remove(dst)
            return name, c, 'FAIL'
        return name, c, os.path.getsize(dst)
    with cf.ThreadPoolExecutor(10) as ex:
        res = list(ex.map(dl_icon, jobs))
    fails = [r for r in res if r[2] == 'FAIL']
    print('icons ok:', len(res) - len(fails), 'failed:', fails[:10])


def slug_of(name):
    s = name.lower().replace('&', 'and').replace("'", '')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


if __name__ == '__main__':
    main()
