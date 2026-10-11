#!/usr/bin/env python3
"""Step 2 of the item pipeline: turn the Deadlocker snapshot into the site's item database.

Input : data/items_src/deadlocker_snapshot.json   (written by data/items_fetch.py)
Output: data/items.json      canonical item database (fetched by the site)
        js/items-data.js     same data as a script, so the site also works from file://

Rules
- Inventory = every shop record (shop_version set). Hero records are NOT items.
- Category, tier, cost, type and every stat are copied from the source; nothing is estimated.
- Purpose tags are rule-based from verified stat labels and description text. Each tag stores
  the evidence that triggered it, so it can be checked. Tags are strategic labels, not game data.
- Editorial content (counters, buy timing, alternatives) is NOT generated and is not shown.
- Usage data (pick % and win rate per hero) is copied from Deadlocker's popular-items feed. It
  describes what players bought, not what is recommended.
"""
import datetime
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SNAP = os.path.join(ROOT, 'data', 'items_src', 'deadlocker_snapshot.json')
OUT_JSON = os.path.join(ROOT, 'data', 'items.json')
OUT_JS = os.path.join(ROOT, 'js', 'items-data.js')

CATEGORY_ORDER = ['Weapon', 'Vitality', 'Spirit']

# ---------- purpose tags ----------
# Each rule: id, label, group, and matchers. A matcher is either a stat label (exact or
# substring listed in LABELS) with an optional sign requirement, or a regex on description text.
TAGS = [
    # Offensive counters
    dict(id='anti-tank', label='Anti-tank', group='offensive', labels=[], text=[r'\btank(s|y)?\b'],
         note='No verified tank-specific mechanic in the source text, so no item is tagged.'),
    dict(id='anti-high-health', label='Anti-high-health', group='offensive',
         labels=['Max Health Damage', 'Current Health Damage', 'Current Health Bonus Damage'],
         text=[r'\b(max|current)\b[^.]{0,20}health[^.]{0,20}damage', r'damage[^.]{0,30}\b(max|current)\b[^.]{0,15}health']),
    dict(id='anti-healing', label='Anti-healing', group='offensive', labels=[],
         text=[r'(heal\w*|healing)[^.]{0,25}reduc', r'reduc\w*[^.]{0,25}(heal\w*|healing)']),
    dict(id='anti-lifesteal', label='Anti-lifesteal', group='offensive', labels=[],
         text=[r'(reduc|prevent|block|negat)\w*[^.]{0,30}lifesteal', r'lifesteal[^.]{0,30}(reduc|prevent|block|negat)']),
    dict(id='anti-regeneration', label='Anti-regeneration', group='offensive', labels=[],
         text=[r'(reduc|prevent|block|disabl|stop)\w*[^.]{0,30}regen']),
    dict(id='bullet-resist-reduction', label='Bullet resistance reduction', group='offensive',
         labels=['Bullet Resist'], negative_only=True,
         text=[r'(reduc|shred|strip|ignor|pierc)\w*[^.]{0,30}bullet resist']),
    dict(id='spirit-resist-reduction', label='Spirit resistance reduction', group='offensive',
         labels=['Spirit Resist'], negative_only=True,
         text=[r'(reduc|shred|strip|ignor|pierc)\w*[^.]{0,30}spirit resist']),
    dict(id='anti-armor', label='Anti-armor', group='offensive', labels=[],
         text=[r'\barmou?r\b[^.]{0,30}(reduc|pierc|ignor|shred)', r'(reduc|pierc|ignor|shred)\w*[^.]{0,30}\barmou?r\b']),
    dict(id='burst-damage', label='Burst damage', group='offensive', labels=[],
         text=[r'\bburst\b']),
    dict(id='sustained-damage', label='Sustained damage', group='offensive',
         labels=['Damage Per Second', 'Max DPS'], text=[r'damage over time', r'\bDPS\b', r'per second']),
    # Defensive counters
    dict(id='anti-bullet-damage', label='Anti-bullet damage', group='defensive',
         labels=['Bullet Resist', 'Max Bullet Resist', 'Bullet Resist per Stack'], positive_only=True, text=[]),
    dict(id='anti-spirit-damage', label='Anti-spirit damage', group='defensive',
         labels=['Spirit Resist', 'Spirit Damage Reduction'], positive_only=True, text=[]),
    dict(id='anti-burst', label='Anti-burst', group='defensive',
         labels=['Damage Threshold'], text=[]),
    dict(id='anti-critical-damage', label='Anti-critical damage', group='defensive', labels=[],
         text=[r'\bcritical\w*[^.]{0,30}(reduc|resist|prevent)'],
         note='No verified critical-damage mechanic found in the source text. Headshot-based resist reduction is not critical-damage protection.'),
    dict(id='healing-and-sustain', label='Healing and sustain', group='defensive',
         labels=['Heal Amount', 'Healing', 'Heal Per Stack', 'Heal On Hero Kill', 'Health Regen', 'Out of Combat Regen',
                 'Total HP Regen', 'Max Health Regen', 'Heal Interval', 'Heal Radius', 'Healing on Ability Cast',
                 'Bullet Lifesteal', 'Spirit Lifesteal', 'Max HP Steal', 'Imbued Lifesteal', 'Heal on Melee Hit',
                 'Heal Per Headshot', 'Melee Hit Heal', 'HP Healed On Activate', 'Healing From Heroes',
                 'Regeneration', 'Heal', 'Heal On Hero Kill', 'Heal Per Stack'],
         text=[r'\bheal(s|ed|ing)?\b', r'\blifesteal\b', r'\bregenerat\w*']),
    dict(id='damage-mitigation', label='Damage mitigation', group='defensive',
         labels=['Melee Resist', 'Deflection Percent', 'On-Hit Prevention Percent', 'Spirit Damage Reduction',
                 'Damage Threshold', 'Min Reduction', 'Max Bullet Resist', 'Bullet Resist', 'Spirit Resist'],
         positive_only=True, text=[r'reduces? (incoming )?damage', r'damage reduction']),
    dict(id='anti-debuff', label='Anti-debuff', group='defensive',
         labels=['Debuff Resist', 'Slow Resist'], text=[r'cleans\w*', r'\bcleanse\b', r'remov\w* (all )?(debuff|slow|stun)']),
    dict(id='survival-and-escape', label='Survival and escape', group='defensive',
         labels=['Bonus Health', 'Base Health', 'Death Immunity Duration', 'Unstoppable Duration',
                 'Invisibility Duration', 'Invis Move Speed', 'Invis Sprint Speed', 'Immunity Duration'],
         text=[r'\bescap\w*', r'\bteleport\w*', r'\binvisib\w*', r'\bimmun\w*', r'\bunstoppable\b']),
    # Utility
    dict(id='anti-mobility', label='Anti-mobility', group='utility',
         labels=['Slow Duration'], negative_only_labels=['Move Speed'],
         text=[r'(?<!immune to )\bslow(s|ed|ing)?\b(?! resist)', r'\broot\w*', r'\bsnare\w*']),
    dict(id='crowd-control', label='Crowd control', group='utility',
         labels=['Stun Duration', 'Freeze Duration', 'Daze Duration', 'Tether Duration', 'Stun Delay'],
         text=[r'\bstun\w*', r'\bfreez\w*', r'\bdaz\w*', r'\bknock\w*']),
    dict(id='silence-and-ability-disruption', label='Silence and ability disruption', group='utility',
         labels=['Silence Duration', 'Interrupt Cooldown'], text=[r'\bsilenc\w*', r'\binterrupt\w*']),
    dict(id='cooldown-reduction', label='Cooldown reduction', group='utility',
         labels=['Cooldown Reduction', 'Ability Cooldown Reduction', 'Ultimate Cooldown Reduction',
                 'Cooldown Reduction on Hit', 'Cooldown Reduction per Hit', 'Item Cooldown Reduction',
                 'Cooldown Reduction For Charged Abilities'], text=[]),
    dict(id='range-and-projectile', label='Range and projectile improvement', group='utility',
         labels=['Bullet Velocity', 'Weapon Fall-off Range', 'Bullet Radius', 'Ability Range', 'Cast Range'], text=[]),
    dict(id='reload-improvement', label='Reload improvement', group='utility',
         labels=['Bullets Reloaded'], label_contains=['Reload'], text=[r'\breload\w*']),
    dict(id='mobility-and-repositioning', label='Mobility and repositioning', group='utility',
         labels=['Move Speed', 'Sprint Speed', 'Slide Distance', 'Air Control', 'Air Jump/Dash Distance',
                 'Air Acceleration', 'Bonus Fly Speed', 'Float Speed', 'Max Move Speed'],
         positive_only_labels=['Move Speed'], text=[r'\bdash\w*', r'\bsprint\w*']),
    dict(id='team-support', label='Team support', group='utility', labels=['Ally Percentage'],
         text=[r'\ballies\b', r'\bally\b', r'\bteammates?\b']),
    dict(id='farming-and-objective-damage', label='Farming and objective damage', group='utility',
         labels=['Weapon Damage vs. NPCs', 'Bullet Resist vs. NPCs', 'Non-Hero Weapon Damage', 'Non-Hero Stack Limit',
                 'Healing From NPCs / Orbs', 'Bonus Souls', 'Souls per Minute'],
         text=[r'\bNPCs?\b', r'\bcreeps?\b', r'\bobjectives?\b', r'\bsouls? (orb|from)']),
]

LABEL_FORMS = {  # source labels that are the same mechanic under different wording
}


# Source stats that are activation delays or self-costs, i.e. official limitations of the item.
LIMITATION_LABELS = {'Cast Delay', 'Charge-Up Time', 'Health Drain', 'Stun Delay', 'Delay Before Effect',
                     'Restore Delay', 'Delay Duration', 'Interrupt Cooldown', 'Cooldown Reduction Delay'}


def is_negative(value):
    return bool(re.match(r'^\s*[-\u2212]', value or ''))


def slugify(name):
    s = name.lower().replace('&', 'and').replace("'", '')
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def find_tags(item, stats, text):
    """Return the purpose tags that the verified stats or description support, with evidence."""
    found = []
    for t in TAGS:
        ev = []
        for st in stats:
            lab, val = st['label'], st['value']
            neg = is_negative(val)
            hit = False
            if lab in t.get('labels', []):
                hit = True
            if any(c.lower() in lab.lower() for c in t.get('label_contains', [])):
                hit = True
            if hit and t.get('negative_only') and not neg:
                hit = False
            if hit and t.get('positive_only') and neg:
                hit = False
            if lab in t.get('positive_only_labels', []) and neg:
                hit = False
            if lab in t.get('negative_only_labels', []) and not neg:
                hit = False
            if lab in t.get('negative_only_labels', []) and neg:
                hit = True
            if hit:
                ev.append(f'{lab} {val}'.strip())
        for pat in t.get('text', []):
            m = re.search(pat, text, flags=re.I)
            if m:
                s = max(0, m.start() - 25)
                e = min(len(text), m.end() + 25)
                ev.append('text: "…' + text[s:e].replace('\n', ' ').strip() + '…"')
                break
        if ev:
            found.append({'id': t['id'], 'label': t['label'], 'group': t['group'], 'evidence': ev[:4]})
    return found


def main():
    with open(SNAP, encoding='utf-8') as f:
        snap = json.load(f)
    pages = {p['deadlockerSlug']: p for p in snap['pages']}
    shop = snap['shopRecords']
    if len(shop) != len(snap['pages']):
        sys.exit(f"shop records ({len(shop)}) != item pages ({len(snap['pages'])})")

    # Map Deadlocker page slug -> site slug (names are unique).
    names_seen = {}
    dl_to_site = {}
    for p in snap['pages']:
        sl = slugify(p['name'])
        if sl in names_seen:
            sys.exit(f'duplicate slug {sl}')
        names_seen[sl] = p['name']
        dl_to_site[p['deadlockerSlug']] = sl
    name_to_site = {p['name']: dl_to_site[p['deadlockerSlug']] for p in snap['pages']}

    # Site hero slugs (only real hero pages are linked).
    node = subprocess.run(['node', '-e',
        "global.window={};eval(require('fs').readFileSync('js/data.js','utf8'));"
        "console.log(JSON.stringify(window.HERO_DATA.heroes.map(h=>({slug:h.slug,name:h.name,status:h.status}))))"],
        cwd=ROOT, capture_output=True, text=True)
    site_heroes = json.loads(node.stdout)
    hero_by_norm = {re.sub(r'[^a-z0-9]', '', h['name'].lower()): h for h in site_heroes}

    # Usage: per item class_name, collect hero picks.
    usage = {}
    usage_stamp = None
    for h in snap['heroRecords']:
        pi = h.get('popularItems') or {}
        if pi.get('timestamp'):
            usage_stamp = max(usage_stamp or 0, pi['timestamp'])
        for stage_key, stage in (('early_game', 'Early'), ('mid_game', 'Mid'), ('late_game', 'Late')):
            for e in pi.get(stage_key) or []:
                usage.setdefault(e['class_name'], {}).setdefault(h['name'], []).append(
                    {'stage': stage, 'pickPct': round(e['pick_pct'], 1), 'winratePct': round(e['winrate_pct'], 1)})

    items = []
    for rec in shop:
        dl_slug = next(p['deadlockerSlug'] for p in snap['pages'] if p['name'] == rec['name'])
        page = pages[dl_slug]
        sl = dl_to_site[dl_slug]
        # Description: structured fields from the record first, then the rendered page block.
        label_map = {'passive': 'Passive', 'active': 'Active', 'desc': 'Description', 'desc2': 'Additional description'}
        desc = [{'label': label_map[k], 'text': v} for k, v in rec['descriptionFields'].items() if k in label_map]
        if not desc:
            desc = [{'label': b['label'], 'text': b['text']} for b in page.get('descriptionBlocks', []) if b.get('text')]
        stats = [{'label': s['label'], 'value': s['value']} for s in page['stats']]
        text_desc = ' '.join(d['text'] for d in desc)
        tags = find_tags(rec, stats, text_desc)
        tags_for_tag = [t for t in tags]
        built = [name_to_site[b['name']] for b in (page.get('builtFrom') or []) if b['name'] in name_to_site]
        upgrades = [name_to_site[b['name']] for b in (page.get('upgradesInto') or []) if b['name'] in name_to_site]
        same_tier = [name_to_site[b['name']] for b in (page.get('otherAtTier') or []) if b['name'] in name_to_site]
        # usage
        ustats = []
        for hname, picks in usage.get(rec['id'], {}).items():
            best = max(picks, key=lambda x: x['pickPct'])
            hkey = re.sub(r'[^a-z0-9]', '', hname.lower())
            hero = hero_by_norm.get(hkey)
            ustats.append({'hero': hname, 'heroSlug': hero['slug'] if hero else None,
                           'stage': best['stage'], 'pickPct': best['pickPct'], 'winratePct': best['winratePct']})
        ustats.sort(key=lambda x: -x['pickPct'])

        items.append({
            'id': rec['id'],
            'gameItemId': rec['gameItemId'],
            'slug': sl,
            'name': rec['name'],
            'category': rec['category'],
            'tier': rec['tier'],
            'cost': rec['cost'],
            'type': 'Active' if rec['isActiveItem'] else 'Passive',
            'activation': rec['activation'],
            'icon': f'assets/items/{sl}.webp',
            'iconSource': rec['iconUrl'],
            'description': desc,
            'stats': stats,
            'limitationStats': [s for s in stats if is_negative(s['value']) or s['label'] in LIMITATION_LABELS],
            'tags': tags,
            'builtFrom': built,
            'upgradesInto': upgrades,
            'sameCategoryTier': {'label': page.get('otherAtTierLabel'), 'items': same_tier},
            'usage': ustats[:8],
            'usageNote': None if ustats else 'No usage data in the Deadlocker feed.',
            'sources': [
                {'label': 'Deadlocker item page', 'url': f'https://deadlocker.gg/items/{dl_slug}'},
                {'label': 'Item icon (Valve asset CDN via deadlock-api)', 'url': rec['iconUrl']},
            ],
            'deadlockerSlug': dl_slug,
        })

    # sort keys for stable ordering: game order = Deadlocker list order (as scraped)
    order = {p['deadlockerSlug']: i for i, p in enumerate(snap['pages'])}
    items.sort(key=lambda it: order[it['deadlockerSlug']])

    # validation
    ids = [i['id'] for i in items]; slugs = [i['slug'] for i in items]
    assert len(set(ids)) == len(ids), 'duplicate ids'
    assert len(set(slugs)) == len(slugs), 'duplicate slugs'
    for it in items:
        assert it['category'] in CATEGORY_ORDER, it['name']
        assert it['tier'] in (1, 2, 3, 4, 5), it['name']
        assert it['cost'] and it['cost'] > 0, it['name']
        assert os.path.exists(os.path.join(ROOT, it['icon'])), it['icon']

    stamp = datetime.datetime.fromtimestamp(usage_stamp, datetime.timezone.utc).strftime('%Y-%m-%d') if usage_stamp else None
    db = {
        'schema': 1,
        'generatedFrom': 'data/items_src/deadlocker_snapshot.json',
        'dataVerified': snap['fetchedAt'],
        'source': {
            'primary': {'label': 'Deadlocker item database', 'url': snap['listUrl'],
                        'listedTotal': snap['listTotal']},
            'crossCheck': {'label': 'Deadlock.io item list (name check, 154 of 173 names matched)',
                           'url': 'https://deadlock.io/en/items'},
            'changelog': {'label': "Deadlocker changelog (from Valve's developer changelog)",
                          'url': 'https://deadlocker.gg/updates',
                          'latestEntry': 'Oct 9, 2026 - "Make Your Move."',
                          'latestUrl': 'https://deadlocker.gg/updates/make-your-move'},
            'usageSnapshot': stamp,
        },
        'counts': {
            'total': len(items),
            'byCategory': {c: sum(1 for i in items if i['category'] == c) for c in CATEGORY_ORDER},
            'byTier': {str(t): sum(1 for i in items if i['tier'] == t) for t in (1, 2, 3, 4, 5)},
            'byType': {t: sum(1 for i in items if i['type'] == t) for t in ('Passive', 'Active')},
        },
        'tagDefinitions': [{'id': t['id'], 'label': t['label'], 'group': t['group'],
                            'count': sum(1 for i in items if any(x['id'] == t['id'] for x in i['tags'])),
                            **({'note': t['note']} if t.get('note') else {})} for t in TAGS],
        'items': items,
    }
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=1)
    with open(OUT_JS, 'w', encoding='utf-8') as f:
        f.write('// Generated by data/build_items.py from data/items.json. Do not edit by hand.\n')
        f.write('window.ITEM_DATA = ' + json.dumps(db, ensure_ascii=False) + ';\n')
    print('items:', len(items), db['counts'])
    print('tags assigned:', sum(len(i['tags']) for i in items))
    print('items with no tags:', sum(1 for i in items if not i['tags']))
    print('usage items:', sum(1 for i in items if i['usage']))


if __name__ == '__main__':
    main()
