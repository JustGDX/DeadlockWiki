/* Item detail: one reusable template, filled from items.json for every item.
   Loaded after js/itemization.js, which provides the shared helpers (window.Itemization.util).
   Every section shows the source it came from. Only facts from the source, and
   purpose tags derived from them by rule, are shown. */
(function () {
  'use strict';

  var ACTIVATION = {
    passive: 'Passive',
    press: 'Active · press to use',
    instant_cast: 'Active · instant cast',
    instant_cast_toggle: 'Active · toggle'
  };

  function render(app, slug, U) {
    var h = U.h, clear = U.clear;
    var db = U.db(), I = U.index();
    var it = I.bySlug[slug];
    clear(app);
    if (!it) {
      app.appendChild(notFound(slug, h));
      document.title = 'Item not found · Deadlock Wiki';
      window.scrollTo(0, 0);
      return;
    }
    var pos = I.pos[slug];
    var prev = db.items[pos - 1] || null;
    var next = db.items[pos + 1] || null;
    document.title = it.name + ' · Itemization · Deadlock Wiki';

    var pageSrc = it.sources[0];
    var root = h('article', { class: 'item-detail ' + U.catClass(it.category), 'data-cat': it.category, 'aria-labelledby': 'item-title' },
      h('a', { class: 'back', href: '#/itemization' }, backIcon(), ' Back to Itemization'),
      header(it, U, h),
      h('div', { class: 'idetail-body' },
        section('overview', 'Overview', 'Description from the source, and the purpose tags it supports.', overview(it, U, h), [srcItem(pageSrc, h)]),
        section('stats', 'Complete stats', 'Every stat Deadlocker lists for this item, shown as the source displays it.', statsBlock(it, h), [srcItem(pageSrc, h)]),
        section('limits', 'Limitations', 'Activation delays and self-costs, as Deadlocker lists them.', limitsBlock(it, h), [srcItem(pageSrc, h)]),
        section('links', 'Recipe and upgrade links', 'Built from, upgrades into, and same-tier items, from the source.', linksBlock(it, I, U, h), [srcItem(pageSrc, h)]),
        section('heroes', 'Hero usage', 'Pick and win rates from the Deadlocker usage feed. This shows what players bought. It is not a recommendation.', heroesBlock(it, h), [srcItem(pageSrc, h)]),
        section('sources', 'Sources and patch history', 'Where each fact came from, and the latest game-wide update.', sourcesBlock(it, db, h), null)),
      h('nav', { class: 'pager', 'aria-label': 'Previous and next item' },
        prev ? h('a', { class: 'pager-link', href: '#/itemization/' + prev.slug, rel: 'prev' }, h('span', { class: 'k' }, '← Previous'), h('span', { class: 'v' }, prev.name)) : h('span'),
        next ? h('a', { class: 'pager-link next', href: '#/itemization/' + next.slug, rel: 'next' }, h('span', { class: 'k' }, 'Next →'), h('span', { class: 'v' }, next.name)) : h('span')));

    app.appendChild(root);
    window.scrollTo(0, 0);
  }

  /* ---------- header ---------- */
  function header(it, U, h) {
    var typeLabel = ACTIVATION[it.activation] || it.type;
    return h('header', { class: 'idh' },
      h('div', { class: 'idh-icon-wrap' }, U.iconEl(it, 'idh-icon')),
      h('div', { class: 'idh-main' },
        h('p', { class: 'eyebrow' }, 'Itemization · ' + it.category + ' · Tier ' + it.tier),
        h('h1', { id: 'item-title' }, it.name),
        h('div', { class: 'idh-pills' },
          h('span', { class: 'pill ' + U.catClass(it.category) }, it.category),
          h('span', { class: 'tier-badge' }, 'Tier ' + it.tier),
          h('span', { class: 'chip-plain' }, U.fmtCost(it.cost) + ' souls'),
          h('span', { class: 'chip-plain' }, typeLabel))),
      h('dl', { class: 'idh-facts' },
        fact('Soul cost', U.fmtCost(it.cost), h),
        fact('Tier', String(it.tier), h),
        fact('Shop category', it.category, h),
        fact('Activation', it.type, h)));
  }
  function fact(k, v, h) {
    return h('div', { class: 'fact' }, h('dt', { class: 'k' }, k), h('dd', { class: 'v' }, v));
  }

  /* ---------- sections ---------- */
  function section(id, title, lede, body, srcs) {
    var s = document.createElement('section');
    s.className = 'isec';
    s.id = 'sec-' + id;
    s.setAttribute('aria-labelledby', 'h-' + id);
    var h2 = document.createElement('h2');
    h2.id = 'h-' + id;
    h2.textContent = title;
    s.appendChild(h2);
    if (lede) {
      var p = document.createElement('p');
      p.className = 'isec-lede';
      p.textContent = lede;
      s.appendChild(p);
    }
    s.appendChild(body);
    if (srcs && srcs.length) {
      var f = document.createElement('p');
      f.className = 'src';
      f.appendChild(document.createTextNode('Source: '));
      srcs.forEach(function (node, i) {
        if (i) f.appendChild(document.createTextNode(' · '));
        f.appendChild(node);
      });
      s.appendChild(f);
    }
    return s;
  }

  function srcItem(src, h) {
    return h('a', { href: src.url, target: '_blank', rel: 'noopener' }, src.label + ' (' + src.url.replace(/^https?:\/\//, '') + ')');
  }

  function overview(it, U, h) {
    var kids = [];
    if (!it.description || !it.description.length) {
      kids.push(h('p', { class: 'muted' }, 'The source page gives no description for this item. Its stats are listed below.'));
    } else {
      it.description.forEach(function (d) {
        kids.push(h('div', { class: 'desc-block' }, h('p', { class: 'desc-label' }, d.label), h('p', { class: 'desc-text' }, d.text)));
      });
    }
    kids.push(h('h3', { class: 'subhead' }, 'Purpose tags'));
    if (!it.tags.length) {
      kids.push(h('p', { class: 'muted small' }, 'No purpose tag applies to this item\'s stats or description.'));
    } else {
      kids.push(h('ul', { class: 'tag-list' }, it.tags.map(function (t) {
        return h('li', { class: 'tag-row ' + t.group },
          h('div', { class: 'tag-head' },
            h('span', { class: 'tag-chip ' + t.group }, t.label),
            h('span', { class: 'muted small' }, U.GROUP_LABEL[t.group] || t.group)),
          h('details', { class: 'evidence' },
            h('summary', null, 'Why this tag (' + t.evidence.length + ' evidence item' + (t.evidence.length === 1 ? '' : 's') + ')'),
            h('ul', null, t.evidence.map(function (e) { return h('li', null, e); }))));
      })));
    }
    kids.push(h('p', { class: 'small muted' }, 'Purpose tags are labels, not a rating. Each tag is assigned by rule from the stat labels and description text above, and lists the evidence it used.'));
    return h('div', null, kids);
  }

  function statsBlock(it, h) {
    if (!it.stats.length) return h('p', { class: 'muted' }, 'The source lists no stats for this item.');
    var limit = {};
    it.limitationStats.forEach(function (s) { limit[s.label + '|' + s.value] = true; });
    return h('div', null,
      h('table', { class: 'stat-table' },
        h('thead', null, h('tr', null, h('th', { scope: 'col' }, 'Stat'), h('th', { scope: 'col', class: 'v' }, 'Value'))),
        h('tbody', null, it.stats.map(function (s) {
          var isLim = !!limit[s.label + '|' + s.value];
          return h('tr', { class: isLim ? 'is-limit' : '' },
            h('th', { scope: 'row' }, s.label, isLim ? h('span', { class: 'limit-badge' }, 'Limitation') : null),
            h('td', { class: 'v' }, s.value));
        }))),
      h('p', { class: 'small muted' }, 'Values are copied from the source and keep its units (for example "m" or "mm" as displayed). Stats are not converted or rounded.'));
  }

  function limitsBlock(it, h) {
    if (!it.limitationStats.length) {
      return h('p', { class: 'muted' }, 'The source lists no activation delays, self-costs, or negative values for this item.');
    }
    return h('ul', { class: 'plain-list' }, it.limitationStats.map(function (s) {
      return h('li', null, h('strong', null, s.label + ': '), s.value, ' (activation delay or self-cost)');
    }));
  }

  function miniItem(target, U, h) {
    return h('a', { class: 'mini-item', href: '#/itemization/' + target.slug },
      U.iconEl(target, 'mini-img'),
      h('span', { class: 'mini-text' },
        h('span', { class: 'mini-name' }, target.name),
        h('span', { class: 'mini-meta' }, target.category + ' · T' + target.tier + ' · ' + U.fmtCost(target.cost))));
  }

  function linksBlock(it, I, U, h) {
    var h3 = function (t) { return h('h3', { class: 'subhead' }, t); };
    var kids = [];
    kids.push(h3('Built from (recipe)'));
    if (it.builtFrom.length) kids.push(h('div', { class: 'mini-grid' }, it.builtFrom.map(function (s) { return miniItem(I.bySlug[s], U, h); })));
    else kids.push(h('p', { class: 'muted small' }, 'No recipe components are listed for this item.'));
    kids.push(h3('Upgrades into'));
    if (it.upgradesInto.length) kids.push(h('div', { class: 'mini-grid' }, it.upgradesInto.map(function (s) { return miniItem(I.bySlug[s], U, h); })));
    else kids.push(h('p', { class: 'muted small' }, 'This item does not upgrade into another item.'));
    var same = it.sameCategoryTier;
    kids.push(h3(same.label || 'Same shop category and tier'));
    kids.push(h('p', { class: 'small muted' }, 'Other items in the same category and tier, as the shop groups them.'));
    if (same.items.length) {
      kids.push(h('ul', { class: 'chip-list' }, same.items.map(function (s) {
        var t = I.bySlug[s];
        return h('li', null, h('a', { class: 'chip-link', href: '#/itemization/' + t.slug }, t.name));
      })));
    }
    return h('div', null, kids);
  }

  function heroesBlock(it, h) {
    if (!it.usage.length) {
      return h('p', { class: 'muted' }, 'The Deadlocker usage feed has no hero data for this item.');
    }
    return h('div', { class: 'table-wrap' }, h('table', { class: 'usage-table' },
      h('thead', null, h('tr', null,
        h('th', { scope: 'col' }, 'Hero'), h('th', { scope: 'col' }, 'Most bought in'),
        h('th', { scope: 'col', class: 'v' }, 'Pick rate'), h('th', { scope: 'col', class: 'v' }, 'Win rate'))),
      h('tbody', null, it.usage.map(function (u) {
        return h('tr', null,
          h('th', { scope: 'row' }, u.heroSlug ? h('a', { href: '#/hero/' + u.heroSlug }, u.hero) : u.hero),
          h('td', null, u.stage),
          h('td', { class: 'v' }, u.pickPct.toFixed(1) + '%'),
          h('td', { class: 'v' }, u.winratePct.toFixed(1) + '%'));
      }))));
  }

  function sourcesBlock(it, db, h) {
    var links = it.sources.map(function (s) {
      return h('li', null, h('a', { href: s.url, target: '_blank', rel: 'noopener' }, s.label));
    });
    links.push(h('li', null, h('a', { href: db.source.crossCheck.url, target: '_blank', rel: 'noopener' }, db.source.crossCheck.label)));
    links.push(h('li', null, h('a', { href: db.source.changelog.url, target: '_blank', rel: 'noopener' }, db.source.changelog.label)));
    return h('div', null,
      h('dl', { class: 'meta-list' },
        h('div', null, h('dt', null, 'Data checked'), h('dd', null, db.dataVerified)),
        h('div', null, h('dt', null, 'Latest game update'), h('dd', null,
          db.source.changelog.latestEntry + ' · ',
          h('a', { href: db.source.changelog.latestUrl, target: '_blank', rel: 'noopener' }, 'read the notes'))),
        h('div', null, h('dt', null, 'Usage snapshot'), h('dd', null, db.source.usageSnapshot || 'Not stated')),
        h('div', null, h('dt', null, 'Item identifier'), h('dd', null, h('code', null, it.id)))),
      h('h3', { class: 'subhead' }, 'Sources'),
      h('ul', { class: 'plain-list src-list' }, links),
      h('h3', { class: 'subhead' }, 'Patch history'),
      h('p', { class: 'small' }, 'Deadlocker\'s item pages do not list a per-item change history. Game-wide changes are in the changelog above.'),
      h('p', { class: 'small muted' }, 'Stats and descriptions come from Deadlocker. Icons come from Valve\'s asset CDN, as served by deadlock-api. Purpose tags and the hero-usage table are derived from the source, not written by hand.'));
  }

  function notFound(slug, h) {
    return h('div', { class: 'empty items-status', role: 'status' },
      h('p', { class: 'empty-title' }, 'No item matches this address.'),
      h('p', { class: 'small' }, 'Check the link, or browse all items.'),
      h('a', { class: 'back', href: '#/itemization' }, 'Back to Itemization'));
  }

  function backIcon() {
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');
    var p = document.createElementNS(ns, 'path');
    p.setAttribute('d', 'M15 5l-7 7 7 7');
    svg.appendChild(p);
    return svg;
  }

  window.ItemDetails = { render: render };
})();
