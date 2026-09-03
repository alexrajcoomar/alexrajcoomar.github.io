/* ============================================================
   Alex Rajcoomar — portfolio
   One script for every page. Hand-written, no dependencies.

   Everything here is an enhancement: with JavaScript off the
   pages are still complete documents and every link still works.
   ============================================================ */
(function () {
  "use strict";

  var reduced = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Single-key shortcuts (/, ?, g, j, k) can be turned off from the
     keyboard sheet. On unless the reader has said otherwise; the guarded
     read matches every other storage access in this file. */
  var SINGLES = "keys.singles";
  function singlesOn() {
    try { return localStorage.getItem(SINGLES) !== "off"; } catch (e) { return true; }
  }

  /* ---------------------------------------------------- theme ----- */
  var themebtn = document.getElementById("themebtn");
  function isDark() {
    var t = document.documentElement.getAttribute("data-theme");
    if (t) return t === "dark";
    return !!(window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches);
  }
  function paintTheme() {
    if (!themebtn) return;
    themebtn.setAttribute("aria-label",
      isDark() ? "Switch to light mode" : "Switch to dark mode");
  }
  if (themebtn) {
    themebtn.addEventListener("click", function () {
      var next = isDark() ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      /* Guarded: some embedded contexts throw on storage access, and the
         toggle must still work when they do. */
      try { localStorage.setItem("theme", next); } catch (e) {}
      paintTheme();
    });
    paintTheme();
    if (window.matchMedia) {
      var mq = matchMedia("(prefers-color-scheme: dark)");
      if (mq.addEventListener) mq.addEventListener("change", paintTheme);
    }
  }

  /* ------------------------------------------------ reveal on view -
     The pre-state is only applied by CSS under .js, and under reduced
     motion the elements are snapped to their end state rather than
     given a shorter animation. */
  var risers = [].slice.call(document.querySelectorAll(".rise"));
  if (reduced || !("IntersectionObserver" in window)) {
    risers.forEach(function (n) { n.classList.add("in"); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.05 });
    risers.forEach(function (n) { io.observe(n); });

    /* Safety sweep. A jump to an anchor, or a very fast scroll, can carry
       an element past the viewport without the observer ever reporting an
       intersection, and content that stays at opacity 0 is content the
       reader never sees. This reveals anything already scrolled past. */
    var sweeping = false;
    function sweep() {
      sweeping = false;
      var h = window.innerHeight;
      for (var i = risers.length - 1; i >= 0; i--) {
        var n = risers[i];
        if (n.classList.contains("in")) { risers.splice(i, 1); continue; }
        if (n.getBoundingClientRect().top < h * 0.95) {
          n.classList.add("in"); io.unobserve(n); risers.splice(i, 1);
        }
      }
      if (!risers.length) removeEventListener("scroll", queueSweep);
    }
    function queueSweep() {
      if (!sweeping) { sweeping = true; requestAnimationFrame(sweep); }
    }
    addEventListener("scroll", queueSweep, { passive: true });
    addEventListener("hashchange", queueSweep);
    setTimeout(sweep, 1200);
  }

  /* The flat library-filter block that used to sit here targeted a
     #list element no page has carried since the library moved to
     grouped sections; the grouped filter below is the live one, and
     both bound listeners to the same #q. Removed rather than kept as a
     trap for the next editor. */

  /* -------------------------------------------- command palette ----
     Search every piece from any page. Opened by the header button,
     by "/" and by Cmd or Ctrl + K. Fully keyboard operable, and it
     returns focus to whatever opened it. */
  var work = window.WORK || [];
  var pal = document.getElementById("cmdk");
  var input = document.getElementById("cmdk-input");
  var results = document.getElementById("cmdk-list");
  var openBtn = document.getElementById("searchbtn");
  if (pal && input && results && work.length) {
    var cur = 0, items = [];

    function score(it, t) {
      if (!t) return 1;
      var title = it.t.toLowerCase(), sub = (it.s || "").toLowerCase();
      var other = ((it.c || "") + " " + it.k + " " + (it.d || "")).toLowerCase();
      if (title.indexOf(t) === 0) return 100;
      if (title.indexOf(t) > -1) return 70;
      if (sub.indexOf(t) > -1) return 45;
      if (other.indexOf(t) > -1) return 30;
      /* every word of the query present somewhere */
      var all = title + " " + sub + " " + other, parts = t.split(/\s+/);
      for (var i = 0; i < parts.length; i++) if (all.indexOf(parts[i]) < 0) return 0;
      return 15;
    }
    function render() {
      var term = input.value.trim().toLowerCase();
      var t = term;
      var hits = work.map(function (it) { return { it: it, s: score(it, t) }; })
                     .filter(function (r) { return r.s > 0; })
                     .sort(function (a, b) { return b.s - a.s; })
                     .slice(0, 9);
      /* An empty box leads with what this reader opened last. These are
         marked as their own band rather than folded into the kind groups,
         where a recently opened tool would sink to the bottom. */
      var recentSet = {};
      if (!term) {
        var rec = readRecent();
        if (rec.length) {
          var byUrl = {};
          work.forEach(function (it) { byUrl[it.u] = it; });
          var lead = rec.map(function (u) { return byUrl[u]; }).filter(Boolean)
                        .map(function (it) { recentSet[it.u] = 1; return { it: it, s: 999 }; });
          hits = lead.concat(hits.filter(function (r) { return !recentSet[r.it.u]; })).slice(0, 9);
        }
      }
      results.textContent = "";
      if (!hits.length) {
        var empty = el("li", "cmdk-empty");
        empty.textContent = "Nothing matches that. Try a course code, or a word from a title.";
        results.appendChild(empty);
        items = [];
        return;
      }
      /* Built as nodes, not as a string of HTML. Titles and subtitles come from
         content/pieces.json, which is written by the editor, so an ampersand or
         an angle bracket typed into a title used to land in this markup
         unescaped. textContent cannot be talked into becoming an element. */
      /* Grouped by what the piece is, so nine results read as three short
         lists rather than one undifferentiated one. */
      var order = ["Essay", "Reference", "Tool"], n = 0;
      var bands = [["__recent", "Recently opened"], ["Essay", "Essays"],
                   ["Reference", "References"], ["Tool", "Tools"], ["", "Other"]];
      bands.forEach(function (pair) {
        var kind = pair[0];
        var band = hits.filter(function (r) {
          if (kind === "__recent") return recentSet[r.it.u];
          if (recentSet[r.it.u]) return false;          // already shown above
          return kind ? r.it.k === kind : order.indexOf(r.it.k) === -1;
        });
        if (!band.length) return;
        var head = el("li", "cmdk-group");
        head.setAttribute("role", "presentation");
        head.textContent = pair[1];
        results.appendChild(head);
        band.forEach(function (r) {
          var it = r.it;
          var li = el("li");
          li.setAttribute("role", "option");
          li.id = "cmdk-o" + n;
          li.setAttribute("aria-selected", n === 0 ? "true" : "false");
          if (n === 0) li.className = "on";
          n++;

          var a = el("a");
          a.setAttribute("href", it.u);

          var left = el("span");
          var t = el("span", "t");
          /* Nodes, never a string of HTML: the title is content the editor
             writes, so it is placed as text and only the matched run is
             wrapped. */
          markInto(t, it.t, term);
          left.appendChild(t);
          if (it.s) {
            var sub = el("span", "s");
            sub.appendChild(document.createTextNode(" \u2014 "));
            markInto(sub, it.s, term);
            left.appendChild(sub);
          }

          var right = el("span", "s");
          right.textContent = it.c ? it.c : it.d || "";

          a.appendChild(left);
          a.appendChild(right);
          li.appendChild(a);
          results.appendChild(li);
        });
      });
      items = [].slice.call(results.querySelectorAll("li[role=option]"));
      cur = 0;
      /* the combobox names its selection on every render, not only after
         an arrow key; an emptied list clears the stale reference */
      if (items.length) input.setAttribute("aria-activedescendant", items[0].id);
      else input.removeAttribute("aria-activedescendant");
    }

    /* Puts `text` into `host`, wrapping the first case-insensitive run of
       `needle` in a <mark>. Everything is a text node, so a title that
       contains an angle bracket stays a title. */
    function markInto(host, text, needle) {
      if (!needle) { host.appendChild(document.createTextNode(text)); return; }
      var i = text.toLowerCase().indexOf(needle);
      if (i < 0) { host.appendChild(document.createTextNode(text)); return; }
      host.appendChild(document.createTextNode(text.slice(0, i)));
      var m = document.createElement("mark");
      m.textContent = text.slice(i, i + needle.length);
      host.appendChild(m);
      host.appendChild(document.createTextNode(text.slice(i + needle.length)));
    }
    function el(tag, cls) {
      var n = document.createElement(tag);
      if (cls) n.className = cls;
      return n;
    }
    function move(d) {
      if (!items.length) return;
      items[cur].classList.remove("on");
      items[cur].setAttribute("aria-selected", "false");
      cur = (cur + d + items.length) % items.length;
      items[cur].classList.add("on");
      items[cur].setAttribute("aria-selected", "true");
      input.setAttribute("aria-activedescendant", items[cur].id);
      var a = items[cur], top = a.offsetTop, h = a.offsetHeight, box = results;
      if (top < box.scrollTop) box.scrollTop = top;
      else if (top + h > box.scrollTop + box.clientHeight) box.scrollTop = top + h - box.clientHeight;
    }
    /* What the reader opened last, so an empty box is a shortcut rather
       than an arbitrary first nine. Stored per browser, never sent
       anywhere, and the list falls back to the ordinary ranking if the
       browser refuses storage. */
    var RECENT = "portfolio.recent";
    function readRecent() {
      try { return JSON.parse(localStorage.getItem(RECENT) || "[]"); }
      catch (e) { return []; }
    }
    function noteRecent(u) {
      try {
        var r = readRecent().filter(function (x) { return x !== u; });
        r.unshift(u);
        localStorage.setItem(RECENT, JSON.stringify(r.slice(0, 5)));
      } catch (e) {}
    }
    results.addEventListener("click", function (e) {
      var a = e.target.closest("a[href]");
      if (a) noteRecent(a.getAttribute("href"));
    });

    /* A native dialog: showModal() traps focus, Escape closes it, and focus
       goes back to whatever opened it, all without a line here. The page
       behind it is inert while it is open, and CSS stops the scroll. */
    function open() {
      if (pal.open) return;
      pal.showModal();
      input.setAttribute("aria-expanded", "true");
      input.value = "";
      render();
      input.focus();
    }
    function close() { if (pal.open) pal.close(); }
    pal.addEventListener("close", function () { input.setAttribute("aria-expanded", "false"); });
    if (openBtn) openBtn.addEventListener("click", open);
    input.addEventListener("input", render);
    /* a click on the backdrop reaches the dialog element itself */
    pal.addEventListener("mousedown", function (e) { if (e.target === pal) close(); });
    pal.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
      else if (e.key === "Enter") {
        if (items.length) { e.preventDefault(); items[cur].querySelector("a").click(); }
      } else if (e.key === "Tab") {
        /* The dialog is modal, so focus stays inside it. Tab is given the
           useful meaning instead of none: it moves the selection. */
        e.preventDefault();
        move(e.shiftKey ? -1 : 1);
      }
    });
    results.addEventListener("mousemove", function (e) {
      var li = e.target.closest("li[role=option]");
      if (!li || !items.length) return;
      var n = items.indexOf(li);
      if (n > -1 && n !== cur) { move(n - cur); }
    });
    document.addEventListener("keydown", function (e) {
      var tag = (e.target.tagName || "").toLowerCase();
      var typing = tag === "input" || tag === "textarea" || e.target.isContentEditable;
      if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); pal.open ? close() : open();
      } else if (typing || pal.open || !singlesOn()) {
        /* single-key routes only: the modified Cmd/Ctrl+K above stays on */
      } else if (e.key === "/") {
        e.preventDefault(); open();
      } else if (e.key === "?") {
        e.preventDefault(); keys(true);
      } else if (e.key === "g" || e.key === "G") {
        /* g then a letter: the two-stroke jump every reader of a long site
           already knows from mail clients and code hosts. */
        goArmed = Date.now();
      } else if (!typing && !pal.open && goArmed && Date.now() - goArmed < 1200) {
        var to = { h: "index.html", r: "research.html", c: "coursework.html",
                   t: "tools.html", l: "library.html", a: "about.html" }[e.key.toLowerCase()];
        goArmed = 0;
        if (to) { e.preventDefault(); location.href = to; }
      }
    });
  }

  /* --------------------------------------------- the shortcuts sheet --
     The header already advertises "/" . Everything else was undiscoverable,
     which is the same as absent. */
  var goArmed = 0;
  /* The sheet is a native dialog: the modal trap, Escape and the return of
     focus are the browser's, and the Close button is a method="dialog"
     form submit, so closing needs no script at all. */
  function keys(on) {
    var sheet = document.getElementById("keysheet");
    if (!sheet) return;
    if (on) {
      if (!sheet.open) sheet.showModal();
      var c = sheet.querySelector(".close");
      if (c) c.focus();
    } else if (sheet.open) {
      sheet.close();
    }
  }
  (function () {
    var sheet = document.getElementById("keysheet");
    if (!sheet) return;
    sheet.addEventListener("click", function (e) { if (e.target === sheet) keys(false); });
    var opener = document.getElementById("keysbtn");
    if (opener) opener.addEventListener("click", function () { keys(true); });
    /* Single-key shortcuts can be turned off, for speech input and for
       anyone whose stray key press keeps opening things (WCAG 2.1.4).
       The choice stays in this browser, like the theme. */
    var toggle = document.getElementById("keysingles");
    if (toggle) {
      toggle.checked = singlesOn();
      toggle.addEventListener("change", function () {
        try { localStorage.setItem(SINGLES, toggle.checked ? "on" : "off"); } catch (e) {}
      });
    }
  })();

  /* --------------------------------------- grouped library lists --
     The library is split by what asked for the work, so the filter has
     to walk several lists and hide a whole group when nothing in it
     survives. Without this a filter leaves empty headers behind. */
  (function () {
    var groups = [].slice.call(document.querySelectorAll(".lgroup"));
    if (!groups.length) return;
    var qq = document.getElementById("q"),
        chipsEl = document.getElementById("chips"),
        surfEl = document.getElementById("chips-surface"),
        noteEl = document.getElementById("resultnote"),
        none = document.getElementById("noresults"),
        f = "all", fs = "all", total = 0;
    var sets = groups.map(function (g) {
      /* the head row and the subtotal are the statement's furniture, not
         pieces: never counted, and shown only while the list is whole */
      var r = [].slice.call(g.querySelectorAll("ol.index > li:not(.sr-head):not(.sr-sub)"));
      total += r.length;
      return { g: g, rows: r };
    });
    function run() {
      var term = (qq && qq.value || "").trim().toLowerCase(), shown = 0;
      sets.forEach(function (s) {
        var vis = 0;
        s.rows.forEach(function (li) {
          var ok = (f === "all" || li.getAttribute("data-kind") === f) &&
                   (fs === "all" || li.getAttribute("data-surface") === fs) &&
                   (!term || (li.getAttribute("data-search") || "").indexOf(term) > -1);
          li.hidden = !ok; if (ok) vis++;
        });
        s.g.hidden = vis === 0; shown += vis;
        var whole = f === "all" && fs === "all" && !term;
        [].forEach.call(s.g.querySelectorAll(".sr-head,.sr-sub"), function (el) { el.hidden = !whole; });
      });
      if (noteEl) {
        noteEl.textContent = shown === total
          ? "Showing all " + total + " pieces."
          : shown === 0
            ? "Nothing matches" + (term ? ' "' + qq.value.trim() + '"' : " that filter") + "."
            : "Showing " + shown + " of " + total + " pieces" +
              (term ? ' matching "' + qq.value.trim() + '".' : ".");
      }
      if (none) none.hidden = shown !== 0;
    }
    if (qq) qq.addEventListener("input", run);
    function chipGroup(box, set) {
      if (!box) return;
      box.addEventListener("click", function (e) {
        var b = e.target.closest(".chip"); if (!b) return;
        set(b.getAttribute("data-f"));
        [].slice.call(box.querySelectorAll(".chip")).forEach(function (c) {
          c.setAttribute("aria-pressed", c === b ? "true" : "false");
        });
        run();
      });
    }
    chipGroup(chipsEl, function (v) { f = v; });
    chipGroup(surfEl, function (v) { fs = v; });

    /* A tag that looks like a filter should behave like one. Clicking one
       puts it in the search box, which is the control the reader already
       understands, rather than inventing a second filtering state. */
    groups.forEach(function (g) {
      g.addEventListener("click", function (e) {
        var tag = e.target.closest(".tag");
        if (!tag || !qq) return;
        e.preventDefault();
        var word = tag.textContent.trim();
        qq.value = (qq.value.trim().toLowerCase() === word.toLowerCase()) ? "" : word;
        run();
        qq.focus();
        qq.setSelectionRange(qq.value.length, qq.value.length);
      });
    });

    /* j and k walk the visible rows, matching the g-then-letter vocabulary
       the rest of the site uses. Enter opens whichever row is marked. */
    var here = -1;
    document.addEventListener("keydown", function (e) {
      var tag = (e.target.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea" || e.target.isContentEditable) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (!singlesOn()) return;
      var pal = document.getElementById("cmdk");
      if (pal && pal.open) return;
      var vis = [];
      sets.forEach(function (s) {
        s.rows.forEach(function (li) { if (!li.hidden) vis.push(li); });
      });
      if (!vis.length) return;
      if (e.key === "j" || e.key === "k") {
        e.preventDefault();
        if (here > -1 && vis[here]) vis[here].classList.remove("cursor");
        here = e.key === "j" ? Math.min(vis.length - 1, here + 1) : Math.max(0, here - 1);
        var li = vis[here];
        li.classList.add("cursor");
        var a = li.querySelector("a"); if (a) a.focus({ preventScroll: true });
        li.scrollIntoView({ block: "center", behavior: reduced ? "auto" : "smooth" });
      }
    });

    /* Reordering. The published order is a grouping, which is the right
       default and the wrong one for "what is the longest thing here".
       Sorting moves the rows inside their own group rather than across
       groups, so the split the page is built on survives the sort. */
    var sortEl = document.getElementById("sort");
    if (sortEl) {
      var original = sets.map(function (s) { return s.rows.slice(); });
      sortEl.addEventListener("change", function () {
        var mode = sortEl.value;
        sets.forEach(function (s, i) {
          var list = s.g.querySelector("ol.index");
          if (!list) return;
          var rows = original[i].slice();
          var n = function (li, a) { return +(li.getAttribute(a) || 0); };
          if (mode === "long")  rows.sort(function (a, b) { return n(b,"data-words") - n(a,"data-words"); });
          if (mode === "short") rows.sort(function (a, b) { return n(a,"data-words") - n(b,"data-words"); });
          if (mode === "figs")  rows.sort(function (a, b) { return n(b,"data-figs") - n(a,"data-figs"); });
          if (mode === "az")    rows.sort(function (a, b) {
            return (a.getAttribute("data-title") || "").localeCompare(b.getAttribute("data-title") || "");
          });
          var frag = document.createDocumentFragment();
          rows.forEach(function (li) { frag.appendChild(li); });
          list.appendChild(frag);
          /* a reordered list is no longer the statement: its head and its
             subtotal step aside, and come back with the published order */
          var head = list.querySelector(".sr-head"), sub = list.querySelector(".sr-sub");
          if (mode === "default") {
            if (head) list.insertBefore(head, list.firstChild);
            if (sub) list.appendChild(sub);
          }
          [head, sub].forEach(function (el) { if (el) el.hidden = mode !== "default"; });
          /* the leading numeral is a position in the list, so it is
             renumbered rather than travelling with its row */
          rows.forEach(function (li, k) {
            var num = li.querySelector(".num");
            if (num) num.textContent = (k + 1 < 10 ? "0" : "") + (k + 1);
          });
        });
      });
    }
  })();

  /* -------------------------------------------- the corpus readout --
     Every document in the drawing is a link carrying its own numbers.
     Pointing at one, or tabbing to it, fills the rail beside the figure
     and shows its share of the whole. */
  (function () {
    var fig = document.querySelector(".corpusfig");
    var box = document.getElementById("corpusread");
    if (!fig || !box) return;
    var rest = box.querySelector(".cf-rest"),
        out  = box.querySelector(".cf-out"),
        name = box.querySelector(".cf-name"),
        meta = box.querySelector(".cf-meta"),
        bar  = box.querySelector(".cf-bar i"),
        share = box.querySelector(".cf-share");
    var rows = [].slice.call(fig.querySelectorAll(".cf-row"));
    if (!rows.length) return;
    var widest = 0, total = 0;
    rows.forEach(function (r) {
      var w = +(r.getAttribute("data-w") || 0);
      total += w; if (w > widest) widest = w;
    });
    var hold = null;
    function show(r) {
      clearTimeout(hold);
      var w = +(r.getAttribute("data-w") || 0);
      var mins = +(r.getAttribute("data-m") || 0);
      var f = +(r.getAttribute("data-f") || 0), t = +(r.getAttribute("data-b") || 0);
      name.textContent = r.getAttribute("data-t") || "";
      var bits = [w.toLocaleString("en-CA") + " words"];
      if (mins) bits.push(mins + " min");
      if (f) bits.push(f + (f === 1 ? " figure" : " figures"));
      if (t) bits.push(t + (t === 1 ? " table" : " tables"));
      meta.textContent = bits.join("  ·  ");
      share.textContent = r.getAttribute("data-k") + "  ·  " + r.getAttribute("data-c") +
        "  ·  " + (w / total * 100).toFixed(1) + "% of the words drawn here";
      rest.hidden = true; out.hidden = false;
      /* Set directly rather than inside requestAnimationFrame: rAF does not
         run in a background tab, and a proportion bar that never arrives is
         worse than one that arrives without its transition. */
      if (bar) bar.style.width = (w / widest * 100).toFixed(1) + "%";
    }
    function clear() {
      /* a short hold, so crossing a gap between two rows does not make
         the rail flicker back to its resting state */
      hold = setTimeout(function () {
        out.hidden = true; rest.hidden = false;
        if (bar) bar.style.width = "0";
      }, 260);
    }
    rows.forEach(function (r) {
      r.addEventListener("mouseenter", function () { show(r); });
      r.addEventListener("focus", function () { show(r); });
      r.addEventListener("mouseleave", clear);
      r.addEventListener("blur", clear);
    });
  })();

  /* --------------------------------------------- linkable sections --
     Every band on these pages is worth pointing someone at. The heading
     gets an anchor that appears on hover or focus, gives the section an id
     if the build did not, and copies the address rather than only moving
     to it. */
  (function () {
    var heads = [].slice.call(document.querySelectorAll(".band .sechead h2, .hero .sechead h2"));
    if (!heads.length) return;
    /* one polite live region for the copy confirmations, because the CSS
       pseudo-content the anchor flashes is not reliably announced */
    var live = document.createElement("span");
    live.className = "sr";
    live.setAttribute("aria-live", "polite");
    document.body.appendChild(live);
    heads.forEach(function (h) {
      var sec = h.closest("section");
      if (!sec) return;
      if (!sec.id) {
        sec.id = (h.textContent || "section").toLowerCase()
          .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40);
      }
      var a = document.createElement("a");
      a.className = "anchor";
      a.href = "#" + sec.id;
      a.setAttribute("aria-label", "Link to this section: " + (h.textContent || "").trim());
      a.innerHTML = "&#167;";
      a.addEventListener("click", function () {
        /* the link navigates as a link promises to; the copy is the extra,
           and it is announced rather than only flashed */
        if (!navigator.clipboard) return;
        var url = location.href.split("#")[0] + "#" + sec.id;
        navigator.clipboard.writeText(url).then(function () {
          a.classList.add("copied");
          live.textContent = "";
          setTimeout(function () { live.textContent = "Link copied"; }, 30);
          setTimeout(function () { a.classList.remove("copied"); }, 1400);
        }, function () {});
      });
      h.appendChild(a);
    });
  })();

  /* ------------------------------------------------ back to the top --
     Only on pages long enough to need it, and only once the reader has
     gone far enough that the header is out of reach. */
  (function () {
    if (document.documentElement.scrollHeight < 3400) return;
    if (document.querySelector(".docbar")) return;   // documents carry their own
    var b = document.createElement("button");
    b.className = "totop"; b.type = "button";
    b.innerHTML = '<span aria-hidden="true">&#8593;</span> Top';
    b.setAttribute("aria-label", "Back to the top of the page");
    b.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
      var skip = document.querySelector("h1");
      if (skip) { skip.setAttribute("tabindex", "-1"); skip.focus({ preventScroll: true }); }
    });
    document.body.appendChild(b);
    var tick = false;
    function run() {
      tick = false;
      b.classList.toggle("on", (window.scrollY || document.documentElement.scrollTop) > 900);
    }
    addEventListener("scroll", function () {
      if (!tick) { tick = true; requestAnimationFrame(run); }
    }, { passive: true });
    run();
  })();

  /* --------------------------------------------- the nav edge fade --
     On narrow screens the nav scrolls sideways behind a mask fade that
     signals more content. The CSS hook that lifts the fade at scroll end
     was never driven by anything, so the last item stayed dimmed even
     when fully in view. */
  (function () {
    var nav = document.querySelector("nav.main");
    if (!nav) return;
    function edge() {
      nav.classList.toggle("scrolled-end",
        nav.scrollLeft + nav.clientWidth >= nav.scrollWidth - 4);
    }
    nav.addEventListener("scroll", edge, { passive: true });
    addEventListener("resize", edge);
    edge();
  })();

  /* ------------------------------------------------ the nav underline
     The rule under the current page slides to whichever item the pointer
     is over and returns when it leaves, so the header reads as one
     control rather than six. */
  (function () {
    var nav = document.querySelector("nav.main");
    if (!nav || reduced) return;
    var links = [].slice.call(nav.querySelectorAll("a"));
    var current = nav.querySelector('a[aria-current="page"]');
    if (!current) return;
    var ink = document.createElement("span");
    ink.className = "navink";
    nav.appendChild(ink);
    function moveTo(a) {
      if (!a) return;
      ink.style.width = a.offsetWidth + "px";
      ink.style.transform = "translateX(" + a.offsetLeft + "px)";
    }
    function home() { moveTo(current); }
    links.forEach(function (a) {
      a.addEventListener("mouseenter", function () { moveTo(a); });
      a.addEventListener("focus", function () { moveTo(a); });
    });
    nav.addEventListener("mouseleave", home);
    nav.addEventListener("focusout", function (e) {
      if (!nav.contains(e.relatedTarget)) home();
    });
    addEventListener("resize", home);
    /* the webfont lands after first paint and changes every width */
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(home);
    setTimeout(home, 0);
  })();
})();

  /* --------------------------------------------- the atlas, in miniature
     The same sphere the atlas page draws, at a size where it is a picture
     rather than an instrument: no labels, no hit testing, no second copy of
     the headings. Only the positions and the encoding travel, two decimals
     each, because that is all a small radius can show.

     Mark area follows the apportioned word weight, as it does on the atlas,
     and the sphere idles at zero frames, as the atlas does. The two used
     to disagree: the atlas said in its first wall label that size carries
     level, and the home page drew all 1,247 marks the same size directly
     underneath a paragraph making the same claim. The ratios below are the
     atlas's own (atlas.js:448, `0.75 + (4 - level) * 0.3`), scaled so that
     an ordinary third-level heading lands on the 0.7px radius this teaser
     already used and nothing else has to move. */
  (function () {
    var host = document.getElementById("atlasmini");
    if (!host || !host.getAttribute("data-pts")) return;

    /* This block sits outside the file's main closure, so it reads the motion
       preference for itself rather than borrowing a variable that is not in
       scope here. */
    var reduced = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    /* The fourth field is the kind letter, optionally followed by the
       heading level. A missing digit means level 3, which is what 743 of
       the points are, so the common case costs nothing on the wire. */
    var raw = host.getAttribute("data-pts").split(";");
    var pts = [];
    for (var i = 0; i < raw.length; i++) {
      var f = raw[i].split(",");
      if (f.length < 4) continue;
      var mark = f[3];
      var band = mark.length > 1 ? +mark.charAt(1) : 0;
      if (!(band >= 0 && band <= 9)) band = 0;
      var P = { x: +f[0], y: +f[1], z: +f[2], k: mark.charAt(0), b: band };
      /* the atlas stands its six tool marks off the sphere; the teaser
         makes the same claim about the same points */
      if (P.k === "t") { P.x *= 1.13; P.y *= 1.13; P.z *= 1.13; }
      pts.push(P);
    }
    if (pts.length < 8) return;

    /* The connective layer, from the same harvest the Atlas draws: the
       documents with their centroids, which document each mark belongs to,
       and the links between documents that edges() found in prose. Without
       it the sphere still draws; with it, pointing at a mark draws the
       chords its document records, as the Atlas does, on demand. */
    var docs = [], own = [], lk = [];
    try {
      var dj = JSON.parse(document.getElementById("atlasmini-docs").textContent);
      docs = dj.docs || [];
      (dj.own || "").split(",").forEach(function (tok) {
        var m = tok.split("*"), i = +m[0], n = m.length > 1 ? +m[1] : 1;
        for (var r = 0; r < n; r++) own.push(i);
      });
      docs.forEach(function (d) { d.lk = []; d.marks = 0; });
      for (var oi = 0; oi < own.length && oi < pts.length; oi++) {
        if (docs[own[oi]]) docs[own[oi]].marks++;
      }
      (dj.lk || []).forEach(function (e) {
        var a = docs[e[0]], b = docs[e[1]];
        if (!a || !b || a === b) return;
        var have = null, li;
        for (li = 0; li < a.lk.length; li++) if (a.lk[li].g === b) { have = a.lk[li]; break; }
        if (have) have.out = true; else a.lk.push({ g: b, out: true, into: false });
        var back = null;
        for (li = 0; li < b.lk.length; li++) if (b.lk[li].g === a) { back = b.lk[li]; break; }
        if (back) back.into = true; else b.lk.push({ g: a, out: false, into: true });
      });
    } catch (e) { docs = []; own = []; }
    if (own.length !== pts.length) { docs = []; own = []; }
    var card = document.getElementById("atlasmini-card");
    var cardT = card && card.querySelector(".gc-t"), cardD = card && card.querySelector(".gc-d");
    /* A fine pointer hovers; a coarse one taps. A tap locks the document it
       lands on, so the chords and the card hold until the next tap, and the
       card's name is the link that opens it. */
    var fine = !!(window.matchMedia && window.matchMedia("(pointer:fine)").matches);
    var locked = false;

    /* atlas.js draws 0.55 + 0.028 * sqrt(words) plus a depth term. The
       payload carries sqrt(words) quantised to ten bands of 13, so the
       teaser draws the same rule at the band's centre, scaled by 0.55 for
       a sphere a third the size. */
    var BAND_R = [];
    for (var bi = 0; bi < 10; bi++) BAND_R.push(0.55 * (0.55 + 0.028 * (13 * bi + 6.5)));

    var cv = document.createElement("canvas");
    cv.setAttribute("aria-hidden", "true");
    host.appendChild(cv);
    var ctx = cv.getContext && cv.getContext("2d");
    if (!ctx) return;

    var C = {};
    function colours() {
      var s = getComputedStyle(document.documentElement);
      C.i = s.getPropertyValue("--accent").trim() || "#14509b";
      C.c = s.getPropertyValue("--ink-3").trim() || "#66635a";
      C.t = s.getPropertyValue("--tool").trim() || "#0f6b58";
      C.r = s.getPropertyValue("--rule").trim() || "#ddd9cf";
      C.e = s.getPropertyValue("--edge").trim() || "#8a847c";
      C.p = s.getPropertyValue("--paper").trim() || "#faf9f6";
      C.k = s.getPropertyValue("--ink").trim() || "#16150f";
      /* the second accent: a link the prose records, and nothing else */
      C.l = s.getPropertyValue("--link").trim() || C.k;
    }
    function dark() {
      var h = C.p.replace("#", "");
      if (h.length === 3) h = h[0] + h[0];
      return parseInt(h.slice(0, 2), 16) < 128;
    }
    colours();
    new MutationObserver(function () { colours(); _cc = {}; paint(); })
      .observe(document.documentElement,
        { attributes: true, attributeFilter: ["data-theme"] });

    function rgba(hex, a) {
      var h = hex.replace("#", "");
      if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
      var n = parseInt(h, 16);
      return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," +
        (n & 255) + "," + a.toFixed(3) + ")";
    }

    var W = 0, H = 0, dpr = 1, R = 0, S = 1, yaw = 0.5, pitch = -0.3;
    /* the reader's own turn (drag) rides on top of the descent's camera */
    var offYaw = 0, offPitch = 0, curDoc = -1;
    /* the camera may tip to just short of the pole: the placement puts real
       documents there (the lattice's first point is the pole itself), and a
       camera that cannot face them cannot keep the descent's promise */
    var PITCH_MAX = Math.PI / 2 - 0.02;
    /* The light: a halo outside the limb, the way the Atlas page's
       silhouette is drawn, and a broader, fainter one on the ground behind.
       Both sit outside the disc on purpose: a gradient laid over the marks
       would darken the ground every mark is measured against. Lighting,
       not data; data-light="off" removes it. */
    var lit = host.getAttribute("data-light") !== "off";
    function size() {
      var r = host.getBoundingClientRect();
      dpr = Math.min(2, window.devicePixelRatio || 1);
      /* The host is a real box now. It used to be styled by nothing at
         all, so getBoundingClientRect returned a height of zero, this
         floor caught it, and a 140px sphere was drawn in the middle of a
         1,168px canvas. The floor stays as a floor and is no longer the
         thing deciding the size. */
      W = Math.max(160, r.width);
      H = Math.max(160, r.height);
      cv.width = Math.round(W * dpr);
      cv.height = Math.round(H * dpr);
      cv.style.width = W + "px";
      cv.style.height = H + "px";
      R = Math.min(W, H) * (+host.getAttribute("data-fill") || 0.44);
      /* The marks were drawn for a 350px box (R = 154). At hero scale the
         same rule is drawn proportionally, so a bigger sphere is the same
         picture larger and not the same dots further apart. */
      S = Math.max(1, R / 154);
    }

    /* The depth alpha is quantised to twelve steps and the colour strings
       cached, because building 1,247 rgba strings per frame was most of the
       frame, and a twelfth of the alpha range is invisible at this size. */
    var _cc = {};
    function tone(k, q) {
      var key = k + q;
      var s = _cc[key];
      if (s) return s;
      var a = 0.08 + 0.72 * (q / 12);
      s = k === "c" ? rgba(C.c, a)
        : k === "t" ? rgba(C.t, a)
        : k === "p" ? rgba(C.i, a * 0.55)
        : rgba(C.i, a);
      return (_cc[key] = s);
    }
    /* Every mark's screen position and depth from the last paint, kept so a
       pointer can be matched to a mark without projecting the sphere again. */
    var SX = new Float32Array(pts.length), SY = new Float32Array(pts.length),
        SZ = new Float32Array(pts.length);
    var cx = 0, cy = 0, _cy1 = 1, _sy1 = 0, _cp1 = 1, _sp1 = 0;
    function project(v) {
      var x1 = v[0] * _cy1 + v[2] * _sy1;
      var z1 = -v[0] * _sy1 + v[2] * _cy1;
      var y2 = v[1] * _cp1 - z1 * _sp1;
      var z2 = v[1] * _sp1 + z1 * _cp1;
      return [cx + x1 * R, cy - y2 * R, z2];
    }
    function nrm(v) {
      var l = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) || 1;
      return [v[0] / l, v[1] / l, v[2] / l];
    }
    /* A chord between two documents the corpus links: the great circle
       between their centroids, with a tick at 0.72 of the way toward the
       document being linked, so a mutual pair reads as one chord ticked at
       both ends. The Atlas draws the same chord the same way. */
    function chordTick(A, B, om, so, t) {
      var k1 = Math.sin((1 - t) * om) / so, k2 = Math.sin(t * om) / so;
      var k3 = Math.sin((1 - t - 0.02) * om) / so, k4 = Math.sin((t + 0.02) * om) / so;
      var s = project([A[0] * k1 + B[0] * k2, A[1] * k1 + B[1] * k2, A[2] * k1 + B[2] * k2]);
      if (s[2] < -0.02) return;
      var s2 = project([A[0] * k3 + B[0] * k4, A[1] * k3 + B[1] * k4, A[2] * k3 + B[2] * k4]);
      var dx = s2[0] - s[0], dy = s2[1] - s[1];
      var dl = Math.sqrt(dx * dx + dy * dy) || 1;
      var px = -dy / dl * 4 * Math.max(1, S * 0.8), py = dx / dl * 4 * Math.max(1, S * 0.8);
      ctx.beginPath();
      ctx.moveTo(s[0] - px, s[1] - py); ctx.lineTo(s[0] + px, s[1] + py);
      ctx.strokeStyle = rgba(C.l, 0.95);
      ctx.lineWidth = 1.2;
      ctx.stroke();
    }
    function drawChord(a, b, tickAB, tickBA) {
      var A = nrm(a.p), B = nrm(b.p);
      var dot = Math.max(-1, Math.min(1, A[0] * B[0] + A[1] * B[1] + A[2] * B[2]));
      var om = Math.acos(dot), so = Math.sin(om) || 1e-6;
      ctx.strokeStyle = rgba(C.l, 0.85);
      ctx.lineWidth = 1.25;
      var started = false, seen = false;
      ctx.beginPath();
      for (var i = 0; i <= 48; i++) {
        var t = i / 48;
        var k1 = Math.sin((1 - t) * om) / so, k2 = Math.sin(t * om) / so;
        var s = project([A[0] * k1 + B[0] * k2, A[1] * k1 + B[1] * k2, A[2] * k1 + B[2] * k2]);
        if (s[2] < -0.02) { started = false; continue; }
        seen = true;
        if (!started) { ctx.moveTo(s[0], s[1]); started = true; }
        else ctx.lineTo(s[0], s[1]);
      }
      ctx.stroke();
      if (tickAB) chordTick(A, B, om, so, 0.72);
      if (tickBA) chordTick(A, B, om, so, 0.28);
      return seen;
    }
    var hover = -1;
    function paint() {
      cx = W / 2; cy = H / 2;
      _cy1 = Math.cos(yaw); _sy1 = Math.sin(yaw);
      _cp1 = Math.cos(pitch); _sp1 = Math.sin(pitch);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);
      if (lit) {
        var isDark = dark();
        /* fades to nothing at the box edge, so the canvas boundary never
           shows as a line through the light */
        var edge = Math.min(W, H) / 2;
        var g0 = ctx.createRadialGradient(cx, cy, R * 1.02, cx, cy, Math.max(R * 1.05, edge));
        g0.addColorStop(0, rgba(C.i, isDark ? 0.09 : 0.05));
        g0.addColorStop(0.55, rgba(C.i, isDark ? 0.03 : 0.015));
        g0.addColorStop(1, rgba(C.i, 0));
        ctx.fillStyle = g0;
        ctx.fillRect(0, 0, W, H);
        var g1 = ctx.createRadialGradient(cx, cy, R, cx, cy, R * 1.13);
        g1.addColorStop(0, rgba(C.e, isDark ? 0.22 : 0.14));
        g1.addColorStop(0.45, rgba(C.e, isDark ? 0.07 : 0.04));
        g1.addColorStop(1, rgba(C.e, 0));
        ctx.fillStyle = g1;
        ctx.beginPath();
        ctx.arc(cx, cy, R * 1.13, 0, Math.PI * 2);
        ctx.arc(cx, cy, R, 0, Math.PI * 2, true);
        ctx.fill();
      }
      ctx.beginPath();
      ctx.arc(cx, cy, R, 0, Math.PI * 2);
      ctx.strokeStyle = rgba(lit ? C.e : C.r, 0.6);
      ctx.lineWidth = 1;
      ctx.stroke();
      /* the document under the pointer: its marks come forward, the rest
         hold; the chords its prose records are drawn under the marks */
      var hd = hover >= 0 && own.length ? own[hover] : curDoc;
      var drawn = 0;
      if (hd >= 0 && docs[hd]) {
        var D = docs[hd];
        for (var lc = 0; lc < D.lk.length; lc++) {
          if (drawChord(D, D.lk[lc].g, D.lk[lc].out, D.lk[lc].into)) drawn++;
        }
      }
      /* the sphere says what it is showing: the chords with a visible
         segment in this paint, readable by anything that wants to check */
      if (hd >= 0) host.setAttribute("data-chords", drawn); else host.removeAttribute("data-chords");
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i];
        var x1 = p.x * _cy1 + p.z * _sy1;
        var z1 = -p.x * _sy1 + p.z * _cy1;
        var y2 = p.y * _cp1 - z1 * _sp1;
        var z2 = p.y * _sp1 + z1 * _cp1;
        var sx = cx + x1 * R, sy = cy - y2 * R;
        SX[i] = sx; SY[i] = sy; SZ[i] = z2;
        var t = (z2 + 1) / 2;
        var q = (t * 12) | 0;
        var rad = (BAND_R[p.b] + 1.5 * t) * S;
        var kin = hd >= 0 && own[i] === hd;
        if (kin) { q = Math.min(12, q + 4); }
        if (i === hover) rad += 2.4;
        ctx.beginPath();
        ctx.arc(sx, sy, rad, 0, Math.PI * 2);
        if (p.k === "c") {
          ctx.strokeStyle = tone("c", q);
          ctx.lineWidth = Math.max(1, 0.9 * S);
          ctx.stroke();
        } else {
          ctx.fillStyle = tone(p.k, q);
          ctx.fill();
        }
        if (i === hover) {
          ctx.beginPath();
          ctx.arc(sx, sy, rad + 4.5, 0, Math.PI * 2);
          ctx.strokeStyle = rgba(C.k, 0.6); ctx.lineWidth = 1; ctx.stroke();
        }
      }
    }
    /* the nearest front-facing mark within reach of the pointer */
    function hit(mx, my) {
      var best = -1, bd = 16 * 16;
      for (var i = 0; i < pts.length; i++) {
        if (SZ[i] <= 0) continue;
        var dx = SX[i] - mx, dy = SY[i] - my, d = dx * dx + dy * dy;
        if (d < bd) { bd = d; best = i; }
      }
      return best;
    }
    function placeCard() {
      if (!card || hover < 0) return;
      var w = card.offsetWidth || 240, h = card.offsetHeight || 50;
      var x = SX[hover] + 16, y = SY[hover] - h / 2;
      if (x + w > W - 4) x = SX[hover] - w - 16;
      /* never off the box: a mark near the limb puts the card beside the
         sphere on whichever side has room, clamped inside the canvas */
      x = Math.max(4, Math.min(W - w - 4, x));
      y = Math.max(4, Math.min(H - h - 4, y));
      card.style.transform = "translate(" + Math.round(x) + "px," + Math.round(y) + "px)";
    }
    function setHover(i, lock) {
      locked = !!lock && i >= 0;
      if (i === hover) { if (card && i >= 0) card.hidden = false; return; }
      hover = i;
      var hd = i >= 0 && own.length ? own[i] : -1;
      if (hd < 0 || !docs[hd]) {
        hover = -1;
        if (card) card.hidden = true;
        host.removeAttribute("data-doc");
        host.removeAttribute("data-locked");
        host.style.cursor = fine ? "grab" : "";
        paint();
        return;
      }
      var D = docs[hd], out = 0, into = 0;
      for (var li = 0; li < D.lk.length; li++) { if (D.lk[li].out) out++; if (D.lk[li].into) into++; }
      if (cardT) { cardT.textContent = D.t; if (D.u) cardT.setAttribute("href", D.u); }
      if (cardD) {
        cardD.textContent = D.k + "  \u00b7  " + D.marks + (D.marks === 1 ? " section" : " sections") + "  \u00b7  ";
        var lk = document.createElement("span");
        lk.className = "gc-l";
        lk.textContent = (out ? "links " + out : "") + (out && into ? "  \u00b7  " : "") +
          (into ? "linked by " + into : "") + (!out && !into ? "no links recorded" : "");
        cardD.appendChild(lk);
      }
      if (card) card.hidden = false;
      host.setAttribute("data-doc", D.t);
      if (locked) host.setAttribute("data-locked", "1"); else host.removeAttribute("data-locked");
      host.style.cursor = "pointer";
      paint();
      placeCard();
    }

    /* Idle contract, the same one the Atlas keeps: the sphere paints once
       when the main thread is free and then draws nothing until it is
       turned. A drag carries a little inertia that drains to zero within a
       second, so the loop reschedules only while something is moving. The
       old version turned by itself for as long as it was on screen, sixty
       frames a second on a page whose claim is that nothing moves without a
       reason. On a touch screen at the top of the page a drag surface would
       eat the scroll, so there the sphere holds still and a tap opens the
       Atlas. */
    var raf = 0, lastT = 0, vy = 0, vp = 0, dragT = false, lxT = 0, lyT = 0, movedT = 0;
    function kick() { if (!raf) raf = requestAnimationFrame(frame); }
    function frame(now) {
      raf = 0;
      var dt = lastT ? Math.min(0.05, (now - lastT) / 1000) : 0.016;
      lastT = now;
      if (!dragT) {
        yaw += vy * dt; offYaw += vy * dt;
        pitch = Math.max(-PITCH_MAX, Math.min(PITCH_MAX, pitch + vp * dt)); offPitch += vp * dt;
        vy *= 0.94; vp *= 0.94;
        if (Math.abs(vy) < 0.0006) vy = 0;
        if (Math.abs(vp) < 0.0006) vp = 0;
      }
      paint();
      if (dragT || vy !== 0 || vp !== 0) kick(); else lastT = 0;
    }

    /* First paint waits for an idle main thread: the home page is the LCP
       surface and the sphere must not cost it. The box is sized by CSS, so
       nothing shifts when the canvas fills in. */
    function bootTeaser() { size(); paint(); }
    if ("requestIdleCallback" in window) {
      requestIdleCallback(bootTeaser, { timeout: 1500 });
    } else {
      setTimeout(bootTeaser, 250);
    }
    var t0;
    window.addEventListener("resize", function () {
      clearTimeout(t0);
      t0 = setTimeout(function () { size(); paint(); }, 140);
    });
    if (window.matchMedia && window.matchMedia("(pointer:fine)").matches) {
      cv.addEventListener("pointerdown", function (e) {
        dragT = true; movedT = 0; vy = vp = 0; lxT = e.clientX; lyT = e.clientY;
        try { cv.setPointerCapture(e.pointerId); } catch (x) {}
        host.style.cursor = "grabbing";
        kick();
      });
      cv.addEventListener("pointermove", function (e) {
        if (!dragT) {
          /* pointing, not turning: match the pointer to a mark and draw
             what its document records. One paint per change, no loop. */
          if (!docs.length) return;
          var rr = cv.getBoundingClientRect();
          setHover(hit(e.clientX - rr.left, e.clientY - rr.top));
          return;
        }
        if (hover >= 0) setHover(-1);
        var dx = e.clientX - lxT, dy = e.clientY - lyT;
        movedT += Math.abs(dx) + Math.abs(dy);
        yaw += dx * 0.006; offYaw += dx * 0.006;
        pitch = Math.max(-PITCH_MAX, Math.min(PITCH_MAX, pitch + dy * 0.005)); offPitch += dy * 0.005;
        vy = dx * 0.09; vp = dy * 0.07;
        lxT = e.clientX; lyT = e.clientY;
        kick();
      });
      var endT = function (e) {
        if (!dragT) return;
        dragT = false; host.style.cursor = "grab";
        try { cv.releasePointerCapture(e.pointerId); } catch (x) {}
        kick();
      };
      cv.addEventListener("pointerup", endT);
      cv.addEventListener("pointercancel", endT);
      /* leaving the canvas for the card keeps the card, so its link can be reached */
      cv.addEventListener("pointerleave", function (e) {
        if (dragT || locked) return;
        if (e.relatedTarget && card && card.contains(e.relatedTarget)) return;
        setHover(-1);
      });
      if (card) card.addEventListener("pointerleave", function (e) {
        if (locked) return;
        if (e.relatedTarget === cv) return;
        setHover(-1);
      });
    }
    /* ---- the descent ----------------------------------------------
       The statement's featured rows are documents on the sphere. As each
       row reaches the reading line the camera turns to face that document's
       centroid (the same rotation the Atlas uses to face a mark), its marks
       come forward and the chords its prose records are drawn. The camera is
       a function of the scroll position and nothing else: one frame per
       scroll event, none while the reader is still. With reduced motion the
       camera holds and only the lighting follows the rows. */
    var wrap = host.closest(".descent-globe");
    var rowsD = [];
    (function () {
      if (!docs.length) return;
      var byUrl = {};
      docs.forEach(function (d, i) { byUrl[d.u] = i; });
      var trs = document.querySelectorAll("#statement table.st tr.item");
      for (var r = 0; r < trs.length; r++) {
        var a = trs[r].querySelector("th a");
        var u = a && a.getAttribute("href");
        if (u && (u in byUrl)) rowsD.push({ el: trs[r], doc: byUrl[u] });
      }
    })();
    var homeYaw = yaw, homePitch = pitch;
    var facingEl = wrap && wrap.querySelector(".facing");
    var reducedM = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    function facingOf(v) {
      var n = nrm(v);
      return { yaw: Math.atan2(-n[0], n[2]), pitch: Math.atan2(n[1], Math.sqrt(n[0] * n[0] + n[2] * n[2])) };
    }
    function shortest(a, b) {
      var d = (b - a) % (Math.PI * 2);
      if (d > Math.PI) d -= Math.PI * 2;
      if (d < -Math.PI) d += Math.PI * 2;
      return a + d;
    }
    function smooth(t) { t = Math.max(0, Math.min(1, t)); return t * t * (3 - 2 * t); }
    var sraf = 0, lastStuck = false;
    function descend() {
      sraf = 0;
      if (!rowsD.length) return;
      var hr = host.getBoundingClientRect();
      /* the reading line: mid-viewport, or just under the sphere when it is
         pinned above the rows on a phone */
      var line = Math.min(innerHeight * 0.5, hr.bottom + 40);
      var y = window.scrollY || document.documentElement.scrollTop;
      var anchors = [];
      for (var i = 0; i < rowsD.length; i++) {
        var rr = rowsD[i].el.getBoundingClientRect();
        var f = facingOf(docs[rowsD[i].doc].p);
        anchors.push({ s: y + rr.top + rr.height / 2 - line, yaw: f.yaw, pitch: f.pitch, doc: rowsD[i].doc });
      }
      var byaw, bpitch, cur = -1;
      if (y <= 0 || y < anchors[0].s - Math.max(1, anchors[0].s)) {
        byaw = homeYaw; bpitch = homePitch;
      } else if (y < anchors[0].s) {
        var t0 = smooth(y / anchors[0].s);
        byaw = homeYaw + (shortest(homeYaw, anchors[0].yaw) - homeYaw) * t0;
        bpitch = homePitch + (anchors[0].pitch - homePitch) * t0;
      } else {
        var k = anchors.length - 1;
        for (var a = 0; a < anchors.length - 1; a++) { if (y < anchors[a + 1].s) { k = a; break; } }
        if (k >= anchors.length - 1) { byaw = anchors[k].yaw; bpitch = anchors[k].pitch; }
        else {
          var t1 = smooth((y - anchors[k].s) / Math.max(1, anchors[k + 1].s - anchors[k].s));
          byaw = anchors[k].yaw + (shortest(anchors[k].yaw, anchors[k + 1].yaw) - anchors[k].yaw) * t1;
          bpitch = anchors[k].pitch + (anchors[k + 1].pitch - anchors[k].pitch) * t1;
        }
      }
      /* the row nearest the line is the document faced, once the first row
         is within half a row of it */
      var bestD = Infinity, gap = anchors.length > 1 ? (anchors[1].s - anchors[0].s) : 400;
      for (var c = 0; c < anchors.length; c++) {
        var d = Math.abs(y - anchors[c].s);
        if (d < bestD) { bestD = d; cur = c; }
      }
      if (bestD > gap * 0.75) cur = -1;
      var changed = false;
      if (!reducedM) {
        var ny = byaw + offYaw, np = Math.max(-PITCH_MAX, Math.min(PITCH_MAX, bpitch + offPitch));
        if (Math.abs(ny - yaw) > 1e-4 || Math.abs(np - pitch) > 1e-4) { yaw = ny; pitch = np; changed = true; }
      }
      var nd = cur >= 0 ? anchors[cur].doc : -1;
      if (nd !== curDoc) {
        curDoc = nd; changed = true;
        for (var q = 0; q < rowsD.length; q++) rowsD[q].el.classList.toggle("cur", rowsD[q].doc === curDoc);
        if (facingEl) {
          facingEl.textContent = "";
          if (curDoc >= 0) {
            facingEl.appendChild(document.createTextNode("Facing "));
            var bb = document.createElement("b"); bb.textContent = docs[curDoc].t; facingEl.appendChild(bb);
          }
        }
        if (curDoc >= 0) host.setAttribute("data-facing", docs[curDoc].t); else host.removeAttribute("data-facing");
      }
      /* pinned on a phone: the sphere steps back to make room for the rows */
      if (wrap) {
        var top = parseFloat(getComputedStyle(wrap).top) || 0;
        var stuck = y > 0 && wrap.getBoundingClientRect().top <= top + 1;
        if (stuck !== lastStuck) { lastStuck = stuck; wrap.classList.toggle("stuck", stuck); }
      }
      host.setAttribute("data-yaw", yaw.toFixed(3));
      host.setAttribute("data-pitch", pitch.toFixed(3));
      if (changed && !dragT) paint();
    }
    if (rowsD.length) {
      window.addEventListener("scroll", function () { if (!sraf) sraf = requestAnimationFrame(descend); }, { passive: true });
      window.addEventListener("resize", function () { if (!sraf) sraf = requestAnimationFrame(descend); });
      /* the box changes size when it pins on a phone; the canvas follows */
      if ("ResizeObserver" in window) {
        new ResizeObserver(function () { size(); paint(); }).observe(host);
      }
      if ("requestIdleCallback" in window) requestIdleCallback(descend, { timeout: 1500 });
      else setTimeout(descend, 300);
    }
    host.addEventListener("click", function (e) {
      if (movedT > 8) { movedT = 0; return; }
      if (!fine) {
        /* touch: a tap on a mark locks its document and draws what it
           records; a tap on the void clears the lock, or with nothing
           locked opens the Atlas. Each tap paints once. */
        var rr = cv.getBoundingClientRect();
        var i = docs.length ? hit(e.clientX - rr.left, e.clientY - rr.top) : -1;
        if (i >= 0) { setHover(i, true); return; }
        if (hover >= 0) { setHover(-1); return; }
        window.location.href = "atlas.html";
        return;
      }
      /* a fine pointer: a mark opens its document; the void opens the Atlas */
      var hd = hover >= 0 && own.length ? own[hover] : -1;
      window.location.href = (hd >= 0 && docs[hd] && docs[hd].u) ? docs[hd].u : "atlas.html";
    });
  })();

/* ------------------------------------------------------------ trail ----
   Which passages this browser has opened. The atlas reads it and rings
   them; the record lives in localStorage and never leaves the machine. */
(function () {
  try {
    var k = "atlas.trail";
    var u = location.pathname.split("/").pop() || "index.html";
    if (u === "atlas.html" || u === "admin.html") return;
    var t = JSON.parse(localStorage.getItem(k) || "{}");
    var key = u + location.hash;
    if (t[key] || Object.keys(t).length < 500) {
      t[key] = (t[key] || 0) + 1;
      localStorage.setItem(k, JSON.stringify(t));
    }
  } catch (e) {}
})();

/* ------------------------------------------------ offline, site-wide ----
   Every shell page registers the worker, so the offline claim does not
   depend on which page a reader arrived at. The colophon's two controls
   talk to it over postMessage: one fetches the build's offline manifest and
   stores the whole site, the other removes that copy. */
(function () {
  if (!("serviceWorker" in navigator) || location.protocol.indexOf("http") !== 0) return;
  /* after load and an idle beat, so the worker's first install never taxes
     the paint the budgets are measured on */
  addEventListener("load", function () {
    setTimeout(function () {
      navigator.serviceWorker.register("sw.js").catch(function () {});
    }, 6000);
  });

  var save = document.getElementById("offline-save");
  var drop = document.getElementById("offline-drop");
  var status = document.getElementById("offline-status");
  if (!save || !drop || !status) return;

  function say(t) { status.textContent = t; }
  navigator.serviceWorker.addEventListener("message", function (e) {
    var m = e.data || {};
    if (m.type === "cache-all-progress") {
      say("Saving… " + m.done + " of " + m.total + " files");
    } else if (m.type === "cache-all-done") {
      if (m.failed === -1) { say("Could not read the file list; try again online."); return; }
      say(m.failed
        ? "Saved " + m.ok + " of " + m.total + " files; " + m.failed + " failed. Press again to retry the rest."
        : "The whole site is on this phone: " + m.ok + " files. It refreshes itself when opened online.");
      save.disabled = false;
    } else if (m.type === "drop-all-done") {
      say("Offline copy removed. Pages you visit will still cache as you read.");
      drop.disabled = false;
    }
  });
  save.addEventListener("click", function () {
    save.disabled = true;
    say("Saving…");
    /* ask the browser to protect this storage from being reclaimed; on an
       installed app this is usually granted, and it is what makes the copy
       durable rather than merely cached */
    if (navigator.storage && navigator.storage.persist) {
      navigator.storage.persist().catch(function () {});
    }
    navigator.serviceWorker.ready.then(function (reg) {
      if (reg.active) reg.active.postMessage({ type: "cache-all" });
      else { say("The offline worker is still starting; try again in a moment."); save.disabled = false; }
    });
  });
  drop.addEventListener("click", function () {
    drop.disabled = true;
    navigator.serviceWorker.ready.then(function (reg) {
      if (reg.active) reg.active.postMessage({ type: "drop-all" });
      else drop.disabled = false;
    });
  });
})();
