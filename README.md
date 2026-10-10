# Deadlock Wiki

A fan-made hero database for **Deadlock**, the MOBA from Valve. It puts each hero's scaling, win rates, matchups, and sources on one page, so you can compare heroes without opening five wikis.


**Website:** [github.com/JustGDX/deadlock-wiki](https://github.com/JustGDX/deadlock-wiki)

---

## Purpose

Deadlock has 40+ heroes, and their scaling is spread across wiki pages, patch notes, and stat sites. This project brings the key facts together:

- **Find a hero fast.** Search by name, role, or weapon type, and filter by scaling style.
- **Understand how a hero scales.** Each hero is tagged **Spirit**, **Hybrid**, or **Weapon**, based on how many of its abilities scale with Spirit.
- **See how a hero performs.** Win rate, pick rate, tier, matchups, and best partners come from Deadlock Labs.
- **Check where the information came from.** Every section links to its source, and anything not verified is marked with a dash instead of a guess.

It is a static site. It works offline once the files are on your computer, and it has no accounts, tracking, or external dependencies.

## Features

### Home page
- **Hero cards** with portrait, role, difficulty, scaling tag, and win rate.
- **Search** across hero name, role, weapon type, and scaling tag. Press `/` to focus it and Escape to clear it.
- **Scaling filters:** All, Spirit, Hybrid, and Weapon. Each button shows how many heroes it matches. The stat tiles at the top also act as filters.
- **Sorting:** by name, by win rate (high or low), or by newest release.
- **Upcoming heroes** are listed separately at the end.
- Your search, filter, and sort are remembered while the tab is open.

### Hero profile
- **Header:** portrait, name, Role · Difficulty · Playstyle, scaling tag, release date, and tier.
- **Key numbers:** win rate, pick rate, tier, and match count.
- **Scaling:** Early game (laning), Mid game (power spikes), and Late game (scaling), with a short explanation of the hero's scaling tag.
- **Weapon / Spirit / Melee:** base values, with the increase per boon.
- **Matchups:** Strong against, Weak against, and Best partners, shown as bar charts.
- **Statistics table:** each value with its source.
- **Sources:** a collapsible list of the pages used for this hero.
- **Back button:** returns to the hero list with your previous search and filter kept.

## Getting started

No install or build step is needed. Open `index.html` in a browser, or serve the folder with a static server:

```bash
cd deadlock-wiki
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.

To rebuild the data after editing the source files:

```bash
python3 data/build_data.py
```

## Project structure

```
deadlock-wiki/
├── index.html                    # page shell (header, app container, footer)
├── css/style.css                 # theme and layout
├── js/
│   ├── config.js                 # site name, author, GitHub link, data date
│   ├── data.js                   # generated hero data (do not edit by hand)
│   └── app.js                    # home page, hero profile, routing, search
├── assets/
│   ├── logo.png                  # site logo
│   └── heroes/<slug>.webp        # hero renders (41 of 44 heroes)
└── data/
    ├── build_data.py             # builds js/data.js from the sources below
    ├── spirit_ability_scaling.json  # ability-level Spirit data and tag overrides
    ├── deadlocklabs_raw.json     # scraped Deadlock Labs hero data
    ├── fetch.py / parse.py       # Deadlock Labs scraper and parser
    └── download_renders.py       # downloads hero renders
```

## Configuration

Edit `js/config.js` to change the footer and data date:

```js
window.SITE_CONFIG = {
  siteName: 'Deadlock Wiki',
  githubName: 'JustGDX',
  githubUrl: 'https://github.com/JustGDX',
  dataAccessDate: '2026-10-10'
};
```

## Where the data comes from

| Information | Source |
| --- | --- |
| Win rate, pick rate, tier, matches, matchups, best partners | [Deadlock Labs](https://deadlocklabs.gg) (`data/deadlocklabs_raw.json`) |
| Base stats, boon growth, Spirit Power, release dates, roster | [Deadlock Wiki](https://deadlock.wiki) (Hero Comparison Table, Heroes by release) |
| Role, difficulty, playstyle | [Dexerto Deadlock wiki](https://www.dexerto.com/wikis/deadlock/heroes/) |
| Ability-level Spirit coefficients | Dexerto hero pages (`data/spirit_ability_scaling.json`) |
| Hero renders | Deadlock Labs (`assets/heroes/`) |

Each hero profile links to the pages it used. Data was accessed on **2026-10-10**.

## How the scaling tags work

A hero's tag is based on its **four ability slots**:

| Tag | Rule |
| --- | --- |
| **Spirit** | At least 3 of 4 abilities scale with Spirit damage, healing, or barrier. |
| **Hybrid** | 2 of 4 abilities scale with Spirit. |
| **Weapon** | 0 or 1 of 4 abilities scale with Spirit. |
| **Pending** | No verified ability data yet. |

Only damage, healing, and barrier scaling count. A Spirit coefficient on duration, range, speed, or fire rate does not.

Tags set by hand in `user_overrides` (in `data/spirit_ability_scaling.json`) take priority over the count. The count is kept in the file for reference, so you can see where a manual tag differs from the rule.

Some heroes were read before their full ability list was saved. Those entries are marked **provisional** in the data file.

## Updating the data after a patch

1. Check the latest Deadlock patch notes on [Deadlock Wiki](https://deadlock.wiki) and [Dexerto](https://www.dexerto.com/wikis/deadlock/heroes/).
2. Update the hero's entry in `data/spirit_ability_scaling.json`, or change its entry in `data/build_data.py` if the base stats changed.
3. Run `python3 data/build_data.py`.
4. Reload `index.html` and check the affected hero's profile.
5. Update the data access date in `js/config.js` and in this README.

## Known limitations

- **Snapshot data.** Numbers reflect the sources as of 2026-10-10. The base-stat table on Deadlock Wiki can lag behind the latest patch, so check the linked source before relying on a specific number.
- **Some values differ between sources.** For example, Dexerto's Grey Talon page lists Guided Owl's Spirit Power per kill as 8, but the January 30, 2026 patch changed it to 10. The site follows the source it cites for each value.
- **Pending information.** Shown as "—" or "Pending" when no verified source provides it. Rat King and Solomon have no verified ability-level data yet.
- **Traits are not shown** because they have not been verified against a source.
- **Upcoming heroes** (Deadman Danny, Nurse Harrow, and Violet) have unreleased stats, which may change.
- **Early / Mid / Late game** labels are the same for every hero. Ability-specific detail is on the linked Deadlock Wiki page.

## Contributing

Ideas and corrections are welcome. For a data correction, please include the source link. Nothing is added without a source, so a claim with no link will not be accepted.

## Disclaimer

This is a fan project. It is not affiliated with, endorsed by, or sponsored by Valve Corporation. Deadlock is a trademark of Valve. All hero names and game content belong to their respective owners.

----------------
**Author:** GDX
