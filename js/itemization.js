/* Itemization: data loading, the item browser, and shared helpers.
   Vanilla JavaScript, no dependencies. Route: #/itemization and #/itemization/<slug>.
   The detail view lives in js/item-details.js and is loaded after this file. */
(function () {
  'use strict';

  var STATE_KEY = 'deadlock-wiki-items-state';   // filters survive a trip to an item page
  var RETURN_KEY = 'deadlock-wiki-items-return'; // scroll position to restore when coming back
  var SLUG_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  var CATS = ['All', 'Weapon', 'Vitality', 'Spirit'];
  var CAT_ORDER = ['Weapon', 'Vitality', 'Spirit'];
  var TIERS = [1, 2, 3, 4, 5];
  var SORTS = [
    { id: 'default', label: 'Game order' },
    { id: 'name', label: 'Name (A–Z)' },
    { id: 'price-asc', label: 'Price: low to high' },
    { id: 'price-desc', label: 'Price: high to low' },
    { id: 'category', label: 'Category' },
    { id: 'tier', label: 'Tier' }
  ];
  var GROUP_LABEL = { offensive: 'Offensive counters', defensive: 'Defensive counters', utility: 'Utility' };
  var DEFAULTS = { q: '', cat: 'All', tier: 0, purpose: '', sort: 'default' };
  var BASE_TITLE = document.title;

  var DB = null;
  var IDX = { bySlug: {}, pos: {}, hay: {}, tagById: {} };
  var loadPromise = null;
  var renderToken = 0;
  var globalKeysBound = false;

  /* ---------- safe DOM helpers (no innerHTML with data) ---------- */
  function append(el, kid) {
    if (kid === null || kid === undefined || kid === false) return;
    if (Array.isArray(kid)) { kid.forEach(function (k) { append(el, k); }); return; }
    if (kid.nodeType) el.appendChild(kid);
    else el.appendChild(document.createTextNode(String(kid)));
  }
  function h(tag, attrs) {
    var el = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) {
        var v = attrs[k];
        if (v === null || v === undefined || v === false) return;
        if (k === 'class') el.className = v;
        else if (k === 'text') el.textContent = String(v);
        else if (k.indexOf('on') === 0 && typeof v === 'function') el.addEventListener(k.slice(2), v);
        else el.setAttribute(k, v === true ? '' : String(v));
      });
    }
    for (var i = 2; i < arguments.length; i++) append(el, arguments[i]);
    return el;
  }
  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }

  /* ---------- data ---------- */
  function validate(db) {
    if (!db || !Array.isArray(db.items) || db.items.length === 0) throw new Error('Item data is empty or malformed.');
    var slugs = {}, ids = {};
    db.items.forEach(function (it, i) {
      if (!it || typeof it.slug !== 'string' || !SLUG_RE.test(it.slug)) throw new Error('Invalid item slug at index ' + i);
      if (slugs[it.slug]) throw new Error('Duplicate item slug: ' + it.slug);
      if (ids[it.id]) throw new Error('Duplicate item id: ' + it.id);
      slugs[it.slug] = true; ids[it.id] = true;
    });
  }
  function index(db) {
    IDX = { bySlug: {}, pos: {}, hay: {}, tagById: {} };
    (db.tagDefinitions || []).forEach(function (t) { IDX.tagById[t.id] = t; });
    db.items.forEach(function (it, i) {
      IDX.bySlug[it.slug] = it;
      IDX.pos[it.slug] = i;
      var parts = [it.name, it.category, it.type, 'tier ' + it.tier, 't' + it.tier, String(it.cost)];
      (it.description || []).forEach(function (d) { parts.push(d.text); });
      (it.stats || []).forEach(function (s) { parts.push(s.label, s.value); });
      (it.tags || []).forEach(function (t) { parts.push(t.label, t.id.replace(/-/g, ' ')); });
      IDX.hay[it.slug] = parts.join(' | ').toLowerCase();
    });
  }
  function loadEmbedded() {
    return new Promise(function (resolve, reject) {
      if (window.ITEM_DATA) return resolve(window.ITEM_DATA);
      var s = document.createElement('script');
      s.src = 'js/items-data.js';
      s.onload = function () {
        if (window.ITEM_DATA) resolve(window.ITEM_DATA);
        else reject(new Error('js/items-data.js did not define ITEM_DATA'));
      };
      s.onerror = function () { reject(new Error('could not load js/items-data.js')); };
      document.head.appendChild(s);
    });
  }
  /* Loads items.json once per session. Falls back to the embedded copy for file:// use. */
  function loadDb() {
    if (!loadPromise) {
      loadPromise = Promise.resolve().then(function () {
        if (typeof fetch !== 'function') throw new Error('fetch is not available');
        return fetch('data/items.json', { cache: 'no-cache' }).then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status + ' while loading data/items.json');
          return r.json();
        });
      }).catch(function (err) {
        // Opened from file://, where fetch is blocked: use the embedded copy, loaded on demand.
        return loadEmbedded().catch(function () { throw err; });
      }).then(function (db) {
        validate(db);
        DB = db;
        index(db);
        return db;
      }).catch(function (err) {
        loadPromise = null; // allow a retry on the next navigation
        throw err;
      });
    }
    return loadPromise;
  }

  /* ---------- routing ---------- */
  function parse(hash) {
    var m = /^#\/?itemization(?:\/(.*))?$/i.exec(hash || '');
    if (!m) return null;
    var rest = (m[1] || '').replace(/\/+$/, '');
    if (!rest) return { view: 'browser' };
    return { view: 'detail', slug: rest.toLowerCase() };
  }

  /* ---------- helpers shared with item-details.js ---------- */
  function fmtCost(n) { return typeof n === 'number' ? n.toLocaleString('en-US') : String(n); }
  function initials(name) {
    return String(name).split(/\s+/).map(function (w) { return w.charAt(0); }).join('').slice(0, 2).toUpperCase();
  }
  function catClass(cat) { return 'cat-' + String(cat || '').toLowerCase(); }
  function hasTag(it, id) { return (it.tags || []).some(function (t) { return t.id === id; }); }
  function iconEl(it, cls) {
    var img = h('img', { class: cls, src: it.icon, alt: '', loading: 'lazy', decoding: 'async' });
    img.addEventListener('error', function () {
      var ph = h('div', { class: cls + ' ph', 'aria-hidden': 'true' }, initials(it.name));
      if (img.parentNode) img.parentNode.replaceChild(ph, img);
    });
    return img;
  }
  function summaryOf(it, max) {
    max = max || 130;
    var first = (it.description || [])[0];
    var text = first ? first.text : '';
    if (!text) {
      var s = (it.stats || []).slice(0, 2).map(function (x) { return x.label + ' ' + x.value; }).join(', ');
      return s ? 'No description on source. Stats: ' + s : 'No description on source.';
    }
    if (text.length <= max) return text;
    var cut = text.slice(0, max);
    return cut.slice(0, cut.lastIndexOf(' ')) + '…';
  }

  var util = {
    h: h, clear: clear, append: append, iconEl: iconEl, fmtCost: fmtCost, initials: initials,
    catClass: catClass, hasTag: hasTag, summaryOf: summaryOf, GROUP_LABEL: GROUP_LABEL,
    CAT_ORDER: CAT_ORDER, TIERS: TIERS,
    db: function () { return DB; },
    index: function () { return IDX; }
  };

  /* ---------- browser state ---------- */
  function sanitize(s) {
    var out = {};
    Object.keys(DEFAULTS).forEach(function (k) { out[k] = DEFAULTS[k]; });
    if (!s || typeof s !== 'object') return out;
    if (typeof s.q === 'string') out.q = s.q.slice(0, 80);
    if (CATS.indexOf(s.cat) !== -1) out.cat = s.cat;
    if (TIERS.indexOf(Number(s.tier)) !== -1) out.tier = Number(s.tier);
    if (typeof s.purpose === 'string' && (!s.purpose || IDX.tagById[s.purpose])) out.purpose = s.purpose;
    if (SORTS.some(function (x) { return x.id === s.sort; })) out.sort = s.sort;
    return out;
  }
  function getState() {
    try { return sanitize(JSON.parse(sessionStorage.getItem(STATE_KEY) || 'null')); }
    catch (e) { return sanitize(null); }
  }
  function saveState(st) {
    try { sessionStorage.setItem(STATE_KEY, JSON.stringify(st)); } catch (e) { /* storage disabled */ }
  }
  function isDirty(st) {
    return st.q !== '' || st.cat !== 'All' || st.tier !== 0 || st.purpose !== '' || st.sort !== 'default';
  }
  function tokens(q) { return (q || '').toLowerCase().trim().split(/\s+/).filter(Boolean); }

  /* skip: which facet is being counted ('cat' | 'tier' | 'purpose'), so counts show what each choice would give */
  function matchItem(it, st, skip) {
    if (skip !== 'cat' && st.cat !== 'All' && it.category !== st.cat) return false;
    if (skip !== 'tier' && st.tier && it.tier !== st.tier) return false;
    if (skip !== 'purpose' && st.purpose && !hasTag(it, st.purpose)) return false;
    var hay = IDX.hay[it.slug];
    var toks = tokens(st.q);
    for (var i = 0; i < toks.length; i++) if (hay.indexOf(toks[i]) === -1) return false;
    return true;
  }
  function sortList(list, sort) {
    var arr = list.slice();
    var byName = function (a, b) { return a.name.localeCompare(b.name); };
    switch (sort) {
      case 'name': arr.sort(byName); break;
      case 'price-asc': arr.sort(function (a, b) { return a.cost - b.cost || byName(a, b); }); break;
      case 'price-desc': arr.sort(function (a, b) { return b.cost - a.cost || byName(a, b); }); break;
      case 'category': arr.sort(function (a, b) {
        return CAT_ORDER.indexOf(a.category) - CAT_ORDER.indexOf(b.category) || a.tier - b.tier || byName(a, b);
      }); break;
      case 'tier': arr.sort(function (a, b) { return a.tier - b.tier || byName(a, b); }); break;
      default: arr.sort(function (a, b) { return IDX.pos[a.slug] - IDX.pos[b.slug]; });
    }
    return arr;
  }

  /* ---------- browser view ---------- */
  function renderBrowser(app) {
    var st = getState();
    var refs = { cat: [], tier: [], tagOpts: [] };
    var total = DB.items.length;
    clear(app);

    var search = h('input', {
      id: 'iq', type: 'search', placeholder: 'Search names, effects, stats, or tags…',
      'aria-label': 'Search items', autocomplete: 'off', value: st.q
    });
    search.addEventListener('input', function () { st.q = search.value; update(); });
    refs.clearSearch = h('button', {
      type: 'button', class: 'clear', 'aria-label': 'Clear search', hidden: true,
      onclick: function () { st.q = ''; search.value = ''; update(); search.focus(); }
    }, '×');

    var tiles = h('div', { class: 'stat-tiles', 'aria-label': 'Item totals by shop category' },
      tile('All items', total, ''),
      tile('Weapon', DB.counts.byCategory.Weapon, 'weapon', 'Weapon'),
      tile('Vitality', DB.counts.byCategory.Vitality, 'vitality', 'Vitality'),
      tile('Spirit', DB.counts.byCategory.Spirit, 'spirit', 'Spirit'));

    var catSeg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Shop category' });
    CATS.forEach(function (c) {
      var count = h('span', { class: 'c' }, '');
      var btn = h('button', { type: 'button', 'data-value': c, onclick: function () { st.cat = c; update(); } }, c === 'All' ? 'All' : c, ' ', count);
      refs.cat.push({ value: c, btn: btn, count: count });
      catSeg.appendChild(btn);
    });

    var tierSeg = h('div', { class: 'seg', role: 'group', 'aria-label': 'Tier' });
    [0].concat(TIERS).forEach(function (t) {
      var count = h('span', { class: 'c' }, '');
      var btn = h('button', { type: 'button', 'data-value': t, onclick: function () { st.tier = t; update(); } }, t ? 'T' + t : 'All tiers', ' ', count);
      refs.tier.push({ value: t, btn: btn, count: count });
      tierSeg.appendChild(btn);
    });

    var purposeSel = h('select', { class: 'select', id: 'ipurpose', 'aria-label': 'Purpose' });
    purposeSel.appendChild(h('option', { value: '' }, 'All purposes'));
    ['offensive', 'defensive', 'utility'].forEach(function (g) {
      var og = h('optgroup', { label: GROUP_LABEL[g] });
      (DB.tagDefinitions || []).filter(function (t) { return t.group === g; }).forEach(function (t) {
        var opt = h('option', { value: t.id }, t.label);
        refs.tagOpts.push({ id: t.id, opt: opt, label: t.label });
        og.appendChild(opt);
      });
      purposeSel.appendChild(og);
    });
    purposeSel.addEventListener('change', function () { st.purpose = purposeSel.value; update(); });

    var sortSel = h('select', { class: 'select', id: 'isort', 'aria-label': 'Sort items' });
    SORTS.forEach(function (s) { sortSel.appendChild(h('option', { value: s.id }, s.label)); });
    sortSel.addEventListener('change', function () { st.sort = sortSel.value; update(); });

    refs.clearAll = h('button', {
      type: 'button', class: 'btn-ghost', onclick: function () {
        st.q = ''; st.cat = 'All'; st.tier = 0; st.purpose = ''; st.sort = 'default';
        search.value = ''; purposeSel.value = ''; sortSel.value = 'default'; update(); search.focus();
      }
    }, 'Clear filters');

    refs.toggle = h('button', {
      type: 'button', class: 'ifilter-toggle', 'aria-controls': 'ifilters', 'aria-expanded': 'false',
      onclick: function () {
        var open = panel.classList.toggle('open');
        refs.toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      }
    }, 'Filters');
    var panel = h('div', { class: 'ifilters', id: 'ifilters' },
      h('div', { class: 'frow' }, h('span', { class: 'flabel' }, 'Shop category'), catSeg),
      h('div', { class: 'frow' }, h('span', { class: 'flabel' }, 'Tier'), tierSeg),
      h('div', { class: 'frow frow-two' },
        h('label', { class: 'fcontrol' }, h('span', null, 'Purpose'), purposeSel),
        h('label', { class: 'fcontrol' }, h('span', null, 'Sort'), sortSel),
        refs.clearAll));

    refs.count = h('p', { class: 'count', 'aria-live': 'polite' });
    refs.chips = h('div', { class: 'chips' });
    refs.grid = h('div', { class: 'item-grid', id: 'igrid' });
    // Remember where the user was when they open an item, so Back returns to the same place.
    refs.grid.addEventListener('click', function (e) {
      if (e.target.closest && e.target.closest('a.item-card')) {
        try { sessionStorage.setItem(RETURN_KEY, String(window.scrollY)); } catch (err) { /* ignore */ }
      }
    });

    var head = h('header', { class: 'banner items-banner' },
      h('p', { class: 'eyebrow' }, 'Deadlock Wiki · Items'),
      h('h1', { id: 'items-title' }, 'Itemization'),
      h('p', { class: 'lede' }, 'Every shop item in Deadlock, with its shop category, tier, soul cost, verified stats, recipe links, and hero usage. Filter by category, tier, or purpose, or search by name, effect, or stat.'),
      h('p', { class: 'items-total small' }, h('strong', null, String(total)), ' items in the current database · verified ', DB.dataVerified, ' · ', h('a', { href: DB.source.primary.url, target: '_blank', rel: 'noopener' }, 'Deadlocker'), ' is the source'),
      tiles);

    var toolbar = h('div', { class: 'toolbar' },
      h('div', { class: 'search' },
        searchIcon(),
        search, refs.clearSearch, h('span', { class: 'kbd' }, '/')),
      refs.toggle);

    app.appendChild(h('section', { class: 'items-page', 'aria-labelledby': 'items-title' }, head, toolbar, panel, h('div', { class: 'count-row' }, refs.count, refs.chips), refs.grid));

    refs.search = search; refs.purposeSel = purposeSel; refs.sortSel = sortSel; refs.panel = panel;
    update();

    var ret = null;
    try { ret = sessionStorage.getItem(RETURN_KEY); sessionStorage.removeItem(RETURN_KEY); } catch (e) { ret = null; }
    if (ret !== null) window.scrollTo(0, Number(ret) || 0);

    function tile(label, n, cls, cat) {
      var inner = [h('div', { class: 'n' }, String(n)), h('div', { class: 'l' }, label)];
      if (!cat) return h('div', { class: 'tile' }, inner);
      return h('button', {
        type: 'button', class: 'tile ' + cls,
        'aria-label': label + ': ' + n + ' items. Show ' + label + ' items',
        onclick: function () { st.cat = cat; update(); }
      }, inner);
    }

    function update() {
      saveState(st);
      // Facet counts reflect the other active filters.
      refs.cat.forEach(function (r) {
        var n = DB.items.filter(function (it) { return matchItem(it, st, 'cat') && (r.value === 'All' || it.category === r.value); }).length;
        r.count.textContent = String(n);
        r.btn.setAttribute('aria-pressed', st.cat === r.value ? 'true' : 'false');
      });
      refs.tier.forEach(function (r) {
        var n = DB.items.filter(function (it) { return matchItem(it, st, 'tier') && (!r.value || it.tier === r.value); }).length;
        r.count.textContent = String(n);
        r.btn.setAttribute('aria-pressed', st.tier === r.value ? 'true' : 'false');
      });
      refs.tagOpts.forEach(function (r) {
        var n = DB.items.filter(function (it) { return matchItem(it, st, 'purpose') && hasTag(it, r.id); }).length;
        r.opt.textContent = r.label + ' (' + n + ')';
      });
      refs.purposeSel.value = st.purpose;
      refs.sortSel.value = st.sort;
      refs.clearSearch.hidden = st.q === '';
      refs.clearAll.disabled = !isDirty(st);

      var list = sortList(DB.items.filter(function (it) { return matchItem(it, st, null); }), st.sort);
      refs.count.textContent = 'Showing ' + list.length + ' of ' + total + ' items';
      if (refs.toggle) {
        var active = [st.cat !== 'All', st.tier !== 0, st.purpose !== '', st.q !== ''].filter(Boolean).length;
        refs.toggle.textContent = active ? 'Filters (' + active + ' active)' : 'Filters';
      }
      refreshChips(st);

      clear(refs.grid);
      if (!list.length) {
        refs.grid.appendChild(h('div', { class: 'empty', role: 'status' },
          h('p', { class: 'empty-title' }, 'No items match these filters.'),
          h('p', { class: 'small' }, 'Try a shorter search, or remove the purpose or tier filter.'),
          h('button', { type: 'button', class: 'btn-ghost', onclick: function () { refs.clearAll.click(); } }, 'Clear filters')));
      } else {
        var frag = document.createDocumentFragment();
        list.forEach(function (it) { frag.appendChild(itemCard(it)); });
        refs.grid.appendChild(frag);
      }
    }

    function refreshChips(st) {
      clear(refs.chips);
      var chips = [];
      if (st.q) chips.push({ label: 'Search: ' + st.q, clear: function () { st.q = ''; refs.search.value = ''; } });
      if (st.cat !== 'All') chips.push({ label: st.cat, clear: function () { st.cat = 'All'; } });
      if (st.tier) chips.push({ label: 'Tier ' + st.tier, clear: function () { st.tier = 0; } });
      if (st.purpose) chips.push({ label: (IDX.tagById[st.purpose] || {}).label || st.purpose, clear: function () { st.purpose = ''; refs.purposeSel.value = ''; } });
      chips.forEach(function (c) {
        refs.chips.appendChild(h('button', {
          type: 'button', class: 'chip-x', 'aria-label': 'Remove filter: ' + c.label,
          onclick: function () { c.clear(); update(); }
        }, c.label, ' ×'));
      });
    }
  }

  /* SVG elements must be created in the SVG namespace to render. */
  function searchIcon() {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');
    var c = document.createElementNS(ns, 'circle');
    c.setAttribute('cx', '11'); c.setAttribute('cy', '11'); c.setAttribute('r', '6.5');
    var p = document.createElementNS(ns, 'path');
    p.setAttribute('d', 'M20 20l-4.2-4.2');
    svg.appendChild(c); svg.appendChild(p);
    return svg;
  }

  function itemCard(it) {
    var tagChips = (it.tags || []).slice(0, 3).map(function (t) {
      return h('span', { class: 'tag-chip ' + t.group }, t.label);
    });
    return h('a', {
      class: 'item-card ' + catClass(it.category), href: '#/itemization/' + it.slug,
      'data-cat': it.category, 'aria-label': it.name + '. ' + it.category + ', tier ' + it.tier + ', ' + fmtCost(it.cost) + ' souls.'
    },
      h('div', { class: 'ic-media' }, iconEl(it, 'ic-img')),
      h('div', { class: 'ic-top' },
        h('span', { class: 'pill ' + catClass(it.category) }, it.category),
        h('span', { class: 'tier-badge' }, 'T' + it.tier)),
      h('div', { class: 'ic-name' }, it.name),
      h('div', { class: 'ic-meta' }, h('span', { class: 'ic-cost' }, fmtCost(it.cost) + ' souls'), ' · ', it.type),
      h('div', { class: 'ic-tags' }, tagChips.length ? tagChips : h('span', { class: 'tag-chip none' }, 'No purpose tag')),
      h('p', { class: 'ic-sum' }, summaryOf(it)));
  }

  /* ---------- status panels ---------- */
  function panel(app, title, msg) {
    clear(app);
    app.appendChild(h('div', { class: 'empty items-status', role: 'status' },
      h('p', { class: 'empty-title' }, title),
      h('p', { class: 'small' }, msg),
      h('a', { class: 'back', href: '#/itemization' }, 'Back to Itemization')));
  }

  function bindGlobalKeys() {
    if (globalKeysBound) return;
    globalKeysBound = true;
    document.addEventListener('keydown', function (e) {
      var active = document.activeElement;
      var typing = active && (active.tagName === 'INPUT' || active.tagName === 'SELECT' || active.tagName === 'TEXTAREA');
      var q = document.getElementById('iq');
      if (e.key === '/' && !typing && q) { e.preventDefault(); q.focus(); q.select(); }
      else if (e.key === 'Escape' && active === q && q.value) { q.value = ''; q.dispatchEvent(new Event('input')); }
    });
  }

  /* ---------- entry point, called by app.js on every hash change ---------- */
  function render(app, hash) {
    var route = parse(hash);
    if (!route) return;
    var token = ++renderToken;
    bindGlobalKeys();
    clear(app);
    app.appendChild(h('div', { class: 'items-loading', role: 'status' }, 'Loading item database…'));
    loadDb().then(function (db) {
      if (token !== renderToken) return; // a newer navigation has started
      if (route.view === 'browser') {
        document.title = 'Itemization · ' + BASE_TITLE;
        renderBrowser(app);
      } else if (window.ItemDetails) {
        window.ItemDetails.render(app, route.slug, util);
      }
    }).catch(function (err) {
      if (token !== renderToken) return;
      panel(app, 'Item data could not be loaded.',
        'Check that data/items.json is reachable, or open the site through a local web server. (' + (err && err.message ? err.message : 'unknown error') + ')');
    });
  }

  util.exportRoute = parse;
  window.Itemization = {
    util: util,
    handles: function (hash) { return !!parse(hash); },
    render: render,
    parse: parse,
    panel: panel
  };
})();
