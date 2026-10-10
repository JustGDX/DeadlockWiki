"""Builds data/heroes.js from verified sources.

Sources (all cited on each hero page):
- Deadlock Wiki (deadlock.wiki): hero roster, release dates, traits, Hero Comparison Table stats
- Dexerto Deadlock wiki (dexerto.com): role, difficulty, weapon type
- Deadlock Labs (deadlocklabs.gg): win rate, pick rate, tier, worst matchups, best matchups, best synergies
Anything a source did not provide is written as None and rendered as "Pending" on the site.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
DL = json.load(open(os.path.join(HERE, 'deadlocklabs_raw.json'), encoding='utf-8'))

# slug, display name, wiki page title, dexerto slug, release date (Deadlock Wiki "Heroes by release")
ROSTER = [
 ('abrams','Abrams','Abrams','abrams','2024-04-24'),
 ('apollo','Apollo','Apollo','apollo','2026-02-12'),
 ('baba','Baba','Baba',None,'2026-10-06'),
 ('bebop','Bebop','Bebop','bebop','2024-04-24'),
 ('billy','Billy','Billy','billy','2025-08-20'),
 ('calico','Calico','Calico','calico','2025-01-17'),
 ('celeste','Celeste','Celeste','celeste','2026-02-09'),
 ('the-doorman','The Doorman','The_Doorman','the-doorman','2025-08-22'),
 ('drifter','Drifter','Drifter','drifter','2025-08-27'),
 ('dynamo','Dynamo','Dynamo','dynamo','2024-04-24'),
 ('graves','Graves','Graves','graves','2026-01-29'),
 ('grey-talon','Grey Talon','Grey_Talon','grey-talon','2024-04-24'),
 ('haze','Haze','Haze','haze','2024-04-24'),
 ('holliday','Holliday','Holliday','holliday','2025-01-17'),
 ('infernus','Infernus','Infernus','infernus','2024-04-24'),
 ('ivy','Ivy','Ivy','ivy','2024-04-24'),
 ('kelvin','Kelvin','Kelvin','kelvin','2024-04-24'),
 ('lady-geist','Lady Geist','Lady_Geist','lady-geist','2024-04-24'),
 ('lash','Lash','Lash','lash','2024-04-24'),
 ('mcginnis','McGinnis','McGinnis','mcginnis','2024-04-24'),
 ('mina','Mina','Mina','mina','2025-08-18'),
 ('mirage','Mirage','Mirage','mirage','2024-09-26'),
 ('mo-and-krill','Mo & Krill','Mo_%26_Krill','mo-krill','2024-04-24'),
 ('paige','Paige','Paige','paige','2025-08-25'),
 ('paradox','Paradox','Paradox','paradox','2024-04-24'),
 ('pocket','Pocket','Pocket','pocket','2024-04-24'),
 ('rat-king','Rat King','Rat_King',None,'2026-10-02'),
 ('rem','Rem','Rem','rem','2026-01-26'),
 ('solomon','Solomon','Solomon',None,'2026-10-10'),
 ('seven','Seven','Seven','seven','2024-04-24'),
 ('shiv','Shiv','Shiv','shiv','2024-08-15'),
 ('silver','Silver','Silver','silver','2026-02-02'),
 ('sinclair','Sinclair','Sinclair','sinclair','2025-01-17'),
 ('venator','Venator','Venator','venator','2026-02-05'),
 ('victor','Victor','Victor','victor','2025-08-29'),
 ('vindicta','Vindicta','Vindicta','vindicta','2024-04-24'),
 ('viscous','Viscous','Viscous','viscous','2024-08-01'),
 ('vyper','Vyper','Vyper','vyper','2025-01-17'),
 ('warden','Warden','Warden','warden','2024-04-24'),
 ('wraith','Wraith','Wraith','wraith','2024-04-24'),
 ('yamato','Yamato','Yamato','yamato','2024-04-24'),
]
UPCOMING = [
 ('deadman-danny','Deadman Danny','Deadman_Danny',None,None,'Currently voting (Deadlock Wiki)'),
 ('nurse-harrow','Nurse Harrow','Nurse_Harrow',None,None,'Currently voting (Deadlock Wiki)'),
 ('violet','Violet','Violet',None,None,'Currently voting (Deadlock Wiki)'),
]

# Official traits row from Deadlock Wiki Heroes page
TRAITS = {
 'abrams':['Tank','Brawler','Bull-Headed'], 'apollo':['Finesse','Mobility','A Cut Above'],
 'baba':['Cackling','Beady','Hexing'], 'bebop':['Hook','Bomb','Punch'], 'billy':['Punk','Chaotic','G.O.A.T.'],
 'calico':['Tricksy','Slippery','Burst Damage'], 'celeste':['Performer','Disruptive','Dazzling'],
 'deadman-danny':['Reckless','High-flying','Explosive'], 'the-doorman':['Disorienting','Map Control','Mind Games'],
 'drifter':['Stalker','Bloodthirsty','Cruel'], 'dynamo':['Teamplay','Initiator','Clutch'],
 'graves':['Morbid','Area Denial','Necromancer'], 'grey-talon':['Precision','Hunter','Area Denial'],
 'haze':['Assassin','Stealthy','Lethal'], 'holliday':['Crackshot','Explosive','Apprehender'],
 'infernus':['Arsonist','Explosive','Burn Rubber'], 'ivy':['Team-up','Disruptor','Rock Solid'],
 'kelvin':['Protector','Explorer','Ice Cold'], 'lady-geist':['Lifesteal','Self Damage','Fatale'],
 'lash':['Initiator','High-Flying','Arrogant'], 'mcginnis':['Inventor','Support','Disruption'],
 'mina':['Harasser','Nimble','Vexing'], 'mirage':['Bodyguard','Traveller','Focused'],
 'mo-and-krill':['Tag-Team','Initiator','Burrower'], 'nurse-harrow':['Strict','Terrifying','Savior'],
 'paige':['Helpful','Protector','Booksmart'], 'paradox':['Calculated','Disruptor','Tactician'],
 'pocket':['Trickster','Burst Damage','Frogs'], 'rat-king':['Scrappy','Regal','Tenacious'],
 'rem':['Helpful','Tiny','zZzzZ'], 'seven':['High Voltage','Merciless','Area Denial'],
 'shiv':['Rage','Bleed','Repeat'], 'silver':['Feral','Hot Mess','Transformation'],
 'sinclair':['Trickster','Copycat','Versatile'], 'solomon':['Strategist','Focused','Checkmate'],
 'venator':['Devout','Arms Expert','Tactical'], 'victor':["You",'Can\'t','Kill Me'],
 'vindicta':['Sniper','Soaring','One Shot Kill'], 'violet':['Ambitious','Nimble','Creative'],
 'viscous':['Evasive','Disruptor','Gooey'], 'vyper':['Gunner','Slippery','Rat-a-Tat'],
 'warden':['Initiator','Fearless','One Man Army'], 'wraith':['Duelist','Isolator','Telekinetic'],
 'yamato':['Relentless','Acrobatics','Pursuer'],
}

# Role, difficulty and weapon type from Dexerto (None = not listed there yet)
DEXERTO = {
 'abrams':('Brawler','Easy','Shotgun'), 'apollo':('Assassin','Medium','Spreadshot'),
 'baba':('Mystic','Easy','Heavy Artillery'), 'bebop':('Brawler','Medium','Beam Weapon'),
 'billy':('Brawler','Hard','Close Range'), 'calico':('Assassin','Medium','Spreadshot'),
 'celeste':('Mystic','Medium','Burst Fire'), 'the-doorman':('Mystic','Easy','Pistol'),
 'drifter':('Assassin','Hard','Spreadshot'), 'dynamo':('Mystic','Medium','Pistol'),
 'graves':('Mystic','Medium','Pistol'), 'grey-talon':('Marksman','Medium','Bow'),
 'haze':('Assassin','Easy','Rapid Fire'), 'holliday':('Marksman','Hard','Pistol'),
 'infernus':('Marksman','Easy','Rapid Fire'), 'ivy':('Marksman','Hard','Rapid Fire'),
 'kelvin':('Brawler','Medium','Heavy Hitter'), 'lady-geist':('Mystic','Medium','Pistol'),
 'lash':('Assassin','Hard','Burst Fire'), 'mcginnis':('Mystic','Easy','Heavy Artillery'),
 'mina':('Marksman','Hard','Pistol'), 'mirage':('Assassin','Medium','Pistol'),
 'mo-and-krill':('Brawler','Hard','Spreadshot'), 'paige':('Mystic','Easy','Projectile'),
 'paradox':('Marksman','Hard','Burst Fire'), 'pocket':('Assassin','Medium','Spreadshot'),
 'rem':('Mystic','Hard',None), 'seven':('Mystic','Easy','Burst Fire'),
 'shiv':('Brawler','Hard','Spreadshot'), 'silver':('Brawler','Easy','Long Range'),
 'sinclair':('Mystic','Expert','Burst Fire'), 'venator':('Marksman','Medium','Crossbow'),
 'victor':('Brawler','Medium','Pistol'), 'vindicta':('Marksman','Easy','Long Range'),
 'viscous':('Mystic','Medium','Projectile'), 'vyper':('Assassin','Easy','Rapid Fire'),
 'warden':('Brawler','Medium','Heavy Hitter'), 'wraith':('Marksman','Easy','Rapid Fire'),
 'yamato':('Assassin','Hard','Spreadshot'),
}

# Deadlock Wiki "Hero Comparison Table": [value, boon increment] pairs; spirit scaling as text
# Keys: dps, bulletDamage, bulletsPerSec, ammo, lightMelee, heavyMelee, maxHealth, healthRegen, moveSpeed, spiritPower
S = {
 'abrams':dict(dps=[51.43,1.43],bulletDamage=[3.6,0.1],bulletsPerSec=1.587,ammo=9,lightMelee=[50,1.74],heavyMelee=[116,4.03],maxHealth=[800,49],healthRegen=1.5,moveSpeed=6.4,spiritPower=[0,1.1],scaling=[]),
 'apollo':dict(dps=[48.69,2.17],bulletDamage=[18.5,0.825],bulletsPerSec=2.632,ammo=15,lightMelee=[63,1.58],heavyMelee=[116,2.91],maxHealth=[770,45],healthRegen=1,moveSpeed=7.2,spiritPower=[0,1.1],scaling=[]),
 'baba':dict(dps=[28.39,1.32],bulletDamage=[8.8,0.41],bulletsPerSec=3.226,ammo=15,lightMelee=[50,0.7],heavyMelee=[116,1.62],maxHealth=[780,45],healthRegen=2.5,moveSpeed=6.5,spiritPower=[0,1.1],scaling=[]),
 'bebop':dict(dps=[59.29,1.37],bulletDamage=[4.98,0.115],bulletsPerSec=11.91,ammo=66,lightMelee=[63,1.58],heavyMelee=[116,2.91],maxHealth=[880,52],healthRegen=2.5,moveSpeed=6.45,spiritPower=[0,1.1],scaling=[]),
 'billy':dict(dps=[74.12,1.49],bulletDamage=[6.3,0.127],bulletsPerSec=11.77,ammo=30,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[820,53],healthRegen=2,moveSpeed=7,spiritPower=[0,1.1],scaling=[]),
 'calico':dict(dps=[78.86,1.84],bulletDamage=[1.84,0.043],bulletsPerSec=4.762,ammo=12,lightMelee=[63,1.58],heavyMelee=[116,2.91],maxHealth=[730,37],healthRegen=2,moveSpeed=6.8,spiritPower=[0,1.1],scaling=[]),
 'celeste':dict(dps=[31.03,1.41],bulletDamage=[18,0.82],bulletsPerSec=1.724,ammo=8,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[690,33],healthRegen=1,moveSpeed=6.2,spiritPower=[0,1.1],scaling=[]),
 'the-doorman':dict(dps=[38.1,1.98],bulletDamage=[24,1.25],bulletsPerSec=1.587,ammo=8,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[755,42],healthRegen=1,moveSpeed=7.9,spiritPower=[0,1.1],scaling=[]),
 'drifter':dict(dps=[44.22,1.11],bulletDamage=[19.5,0.49],bulletsPerSec=2.268,ammo=12,lightMelee=[51.5,1.58],heavyMelee=[120,3.68],maxHealth=[755,41],healthRegen=3.5,moveSpeed=6.9,spiritPower=[0,1.1],scaling=[]),
 'dynamo':dict(dps=[48,1.9],bulletDamage=[12.6,0.5],bulletsPerSec=3.81,ammo=20,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[880,61],healthRegen=1.75,moveSpeed=6.7,spiritPower=[0,1.1],scaling=[]),
 'graves':dict(dps=[35.29,0.529],bulletDamage=[3.6,0.054],bulletsPerSec=9.804,ammo=40,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[730,35],healthRegen=1,moveSpeed=7,spiritPower=[0,1.1],scaling=[]),
 'grey-talon':dict(dps=[39.18,1.42],bulletDamage=[23.51,0.85],bulletsPerSec=1.667,ammo=17,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[780,38],healthRegen=1.5,moveSpeed=6.3,spiritPower=[0,1.6],scaling=['DPS ×0.133 per Spirit Power','Sustained DPS ×0.108 per Spirit Power','Bullet damage ×0.08 per Spirit Power','Move speed ×0.0084 per Spirit Power']),
 'haze':dict(dps=[50.1,1.36],bulletDamage=[5.26,0.143],bulletsPerSec=9.524,ammo=25,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[730,33],healthRegen=2,moveSpeed=8.2,spiritPower=[0,0.5],scaling=['Sustained DPS ×0.247 per Spirit Power','Ammo ×0.5 per Spirit Power']),
 'holliday':dict(dps=[41.69,2.42],bulletDamage=[19.7,1.14],bulletsPerSec=2.116,ammo=10,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[780,43],healthRegen=2,moveSpeed=8.2,spiritPower=[0,1.1],scaling=[]),
 'infernus':dict(dps=[52.38,0.838],bulletDamage=[5.5,0.088],bulletsPerSec=9.524,ammo=27,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[830,39],healthRegen=2,moveSpeed=6.7,spiritPower=[0,1.1],scaling=[]),
 'ivy':dict(dps=[60.54,1.09],bulletDamage=[4.45,0.08],bulletsPerSec=13.61,ammo=33,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[755,45],healthRegen=2,moveSpeed=7.2,spiritPower=[0,1.2],scaling=[]),
 'kelvin':dict(dps=[70.86,1.59],bulletDamage=[18.6,0.418],bulletsPerSec=3.81,ammo=14,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[880,60],healthRegen=1,moveSpeed=6.7,spiritPower=[0,1.3],scaling=[]),
 'lady-geist':dict(dps=[43.81,2.12],bulletDamage=[20.7,1],bulletsPerSec=2.116,ammo=9,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[880,51],healthRegen=1,moveSpeed=6.3,spiritPower=[0,1.1],scaling=[]),
 'lash':dict(dps=[49.33,1.81],bulletDamage=[8.46,0.31],bulletsPerSec=5.831,ammo=29,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[780,50],healthRegen=2,moveSpeed=7.2,spiritPower=[0,1.1],scaling=[]),
 'mcginnis':dict(dps=[72.38,2.04],bulletDamage=[6.08,0.171],bulletsPerSec=4.762,ammo=66,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[780,52],healthRegen=2,moveSpeed=6.7,spiritPower=[0,1.1],scaling=[]),
 'mina':dict(dps=[29.01,1.09],bulletDamage=[7.31,0.275],bulletsPerSec=3.968,ammo=12,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[660,27],healthRegen=2,moveSpeed=6.5,spiritPower=[0,1.1],scaling=[]),
 'mirage':dict(dps=[40.27,0.816],bulletDamage=[14.8,0.3],bulletsPerSec=2.721,ammo=16,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[730,45],healthRegen=1.5,moveSpeed=7,spiritPower=[0,1.1],scaling=[]),
 'mo-and-krill':dict(dps=[59.68,1.79],bulletDamage=[2.82,0.0847],bulletsPerSec=5.291,ammo=20,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[930,65],healthRegen=1,moveSpeed=8,spiritPower=[0,1.1],scaling=[]),
 'paige':dict(dps=[70,1.04],bulletDamage=[35,0.52],bulletsPerSec=2,ammo=14,lightMelee=[42,1.2],heavyMelee=[120,3.43],maxHealth=[680,31],healthRegen=2,moveSpeed=6.9,spiritPower=[0,1.1],scaling=['Heavy melee ×0.45 per Spirit Power']),
 'paradox':dict(dps=[51.4,1.97],bulletDamage=[6.8,0.26],bulletsPerSec=7.559,ammo=40,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[730,46],healthRegen=1,moveSpeed=6.7,spiritPower=[0,1.1],scaling=[]),
 'pocket':dict(dps=[57.07,1.87],bulletDamage=[4.28,0.14],bulletsPerSec=1.905,ammo=11,lightMelee=[60,1.58],heavyMelee=[116,3.05],maxHealth=[780,36],healthRegen=1,moveSpeed=7.2,spiritPower=[0,1.1],scaling=[]),
 'rat-king':dict(dps=[60,1.8],bulletDamage=[6,0.18],bulletsPerSec=5,ammo=24,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[800,50],healthRegen=2,moveSpeed=6.8,spiritPower=[0,1.1],scaling=[]),
 'rem':dict(dps=[61.54,1.31],bulletDamage=[16,0.34],bulletsPerSec=3.846,ammo=13,lightMelee=[58,1.58],heavyMelee=[116,3.16],maxHealth=[680,28],healthRegen=2,moveSpeed=7.2,spiritPower=[0,1.1],scaling=[]),
 'seven':dict(dps=[62.97,1.4],bulletDamage=[10.8,0.24],bulletsPerSec=5.831,ammo=29,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[730,41],healthRegen=1,moveSpeed=6.7,spiritPower=[0,1.1],scaling=[]),
 'shiv':dict(dps=[52.25,1.8],bulletDamage=[4.8,0.165],bulletsPerSec=1.814,ammo=10,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[830,46],healthRegen=2,moveSpeed=6.5,spiritPower=[0,1.1],scaling=[]),
 'silver':dict(dps=[42,0.964],bulletDamage=[5.1,0.117],bulletsPerSec=1.177,ammo=7,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[830,31],healthRegen=2.5,moveSpeed=6.7,spiritPower=[0,1.1],scaling=[]),
 'sinclair':dict(dps=[44.9,1.5],bulletDamage=[16.5,0.55],bulletsPerSec=2.721,ammo=16,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[730,38],healthRegen=1,moveSpeed=7.2,spiritPower=[0,1.3],scaling=['Move speed ×0.0138 per Spirit Power']),
 'venator':dict(dps=[63.49,2.14],bulletDamage=[8,0.27],bulletsPerSec=7.937,ammo=33,lightMelee=[50,1.7],heavyMelee=[125,4.25],maxHealth=[820,43],healthRegen=2,moveSpeed=6.4,spiritPower=[0,1.1],scaling=[]),
 'victor':dict(dps=[70.18,1.52],bulletDamage=[12,0.26],bulletsPerSec=5.051,ammo=24,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[800,34],healthRegen=1.5,moveSpeed=6.3,spiritPower=[0,1.1],scaling=['Health regen ×0.08 per Spirit Power']),
 'vindicta':dict(dps=[53.38,2.14],bulletDamage=[12.33,0.495],bulletsPerSec=4.329,ammo=19,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[755,28],healthRegen=2,moveSpeed=7.9,spiritPower=[0,1.1],scaling=['DPS ×0.0952 per Spirit Power','Sustained DPS ×0.0572 per Spirit Power','Bullet damage ×0.022 per Spirit Power']),
 'viscous':dict(dps=[49.24,1.71],bulletDamage=[10.34,0.36],bulletsPerSec=4.762,ammo=20,lightMelee=[63,1.58],heavyMelee=[116,2.91],maxHealth=[780,45],healthRegen=2,moveSpeed=7.2,spiritPower=[0,1.3],scaling=[]),
 'vyper':dict(dps=[94,2.54],bulletDamage=[6.58,0.178],bulletsPerSec=14.29,ammo=24,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[780,35],healthRegen=2,moveSpeed=6.9,spiritPower=[0,1.1],scaling=['Move speed ×0.0138 per Spirit Power']),
 'warden':dict(dps=[66.06,0.952],bulletDamage=[17.34,0.25],bulletsPerSec=3.81,ammo=17,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[805,60],healthRegen=2,moveSpeed=6.3,spiritPower=[0,1.1],scaling=['DPS ×0.139 per Spirit Power','Sustained DPS ×0.0507 per Spirit Power','Bullets/sec ×0.008 per Spirit Power','Fire rate ×0.21 per Spirit Power']),
 'wraith':dict(dps=[59.68,1.48],bulletDamage=[5.64,0.14],bulletsPerSec=10.58,ammo=52,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[730,35],healthRegen=2,moveSpeed=7.2,spiritPower=[0,1.1],scaling=['Sprint speed ×0.05 per Spirit Power']),
 'yamato':dict(dps=[63.22,1.83],bulletDamage=[5.31,0.154],bulletsPerSec=2.381,ammo=12,lightMelee=[55,1.58],heavyMelee=[128,3.68],maxHealth=[730,45],healthRegen=1,moveSpeed=8.2,spiritPower=[0,1.1],scaling=['Sustained DPS ×0.172 per Spirit Power','Ammo ×0.15 per Spirit Power']),
 # upcoming (unreleased stats may change, per Deadlock Wiki note)
 'deadman-danny':dict(dps=[52.38,4],bulletDamage=[5.5,0.42],bulletsPerSec=9.524,ammo=27,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[780,39],healthRegen=2,moveSpeed=7.2,spiritPower=[0,1.1],scaling=[]),
 'nurse-harrow':dict(dps=[52.38,5.06],bulletDamage=[5.5,0.532],bulletsPerSec=9.524,ammo=27,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[780,31],healthRegen=2,moveSpeed=7.2,spiritPower=[0,1.1],scaling=[]),
 'solomon':dict(dps=[60,0.8],bulletDamage=[30,0.4],bulletsPerSec=2,ammo=8,lightMelee=[50,1.58],heavyMelee=[116,3.67],maxHealth=[780,40],healthRegen=2,moveSpeed=6.7,spiritPower=[0,1.1],scaling=['DPS ×0.28 per Spirit Power','Sustained DPS ×0.16 per Spirit Power','Bullet damage ×0.14 per Spirit Power']),
 'violet':dict(dps=[52.38,5.24],bulletDamage=[5.5,0.55],bulletsPerSec=9.524,ammo=27,lightMelee=[50,1.2],heavyMelee=[116,2.78],maxHealth=[780,34],healthRegen=2,moveSpeed=7.2,spiritPower=[0,1.1],scaling=[]),
}

WEAPON_KEYS = ('dps','bulletDamage','bulletsPerSec','ammo')
def classify(scaling):
    # Legacy stat-level fallback (not used for the tag any more; see ability_tag)
    text = ' '.join(scaling).lower()
    if any(k in text for k in ['dps','bullet damage','bullets/sec','fire rate','ammo']):
        return 'Hybrid'
    return 'Weapon'

# Ability-level Spirit tags from data/spirit_ability_scaling.json
# Rule: Spirit = >=3 of 4 abilities scale with Spirit; Hybrid = 2 of 4; Weapon = 0-1 of 4; Pending = no verified data.
import json as _json
_SPIRIT = _json.load(open(os.path.join(HERE, 'spirit_ability_scaling.json'), encoding='utf-8'))
_SPIRIT_ALIAS = {'mo-krill': 'mo-and-krill'}
def _spirit_entry(slug):
    slug = _SPIRIT_ALIAS.get(slug, slug)
    return _SPIRIT.get('batch2', {}).get(slug)
def ability_tag(slug):
    slug = _SPIRIT_ALIAS.get(slug, slug)
    ov = _SPIRIT.get('user_overrides', {}).get('tags', {}).get(slug)
    if ov:
        return ov
    b = _spirit_entry(slug)
    if b and b.get('spirit_count') is not None:
        n = b['spirit_count']
        return 'Spirit' if n >= 3 else ('Hybrid' if n == 2 else 'Weapon')
    first = _SPIRIT.get('classes_first_batch', {}).get(slug)
    if first:
        if first.startswith('Spirit'): return 'Spirit'
        if first.startswith('Hybrid'): return 'Hybrid'
        return 'Weapon'
    return 'Pending'
def ability_spirit_lines(slug):
    slug = _SPIRIT_ALIAS.get(slug, slug)
    b = _spirit_entry(slug)
    if b and b.get('abilities'):
        return [f'{k}: {v}' for k, v in b['abilities'].items() if 'spirit' in v.lower() and 'not counted' not in v.lower() and 'no spirit' not in v.lower()]
    first = _SPIRIT.get('heroes', {}).get(slug)
    if first:
        return list(first)
    return []

PENDING_NOTE = 'Not yet in a verified source'
def dl_name_to_slug():
    m = {}
    for slug, name, *_ in ROSTER + [(u[0],u[1]) for u in UPCOMING]:
        m[name.lower()] = slug
    m['krill'] = 'mo-and-krill'
    return m
NAME2SLUG = dl_name_to_slug()
def to_slug(n):
    return NAME2SLUG.get(n.strip().lower())

def dl_entry(slug):
    d = DL.get(slug)
    if not d:
        return None
    worst = []
    for w in d.get('worst', []):
        s = to_slug(w['name'])
        worst.append({'name': w['name'] if s is None else next(r[1] for r in ROSTER+[(u[0],u[1]) for u in UPCOMING] if r[0]==s), 'slug': s, 'delta': w['delta']})
    syn = []
    for w in d.get('synergy', []):
        s = to_slug(w['name'])
        syn.append({'name': w['name'] if s is None else next(r[1] for r in ROSTER+[(u[0],u[1]) for u in UPCOMING] if r[0]==s), 'slug': s, 'delta': w['delta']})
    best = []
    for r in sorted(d.get('best_matchups', []), key=lambda x: -(x.get('wr') or 0)):
        s = r['enemy_slug']
        name = next((x[1] for x in ROSTER+[(u[0],u[1]) for u in UPCOMING] if x[0]==s), r['enemy'])
        best.append({'name': name, 'slug': s, 'wr': r['wr'], 'delta': r['delta']})
    return {
        'winRate': d.get('wr'), 'pickRate': d.get('pr'), 'tier': d.get('tier'), 'matches': d.get('matches'),
        'worst': worst, 'synergy': syn, 'best': best,
        'url': f"https://deadlocklabs.gg/heroes/{slug}/",
    }

heroes = []
for slug, name, wiki, dex, rel in ROSTER:
    st = S[slug]
    role, diff, weapon = DEXERTO.get(slug, (None, None, None))
    heroes.append({
        'slug': slug, 'name': name, 'status': 'released', 'release': rel,
        'traits': None, 'role': role, 'difficulty': diff, 'weaponType': weapon,
        'scalingTag': ability_tag(slug),
        'stats': {k: st[k] for k in ['dps','bulletDamage','bulletsPerSec','ammo','lightMelee','heavyMelee','maxHealth','healthRegen','moveSpeed','spiritPower']},
        'spiritScaling': ability_spirit_lines(slug),
        'deadlockLabs': dl_entry(slug),
        'links': {
            'wiki': f"https://deadlock.wiki/{wiki}",
            'deadlockLabs': f"https://deadlocklabs.gg/heroes/{slug}/",
            'dexerto': f"https://www.dexerto.com/wikis/deadlock/heroes/{dex}/" if dex else None,
        },
        'image': f"assets/heroes/{slug}.webp",
    })
for slug, name, wiki, _, _, note in UPCOMING:
    st = S.get(slug)
    heroes.append({
        'slug': slug, 'name': name, 'status': 'upcoming', 'statusNote': note, 'release': None,
        'traits': None, 'role': None, 'difficulty': None, 'weaponType': None,
        'scalingTag': ability_tag(slug) if st else None,
        'stats': {k: st[k] for k in ['dps','bulletDamage','bulletsPerSec','ammo','lightMelee','heavyMelee','maxHealth','healthRegen','moveSpeed','spiritPower']} if st else None,
        'spiritScaling': ability_spirit_lines(slug) if st else [],
        'deadlockLabs': dl_entry(slug),
        'links': {'wiki': f"https://deadlock.wiki/{wiki}", 'deadlockLabs': f"https://deadlocklabs.gg/heroes/{slug}/", 'dexerto': None},
        'image': f"assets/heroes/{slug}.webp" if os.path.exists(os.path.join(HERE,'..','assets','heroes',f'{slug}.webp')) else None,
    })

out = os.path.join(HERE, '..', 'js', 'data.js')
with open(out, 'w', encoding='utf-8') as f:
    f.write('// Generated by data/build_data.py from the sources in data/. Do not edit by hand.\n')
    f.write('window.HERO_DATA = ' + json.dumps({'generated': 'Sources: deadlock.wiki, dexerto.com, deadlocklabs.gg', 'heroes': heroes}, ensure_ascii=False, indent=1) + ';\n')
print('heroes:', len(heroes), 'released:', sum(h['status']=='released' for h in heroes))
for h in heroes:
    dl = h['deadlockLabs'] or {}
    print(f"{h['slug']:14} {h['scalingTag'] or '-':7} role={h['role']} diff={h['difficulty']} wt={h['weaponType']} wr={dl.get('winRate')} worst={[w['name'] for w in dl.get('worst',[])]} syn={[s['name'] for s in dl.get('synergy',[])]} best={[b['name'] for b in dl.get('best',[])][:3]}")
