(function () {
  'use strict';

  var DATA = window.HERO_DATA || { heroes: [] };
  var CFG = window.SITE_CONFIG || {};
  var HEROES = DATA.heroes;
  var BY_SLUG = {};
  HEROES.forEach(function (h) { BY_SLUG[h.slug] = h; });
  var app = document.getElementById('app');
  var STATE_KEY = 'deadlock-wiki-home-state';
  var FILTERS = ['All', 'Weapon', 'Hybrid', 'Spirit'];

  var SRC = {
    table: { url: 'https://deadlock.wiki/Hero_Comparison_Table', label: 'Deadlock Wiki – Hero Comparison Table' },
    release: { url: 'https://deadlock.wiki/Heroes_by_release', label: 'Deadlock Wiki – Heroes by release' },
    roster: { url: 'https://deadlock.wiki/Heroes', label: 'Deadlock Wiki – Heroes' },
    dexerto: { url: 'https://www.dexerto.com/wikis/deadlock/heroes/', label: 'Dexerto – Heroes' },
    labs: { url: 'https://deadlocklabs.gg', label: 'Deadlock Labs' }
  };

  var TAG_TEXT = {
    Spirit: 'Most abilities (3 or more of 4) scale with Spirit damage, healing or barrier.',
    Hybrid: 'Two of four abilities scale with Spirit, so weapon and Spirit both matter.',
    Weapon: 'Few or no abilities scale with Spirit; gun damage carries most of the kit.'
  };

  var ICON = {
    search: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/></svg>',
    back: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>',
    sword: '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M14.5 3.5l6 6M3.5 20.5l6-6M5 19l-1.5 1.5M20 4l-9 9M16 8l-3-3"/></svg>',
    shield: '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z"/></svg>',
    people: '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M3 19c0-3 2.7-5 6-5s6 2 6 5M15 15c3 0 6 1.6 6 4"/></svg>'
  };

  /* ---------- helpers ---------- */
  function esc(s) {
    return String(s === null || s === undefined ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function link(url, label) {
    return '<a href="' + esc(url) + '" target="_blank" rel="noopener">' + esc(label) + '</a>';
  }
  function srcLine(items) {
    return '<p class="src">Source: ' + items.join(' · ') + '</p>';
  }
  var DASH = '<span class="muted">—</span>';
  function val(v, suffix) {
    return (v === null || v === undefined || v === '') ? DASH : esc(v) + (suffix || '');
  }
  function isUpcoming(h) { return !!h && h.status !== 'released'; }
  function hasWR(h) { return h.deadlockLabs && typeof h.deadlockLabs.winRate === 'number'; }
  function initials(name) {
    return name.split(/\s+/).map(function (w) { return w[0]; }).join('').slice(0, 2).toUpperCase();
  }
  function portraitHTML(h) {
    if (h.image) {
      return '<img src="' + esc(h.image) + '" alt="' + esc(h.name) + '" loading="lazy" data-fallback="' + esc(h.name) + '">';
    }
    return '<div class="ph">' + esc(initials(h.name)) + '</div>';
  }
  function bindFallbacks(root) {
    root.querySelectorAll('img[data-fallback]').forEach(function (img) {
      var fail = function () {
        var wrap = document.createElement('div');
        wrap.className = 'ph';
        wrap.textContent = initials(img.getAttribute('data-fallback'));
        img.replaceWith(wrap);
      };
      img.addEventListener('error', fail);
      if (img.complete && img.naturalWidth === 0) fail();
    });
  }
  function tagLabel(h) {
    if (['Spirit', 'Hybrid', 'Weapon'].indexOf(h.scalingTag) >= 0) return h.scalingTag;
    return isUpcoming(h) ? 'Upcoming' : 'Not tagged';
  }
  function tagPill(h) {
    if (['Spirit', 'Hybrid', 'Weapon'].indexOf(h.scalingTag) < 0) return '<span class="pill pill-empty">' + esc(tagLabel(h)) + '</span>';
    return '<span class="pill ' + esc(h.scalingTag) + '">' + esc(h.scalingTag) + '</span>';
  }
  function tagColorKey(h) {
    return ['Spirit', 'Hybrid', 'Weapon'].indexOf(h.scalingTag) >= 0 ? h.scalingTag : 'Pending';
  }
  function bar(pct, cls, extra) {
    var w = Math.max(0, Math.min(100, pct));
    return '<div class="bar' + (extra ? ' ' + extra : '') + '"><i class="' + (cls || '') + '" style="width:' + w.toFixed(1) + '%"></i></div>';
  }
  function heroLinks(h) {
    var items = [];
    if (h.links.wiki) items.push(link(h.links.wiki, h.name + ' – Deadlock Wiki'));
    if (h.links.dexerto) items.push(link(h.links.dexerto, h.name + ' – Dexerto'));
    if (h.links.deadlockLabs) items.push(link(h.links.deadlockLabs, h.name + ' – Deadlock Labs'));
    return items;
  }
  function plural(n, word) {
    var forms = { hero: 'heroes' };
    return n + ' ' + (n === 1 ? word : (forms[word] || word + 's'));
  }

  /* ---------- state ---------- */
  function loadState() {
    try { return JSON.parse(sessionStorage.getItem(STATE_KEY)) || {}; } catch (e) { return {}; }
  }
  function saveState(s) {
    try { sessionStorage.setItem(STATE_KEY, JSON.stringify(s)); } catch (e) {}
  }

  /* ---------- homepage ---------- */
  function sortHeroes(list, mode) {
    var cmpName = function (a, b) { return a.name.localeCompare(b.name); };
    return list.slice().sort(function (a, b) {
      var ua = isUpcoming(a), ub = isUpcoming(b);
      if (ua !== ub) return ua ? 1 : -1;
      if (mode === 'wr-desc' || mode === 'wr-asc') {
        var wa = hasWR(a), wb = hasWR(b);
        if (wa !== wb) return wa ? -1 : 1;
        if (wa && wb && a.deadlockLabs.winRate !== b.deadlockLabs.winRate) {
          return mode === 'wr-desc'
            ? b.deadlockLabs.winRate - a.deadlockLabs.winRate
            : a.deadlockLabs.winRate - b.deadlockLabs.winRate;
        }
      }
      if (mode === 'newest') {
        var ra = a.release || '', rb = b.release || '';
        if (ra !== rb) return ra < rb ? 1 : -1;
      }
      return cmpName(a, b);
    });
  }

  function renderHome() {
    var st = Object.assign({ q: '', f: 'All', s: 'name' }, loadState());
    var released = HEROES.filter(function (h) { return !isUpcoming(h); });
    var counts = { All: released.length, Weapon: 0, Hybrid: 0, Spirit: 0 };
    released.forEach(function (h) { if (counts[h.scalingTag] !== undefined) counts[h.scalingTag]++; });
    var upcoming = HEROES.length - released.length;

    app.innerHTML =
      '<section class="banner">' +
        '<p class="eyebrow">Deadlock · Hero database</p>' +
        '<h1>Heroes</h1>' +
        '<p class="lede">' + released.length + ' released heroes' + (upcoming ? ' and ' + upcoming + ' upcoming' : '') +
        '. Scaling tags come from each hero\u2019s abilities. Stats from Deadlock Wiki, Dexerto and Deadlock Labs.</p>' +
        '<div class="stat-tiles">' +
          '<button class="tile" data-f="All" type="button"><div class="n">' + counts.All + '</div><div class="l">All released</div></button>' +
          '<button class="tile spirit" data-f="Spirit" type="button"><div class="n">' + counts.Spirit + '</div><div class="l">Spirit scaling</div></button>' +
          '<button class="tile hybrid" data-f="Hybrid" type="button"><div class="n">' + counts.Hybrid + '</div><div class="l">Hybrid scaling</div></button>' +
          '<button class="tile weapon" data-f="Weapon" type="button"><div class="n">' + counts.Weapon + '</div><div class="l">Weapon scaling</div></button>' +
        '</div>' +
      '</section>' +
      '<div class="toolbar">' +
        '<label class="search">' + ICON.search +
          '<input id="q" type="search" placeholder="Search heroes, roles or weapons" aria-label="Search heroes" autocomplete="off" value="' + esc(st.q) + '">' +
          '<button class="clear" id="clear" type="button" aria-label="Clear search" hidden>×</button>' +
          '<span class="kbd" aria-hidden="true">/</span>' +
        '</label>' +
        '<div class="seg" role="group" aria-label="Scaling filter">' +
          FILTERS.map(function (f) {
            return '<button type="button" data-f="' + f + '" aria-pressed="' + (st.f === f) + '">' + f +
              ' <span class="c">' + counts[f] + '</span></button>';
          }).join('') +
        '</div>' +
        '<select class="select" id="sort" aria-label="Sort heroes">' +
          [['name', 'Name A–Z'], ['wr-desc', 'Win rate (high to low)'], ['wr-asc', 'Win rate (low to high)'], ['newest', 'Newest release']].map(function (o) {
            return '<option value="' + o[0] + '"' + (st.s === o[0] ? ' selected' : '') + '>' + o[1] + '</option>';
          }).join('') +
        '</select>' +
      '</div>' +
      '<p class="count" id="count"></p>' +
      '<div class="grid" id="grid"></div>' +
      srcLine([link(SRC.roster.url, SRC.roster.label), link(SRC.dexerto.url, SRC.dexerto.label), link(SRC.labs.url, SRC.labs.label)]);

    var q = document.getElementById('q');
    var grid = document.getElementById('grid');
    var count = document.getElementById('count');
    var clear = document.getElementById('clear');
    var sort = document.getElementById('sort');

    function syncChips() {
      document.querySelectorAll('.seg button').forEach(function (b) {
        b.setAttribute('aria-pressed', String(b.getAttribute('data-f') === st.f));
      });
      document.querySelectorAll('.tile[data-f]').forEach(function (b) {
        b.setAttribute('aria-pressed', String(b.getAttribute('data-f') === st.f));
      });
    }

    function update() {
      var term = q.value.trim().toLowerCase();
      clear.hidden = !q.value;
      var list = HEROES.filter(function (h) {
        if (term) {
          var hay = [h.name, h.role || '', h.weaponType || '', h.scalingTag || ''].join(' ').toLowerCase();
          if (hay.indexOf(term) === -1) return false;
        }
        if (st.f !== 'All' && h.scalingTag !== st.f) return false;
        return true;
      });
      list = sortHeroes(list, st.s);

      count.textContent = plural(list.length, 'hero') + ' shown' + (st.f !== 'All' ? ' · ' + st.f + ' scaling' : '');

      saveState({ q: q.value, f: st.f, s: st.s });

      if (!list.length) {
        grid.innerHTML = '<div class="empty">No heroes match this search and filter. Try clearing the search or choosing All.</div>';
        return;
      }

      var html = '';
      var shownUpcomingHeader = false;
      list.forEach(function (h, i) {
        if (isUpcoming(h) && !shownUpcomingHeader) {
          html += '<div class="section-divider">Upcoming</div>';
          shownUpcomingHeader = true;
        }
        var wr = hasWR(h) ? h.deadlockLabs.winRate : null;
        html += '<a class="hero-card" data-tag="' + tagColorKey(h) + '" style="--tagc:var(--' + (tagColorKey(h) === 'Pending' ? 'pending' : tagColorKey(h).toLowerCase()) + ');animation-delay:' + Math.min(i * 18, 320) + 'ms" href="#/hero/' + esc(h.slug) + '">' +
          '<div class="portrait">' + portraitHTML(h) +
            '<span class="tag-on">' + tagPill(h) + '</span>' +
          '</div>' +
          '<div class="hc-body">' +
            '<div class="hc-name">' + esc(h.name) + (isUpcoming(h) ? ' <span class="badge upcoming">Upcoming</span>' : '') + '</div>' +
            '<div class="hc-sub">' + val(h.role) + ' · ' + val(h.difficulty) + '</div>' +
            '<div class="hc-wr">' +
              (wr === null ? '<span class="muted">' + (isUpcoming(h) ? 'Not released' : 'No win rate listed') + '</span>' :
                bar(wr, '', 'mid') + '<span>' + wr.toFixed(1) + '%</span>') +
            '</div>' +
          '</div></a>';
      });
      grid.innerHTML = html;
      bindFallbacks(grid);
    }

    q.addEventListener('input', update);
    clear.addEventListener('click', function () { q.value = ''; update(); q.focus(); });
    sort.addEventListener('change', function () { st.s = sort.value; update(); });
    document.querySelectorAll('.seg button, .tile[data-f]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        st.f = btn.getAttribute('data-f');
        syncChips();
        update();
      });
    });
    syncChips();
    update();
  }

  /* ---------- hero profile ---------- */
  function statBoon(v, unit) {
    if (v === null || v === undefined) return DASH;
    if (Array.isArray(v)) {
      return esc(v[0]) + (unit || '') + ' <small>(+' + esc(v[1]) + ' per boon)</small>';
    }
    return esc(v) + (unit || '');
  }

  function linkOrName(e) {
    var target = BY_SLUG[e.slug];
    var name = esc(e.name);
    var label = target ? '<a href="#/hero/' + esc(target.slug) + '">' + name + '</a>' : name;
    var badge = target && isUpcoming(target) ? ' <span class="badge upcoming">Upcoming</span>' : '';
    return label + badge;
  }

  function deltaHTML(d) {
    var cls = d >= 0 ? 'delta-up' : 'delta-down';
    return '<span class="' + cls + '">' + (d >= 0 ? '+' : '') + esc(d) + '</span>';
  }

  // Strong against: enemies with the best win rate for this hero (bar = win rate)
  function strongRows(list) {
    if (!list || !list.length) return '<li class="row"><span class="muted">No entries listed on Deadlock Labs</span></li>';
    return list.map(function (e) {
      return '<li class="row wide"><span class="name">' + linkOrName(e) + '</span>' +
        bar(e.wr, e.delta >= 0 ? 'good' : 'bad', 'mid') +
        '<span class="val">' + esc(e.wr) + '% <small>· ' + deltaHTML(e.delta) + '</small></span></li>';
    }).join('');
  }

  // Weak against / Best partners: bar length = size of the change (Deadlock Labs delta)
  function deltaRows(list) {
    if (!list || !list.length) return '<li class="row"><span class="muted">No entries listed on Deadlock Labs</span></li>';
    var max = list.reduce(function (m, e) { return Math.max(m, Math.abs(e.delta || 0)); }, 0) || 1;
    return list.map(function (e) {
      var pct = Math.abs(e.delta || 0) / max * 100;
      return '<li class="row wide"><span class="name">' + linkOrName(e) + '</span>' +
        bar(pct, e.delta >= 0 ? 'good' : 'bad') +
        '<span class="val">' + deltaHTML(e.delta) + '</span></li>';
    }).join('');
  }

  function kpi(label, value, suffix, barPct) {
    var v = (value === null || value === undefined) ? DASH : esc(value) + (suffix ? '<small>' + suffix + '</small>' : '');
    return '<div class="kpi"><div class="k">' + label + '</div><div class="v">' + v + '</div>' +
      (barPct !== undefined && barPct !== null ? bar(barPct, '', 'mid') : '') + '</div>';
  }

  function renderProfile(slug) {
    var h = BY_SLUG[slug];
    var back = '<a class="back" href="#/">' + ICON.back + ' Back to heroes</a>';
    if (!h) {
      app.innerHTML = back + '<div class="empty">Hero not found.</div>';
      return;
    }
    var dl = h.deadlockLabs || {};
    var st = h.stats;
    var upcoming = isUpcoming(h);
    var tagKey = tagColorKey(h);

    var notice = upcoming
      ? '<div class="p-notice">' + esc(h.statusNote || 'Unreleased hero.') +
        ' Deadlock Wiki notes that stats for unreleased heroes may change.</div>'
      : '';

    var weaponRows = st ? [
      ['DPS', statBoon(st.dps)],
      ['Bullet damage', statBoon(st.bulletDamage)],
      ['Bullets per sec', statBoon(st.bulletsPerSec)],
      ['Ammo', statBoon(st.ammo)]
    ] : null;
    var meleeRows = st ? [
      ['Light melee', statBoon(st.lightMelee)],
      ['Heavy melee', statBoon(st.heavyMelee)]
    ] : null;

    function kvList(rows) {
      if (!rows) return '<li class="row">' + DASH + '</li>';
      return rows.map(function (r) {
        return '<li class="row"><span>' + r[0] + '</span><span class="val">' + r[1] + '</span></li>';
      }).join('');
    }

    var spiritList = (h.spiritScaling && h.spiritScaling.length)
      ? h.spiritScaling.map(function (s) { return '<li class="row"><span>' + esc(s) + '</span></li>'; }).join('')
      : '<li class="row"><span class="muted">No ability-level Spirit scaling listed</span></li>';

    var statRows = [];
    if (st) {
      statRows.push(['Max health', statBoon(st.maxHealth)]);
      statRows.push(['Health regen', statBoon(st.healthRegen)]);
      statRows.push(['Move speed (m/s)', statBoon(st.moveSpeed)]);
      statRows.push(['DPS', statBoon(st.dps)]);
      statRows.push(['Bullet damage', statBoon(st.bulletDamage)]);
      statRows.push(['Bullets per sec', statBoon(st.bulletsPerSec)]);
      statRows.push(['Ammo', statBoon(st.ammo)]);
      statRows.push(['Light melee', statBoon(st.lightMelee)]);
      statRows.push(['Heavy melee', statBoon(st.heavyMelee)]);
      statRows.push(['Spirit Power', statBoon(st.spiritPower)]);
    }
    var wikiTableLink = link(SRC.table.url, 'Hero Comparison Table');
    var dexLink = h.links.dexerto ? link(h.links.dexerto, 'Dexerto') : link(SRC.dexerto.url, 'Dexerto');
    var labsLink = link(h.links.deadlockLabs, 'Deadlock Labs');
    var releaseLink = link(SRC.release.url, 'Heroes by release');

    var table = '<table><thead><tr><th>Statistic</th><th>Value</th><th>Source</th></tr></thead><tbody>' +
      '<tr><td>Release date</td><td>' + val(h.release) + '</td><td>' + releaseLink + '</td></tr>' +
      '<tr><td>Role</td><td>' + val(h.role) + '</td><td>' + dexLink + '</td></tr>' +
      '<tr><td>Difficulty</td><td>' + val(h.difficulty) + '</td><td>' + dexLink + '</td></tr>' +
      '<tr><td>Playstyle (weapon type)</td><td>' + val(h.weaponType) + '</td><td>' + dexLink + '</td></tr>' +
      '<tr><td>Win rate</td><td>' + val(dl.winRate, '%') + '</td><td>' + labsLink + '</td></tr>' +
      '<tr><td>Pick rate</td><td>' + val(dl.pickRate, '%') + '</td><td>' + labsLink + '</td></tr>' +
      '<tr><td>Tier</td><td>' + val(dl.tier) + '</td><td>' + labsLink + '</td></tr>' +
      '<tr><td>Matches</td><td>' + val(dl.matches) + '</td><td>' + labsLink + '</td></tr>' +
      statRows.map(function (r) {
        return '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td><td>' + wikiTableLink + '</td></tr>';
      }).join('') +
      '</tbody></table>';

    var sources = [
      h.links.wiki ? '<li>' + link(h.links.wiki, h.name + ' – Deadlock Wiki page') + ' (hero page)</li>' : '',
      '<li>' + link(SRC.table.url, SRC.table.label) + ' (base stats, boon and Spirit scaling)</li>',
      '<li>' + link(SRC.release.url, SRC.release.label) + ' (release dates, voting status)</li>',
      '<li>' + (h.links.dexerto ? link(h.links.dexerto, h.name + ' – Dexerto') : link(SRC.dexerto.url, SRC.dexerto.label) + ' (no entry for this hero)') + ' (role, difficulty, playstyle)</li>',
      '<li>' + link(h.links.deadlockLabs, h.name + ' – Deadlock Labs') + ' (win rate, pick rate, matchups, synergies; accessed ' + esc(CFG.dataAccessDate || 'n/a') + ')</li>'
    ].join('');

    var backdrop = h.image
      ? '<div class="p-backdrop" style="background-image:url(\'' + esc(h.image) + '\')" aria-hidden="true"></div>'
      : '<div class="p-backdrop none" aria-hidden="true"></div>';

    var subParts = [val(h.role), val(h.difficulty), val(h.weaponType)];
    var subHTML = subParts.join('<span class="dot"></span>');

    app.innerHTML =
      back +
      '<article class="profile" data-tag="' + tagKey + '">' +
        '<header class="p-hero">' + backdrop +
          '<div class="p-portrait">' + portraitHTML(h) + '</div>' +
          '<div class="p-title">' +
            '<p class="eyebrow">Hero profile</p>' +
            '<h1>' + esc(h.name) + (upcoming ? ' <span class="badge upcoming">Upcoming</span>' : '') + '</h1>' +
            '<p class="p-sub">' + subHTML + '</p>' +
            '<div class="p-tags">' + tagPill(h) +
              (h.release ? '<span class="chip-plain">Released ' + esc(h.release) + '</span>' : '') +
              (dl.tier ? '<span class="chip-plain">Tier ' + esc(dl.tier) + '</span>' : '') +
            '</div>' +
          '</div>' +
        '</header>' +
        notice +

        '<div class="kpis">' +
          kpi('Win rate', dl.winRate, '%', typeof dl.winRate === 'number' ? dl.winRate : null) +
          kpi('Pick rate', dl.pickRate, '%', typeof dl.pickRate === 'number' ? Math.min(dl.pickRate, 100) : null) +
          kpi('Tier', dl.tier) +
          kpi('Matches', dl.matches) +
        '</div>' +

        '<div class="body">' +
          '<section class="section">' +
            '<h2>Scaling</h2>' +
            '<p class="lede">Scaling tag: <strong>' + esc(tagLabel(h)) + '</strong>. ' +
              esc(TAG_TEXT[h.scalingTag] || (upcoming ? 'This hero is not released yet, so its ability data may still change.' : 'No ability-level scaling data is listed for this hero.')) + '</p>' +
            '<div class="phases">' +
              '<div class="phase"><span class="step">1</span><div class="k">Early game</div><div class="v">Laning</div></div>' +
              '<div class="phase"><span class="step">2</span><div class="k">Mid game</div><div class="v">Power spikes</div></div>' +
              '<div class="phase"><span class="step">3</span><div class="k">Late game</div><div class="v">Scaling</div></div>' +
            '</div>' +
            srcLine([link(h.links.wiki, h.name + ' – Deadlock Wiki page'), wikiTableLink]) +
          '</section>' +

          '<section class="section">' +
            '<h2>Weapon / Spirit / Melee scaling</h2>' +
            '<p class="lede">Base value, with the increase per boon in brackets.</p>' +
            '<div class="scale-grid">' +
              '<div class="box"><h3>Weapon</h3><ul>' + kvList(weaponRows) + '</ul></div>' +
              '<div class="box"><h3>Spirit</h3><ul>' + spiritList + '</ul></div>' +
              '<div class="box"><h3>Melee</h3><ul>' + kvList(meleeRows) + '</ul></div>' +
            '</div>' +
            srcLine([wikiTableLink, link(SRC.dexerto.url, 'Dexerto (ability coefficients)')]) +
          '</section>' +

          '<section class="section">' +
            '<h2>Matchups</h2>' +
            '<p class="lede">Win rates and changes as reported by Deadlock Labs.</p>' +
            '<div class="matchups">' +
              '<div class="box"><h3>' + ICON.sword + ' Strong against</h3>' +
                '<p class="hint">Heroes this hero beats most often</p>' +
                '<ul>' + strongRows((dl.best || []).slice(0, 3)) + '</ul></div>' +
              '<div class="box"><h3>' + ICON.shield + ' Weak against</h3>' +
                '<p class="hint">Heroes that tend to beat this hero</p>' +
                '<ul>' + deltaRows(dl.worst || []) + '</ul></div>' +
              '<div class="box full"><h3>' + ICON.people + ' Best partners</h3>' +
                '<p class="hint">Heroes that win more often when paired with this hero</p>' +
                '<ul>' + deltaRows(dl.synergy || []) + '</ul></div>' +
            '</div>' +
            srcLine([link(h.links.deadlockLabs, h.name + ' – Deadlock Labs (matchups and synergies)')]) +
          '</section>' +

          '<section class="section">' +
            '<h2>Statistics</h2>' +
            table +
          '</section>' +

          '<section class="section">' +
            '<details class="sources" open>' +
              '<summary>Sources and verification</summary>' +
              '<ul class="src-list">' + sources + '</ul>' +
              '<p class="src">A dash (—) means the sources above do not list that value.</p>' +
            '</details>' +
          '</section>' +
        '</div>' +
      '</article>';

    bindFallbacks(app);
    window.scrollTo(0, 0);
  }

  /* ---------- router ---------- */
  function route() {
    var hash = location.hash || '#/';
    markNav(hash);
    // Itemization (#/itemization and #/itemization/<slug>) is handled by js/itemization.js
    if (window.Itemization && window.Itemization.handles(hash)) {
      window.Itemization.render(app, hash);
      return;
    }
    document.title = BASE_TITLE;
    var m = hash.match(/^#\/hero\/([a-z0-9-]+)$/i);
    if (m) renderProfile(m[1].toLowerCase());
    else renderHome();
  }

  /* top navigation: mark the current section */
  var BASE_TITLE = document.title;
  function markNav(hash) {
    var section = window.Itemization && window.Itemization.handles(hash) ? 'items' : 'heroes';
    document.querySelectorAll('[data-nav]').forEach(function (a) {
      if (a.getAttribute('data-nav') === section) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
  }
  window.addEventListener('hashchange', route);

  /* keyboard: "/" focuses search on the home page, Escape clears it */
  document.addEventListener('keydown', function (e) {
    var active = document.activeElement;
    var typing = active && (active.tagName === 'INPUT' || active.tagName === 'SELECT' || active.tagName === 'TEXTAREA');
    var q = document.getElementById('q');
    if (e.key === '/' && !typing && q) {
      e.preventDefault();
      q.focus();
      q.select();
    } else if (e.key === 'Escape' && active === q && q.value) {
      q.value = '';
      q.dispatchEvent(new Event('input'));
    }
  });

  /* ---------- footer config ---------- */
  var gh = document.getElementById('gh-link');
  var ghName = document.getElementById('gh-name');
  var ghWarn = document.getElementById('gh-warning');
  if (gh) gh.href = CFG.githubUrl || '#';
  if (ghName) ghName.textContent = CFG.githubName || 'Your Name';
  if (ghWarn) ghWarn.hidden = (CFG.githubName || '').indexOf('PLACEHOLDER') === -1;

  route();
})();
