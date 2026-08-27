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
    var cur = 0, items = [], lastFocus = null;

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

    function open() {
      lastFocus = document.activeElement;
      pal.hidden = false;
      input.setAttribute("aria-expanded", "true");
      input.value = "";
      render();
      input.focus();
      document.body.style.overflow = "hidden";
    }
    function close() {
      pal.hidden = true;
      input.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
    if (openBtn) openBtn.addEventListener("click", open);
    input.addEventListener("input", render);
    pal.addEventListener("mousedown", function (e) { if (e.target === pal) close(); });
    pal.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { e.preventDefault(); close(); }
      else if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
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
        e.preventDefault(); pal.hidden ? open() : close();
      } else if (typing || !pal.hidden || !singlesOn()) {
        /* single-key routes only: the modified Cmd/Ctrl+K above stays on */
      } else if (e.key === "/") {
        e.preventDefault(); open();
      } else if (e.key === "?") {
        e.preventDefault(); keys(true);
      } else if (e.key === "g" || e.key === "G") {
        /* g then a letter: the two-stroke jump every reader of a long site
           already knows from mail clients and code hosts. */
        goArmed = Date.now();
      } else if (!typing && pal.hidden && goArmed && Date.now() - goArmed < 1200) {
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
  var keysLastFocus = null;
  function keys(on) {
    var sheet = document.getElementById("keysheet");
    if (!sheet) return;
    if (on) keysLastFocus = document.activeElement;
    sheet.hidden = !on;
    document.body.style.overflow = on ? "hidden" : "";
    if (on) {
      var c = sheet.querySelector(".close");
      if (c) c.focus();
    } else if (keysLastFocus && keysLastFocus.focus) {
      /* aria-modal promised a modal; a modal gives focus back */
      keysLastFocus.focus();
    }
  }
  (function () {
    var sheet = document.getElementById("keysheet");
    if (!sheet) return;
    sheet.addEventListener("click", function (e) {
      if (e.target === sheet || e.target.closest(".close")) keys(false);
    });
    sheet.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { e.preventDefault(); keys(false); }
      else if (e.key === "Tab") {
        /* aria-modal also promised focus stays inside. The sheet holds a
           checkbox and a button, so the trap walks its own controls. */
        var f = [].slice.call(sheet.querySelectorAll("input, button"));
        if (!f.length) return;
        var first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
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

  /* ------------------------------------------------------ the age --
     The bio states an age, and an age goes stale. The build writes the
     value that is correct on the build date; this recomputes it from the
     date of birth on every load, so the sentence stays true without
     anyone editing it. With JS off the built-in value still reads. */
  [].slice.call(document.querySelectorAll("[data-age]")).forEach(function (el) {
    var p = (el.getAttribute("data-age") || "").split("-");
    if (p.length !== 3) return;
    var y = +p[0], m = +p[1], d = +p[2], now = new Date();
    var age = now.getFullYear() - y;
    var md = (now.getMonth() + 1) * 100 + now.getDate();
    if (md < m * 100 + d) age -= 1;
    if (age > 0 && age < 120) el.textContent = String(age);
  });

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
      var r = [].slice.call(g.querySelectorAll("ol.index > li"));
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
      if (pal && !pal.hidden) return;
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

  /* ------------------------------------------------ counted numerals
     The oversized statistics are the first thing the eye lands on, so
     they count once, on first sight. The text already in the DOM is the
     final value and the format is read back off it, which means the
     printed page and a reader with no JS see the number and nobody
     maintains it twice. */
  (function () {
    var nums = [].slice.call(document.querySelectorAll(".stats b.tnum"));
    if (!nums.length) return;
    var jobs = [];
    nums.forEach(function (el) {
      var raw = (el.textContent || "").trim();
      var m = raw.match(/^([^\d]*)([\d,]+)(.*)$/);
      if (!m) return;
      var target = +m[2].replace(/,/g, "");
      if (!isFinite(target) || target <= 0) return;
      var grouped = m[2].indexOf(",") > -1;
      jobs.push({ el: el, pre: m[1], suf: m[3], to: target, grouped: grouped, done: false });
    });
    if (!jobs.length) return;
    if (reduced || !("IntersectionObserver" in window)) return;   // leave the final value in place

    function paint(j, v) {
      var t = Math.round(v);
      j.el.textContent = j.pre + (j.grouped ? t.toLocaleString("en-CA") : String(t)) + j.suf;
    }
    function animate(j) {
      if (j.done) return; j.done = true;
      var start = 0, dur = 900 + Math.min(600, j.to / 400);
      function step(now) {
        if (!start) start = now;
        var t = Math.min(1, (now - start) / dur);
        /* ease-out cubic: fast enough to feel immediate, slow enough at
           the end that the final digits are readable rather than a blur */
        paint(j, j.to * (1 - Math.pow(1 - t, 3)));
        if (t < 1) requestAnimationFrame(step); else paint(j, j.to);
      }
      requestAnimationFrame(step);
      /* requestAnimationFrame is suspended while a tab is in the background,
         so the animation alone cannot be trusted to leave the number behind.
         A page opened in a background tab was showing 0 for every statistic.
         The value is therefore also written on a plain timer, which keeps
         running, and the animation is only the way it gets there. */
      setTimeout(function () { paint(j, j.to); }, dur + 500);
    }
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        var j = jobs.filter(function (x) { return x.el === e.target; })[0];
        if (j) { animate(j); io.unobserve(e.target); }
      });
    }, { threshold: 0.1, rootMargin: "0px 0px -4% 0px" });
    /* The built value stays in the DOM until the count actually starts:
       a screen reader or a reader arriving mid-page must never find a
       statistic reading zero. The first animation frame takes it from
       there. */
    jobs.forEach(function (j) { io.observe(j.el); });

    /* A number showing zero is a wrong number, not a pending animation, so
       nothing is left waiting on an observer that may never report. This
       sweeps anything already on screen, and after fifteen seconds gives up
       and writes every remaining value in full. */
    var swept = 0;
    (function sweepNums() {
      var left = 0;
      jobs.forEach(function (j) {
        if (j.done) return;
        var r = j.el.getBoundingClientRect();
        var onScreen = r.bottom > 0 && r.top < (window.innerHeight || 0);
        if (onScreen || swept > 14000) { animate(j); io.unobserve(j.el); }
        else left++;
      });
      if (left) { swept += 1000; setTimeout(sweepNums, 1000); }
    })();
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
        "  ·  " + (w / total * 100).toFixed(1) + "% of everything written here";
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

     Mark size follows heading level, as it does on the atlas. The two used
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
      var lvl = mark.length > 1 ? +mark.charAt(1) : 3;
      if (!(lvl >= 1 && lvl <= 4)) lvl = 3;
      var P = { x: +f[0], y: +f[1], z: +f[2], k: mark.charAt(0), l: lvl };
      /* the atlas stands its six tool marks off the sphere; the teaser
         makes the same claim about the same points */
      if (P.k === "t") { P.x *= 1.13; P.y *= 1.13; P.z *= 1.13; }
      pts.push(P);
    }
    if (pts.length < 8) return;

    /* atlas.js draws (0.75 + lv * 0.3) + 2.0 * depth, where lv is
       4 - level. At teaser scale that whole ladder is multiplied by
       0.7 / 1.05, the ratio that leaves a third-level heading exactly
       where it was. Levels 1 to 4 land on 1.10, 0.90, 0.70 and 0.50. */
    var LVL_R = [0, 1.10, 0.90, 0.70, 0.50];

    var cv = document.createElement("canvas");
    cv.setAttribute("aria-hidden", "true");
    host.appendChild(cv);
    var ctx = cv.getContext && cv.getContext("2d");
    if (!ctx) return;

    var C = {};
    function colours() {
      var s = getComputedStyle(document.documentElement);
      C.i = s.getPropertyValue("--accent").trim() || "#14509b";
      C.c = s.getPropertyValue("--ink-3").trim() || "#6f6c63";
      C.t = s.getPropertyValue("--tool").trim() || "#0f6b58";
      C.r = s.getPropertyValue("--rule").trim() || "#ddd9cf";
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

    var W = 0, H = 0, dpr = 1, R = 0, yaw = 0.5, pitch = -0.3;
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
      R = Math.min(W, H) * 0.44;
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
    function paint() {
      var cx = W / 2, cy = H / 2;
      var cyaw = Math.cos(yaw), syaw = Math.sin(yaw);
      var cpit = Math.cos(pitch), spit = Math.sin(pitch);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, W, H);
      ctx.beginPath();
      ctx.arc(cx, cy, R, 0, Math.PI * 2);
      ctx.strokeStyle = rgba(C.r, 0.6);
      ctx.lineWidth = 1;
      ctx.stroke();
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i];
        var x1 = p.x * cyaw + p.z * syaw;
        var z1 = -p.x * syaw + p.z * cyaw;
        var y2 = p.y * cpit - z1 * spit;
        var z2 = p.y * spit + z1 * cpit;
        var t = (z2 + 1) / 2;
        var q = (t * 12) | 0;
        var rad = LVL_R[p.l] + 1.5 * t;
        ctx.beginPath();
        ctx.arc(cx + x1 * R, cy - y2 * R, rad, 0, Math.PI * 2);
        if (p.k === "c") {
          ctx.strokeStyle = tone("c", q);
          ctx.lineWidth = 1;
          ctx.stroke();
        } else {
          ctx.fillStyle = tone(p.k, q);
          ctx.fill();
        }
      }
    }

    var spinning = false, last = 0, skip = false;
    function step(now) {
      if (!spinning) return;
      yaw += Math.min(0.05, (now - last) / 1000) * 0.05;
      last = now;
      /* ambient drift at half rate: the eye cannot tell and the phone can */
      skip = !skip;
      if (!skip) paint();
      requestAnimationFrame(step);
    }

    /* First paint waits for an idle main thread: the home page is the LCP
       surface and the sphere must not cost it. The box is sized by CSS, so
       nothing shifts when the canvas fills in. */
    function bootTeaser() {
      size();
      paint();
      watch();
    }
    if ("requestIdleCallback" in window) {
      requestIdleCallback(bootTeaser, { timeout: 1500 });
    } else {
      setTimeout(bootTeaser, 250);
    }
    function watch() {
    if (!reduced && "IntersectionObserver" in window) {
      /* only turns while it is on screen: a globe spinning in a tab nobody is
         looking at is a battery cost with no reader */
      new IntersectionObserver(function (es) {
        var vis = es[0] && es[0].isIntersecting;
        if (vis && !spinning) {
          spinning = true;
          last = performance.now();
          requestAnimationFrame(step);
        } else if (!vis) {
          spinning = false;
        }
      }, { threshold: 0.05 }).observe(host);
    }
    }
    var t0;
    window.addEventListener("resize", function () {
      clearTimeout(t0);
      t0 = setTimeout(function () { size(); paint(); }, 140);
    });
    /* Draggable where a mouse makes that cheap; on a touch screen at the
       top of the page a drag surface would eat the scroll, so the sphere
       turns by itself there and stays a link. */
    var movedT = 0;
    if (window.matchMedia && window.matchMedia("(pointer:fine)").matches) {
      var dragT = false, lxT = 0, lyT = 0;
      cv.addEventListener("pointerdown", function (e) {
        dragT = true; movedT = 0; lxT = e.clientX; lyT = e.clientY;
        spinning = false;
        try { cv.setPointerCapture(e.pointerId); } catch (x) {}
        host.style.cursor = "grabbing";
      });
      cv.addEventListener("pointermove", function (e) {
        if (!dragT) return;
        var dx = e.clientX - lxT, dy = e.clientY - lyT;
        movedT += Math.abs(dx) + Math.abs(dy);
        yaw += dx * 0.006;
        pitch = Math.max(-1.2, Math.min(1.2, pitch + dy * 0.005));
        lxT = e.clientX; lyT = e.clientY;
        paint();
      });
      cv.addEventListener("pointerup", function () {
        dragT = false; host.style.cursor = "grab";
      });
    }
    host.addEventListener("click", function () {
      if (movedT > 8) { movedT = 0; return; }
      window.location.href = "atlas.html";
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
