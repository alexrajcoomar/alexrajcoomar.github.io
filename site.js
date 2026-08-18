/* ============================================================
   Alex Rajcoomar — portfolio
   One script for every page. Hand-written, no dependencies.

   Everything here is an enhancement: with JavaScript off the
   pages are still complete documents and every link still works.
   ============================================================ */
(function () {
  "use strict";

  var reduced = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

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

  /* ------------------------------------------- library filtering ---
     Progressive: the full list is in the DOM and printed. This only
     hides rows. */
  var q = document.getElementById("q");
  var list = document.getElementById("list");
  var chips = document.getElementById("chips");
  var note = document.getElementById("resultnote");
  var empty = document.getElementById("noresults");
  if (list) {
    var rows = [].slice.call(list.children);
    var filter = "all";
    function apply() {
      var term = (q && q.value || "").trim().toLowerCase();
      var shown = 0;
      rows.forEach(function (li) {
        var okKind = filter === "all" || li.getAttribute("data-kind") === filter;
        var okTerm = !term || (li.getAttribute("data-search") || "").indexOf(term) > -1;
        var on = okKind && okTerm;
        li.hidden = !on;
        if (on) shown++;
      });
      var one = shown === 1;
      if (note) {
        var what = filter === "all" ? (one ? "piece" : "pieces")
          : filter === "tool" ? (one ? "tool" : "tools")
          : filter === "essay" ? (one ? "essay" : "essays")
          : (one ? "reference" : "references");
        note.textContent = shown === rows.length
          ? "Showing all " + rows.length + " pieces."
          : shown === 0
            ? "Nothing matches" + (term ? ' "' + q.value.trim() + '"' : " that filter") + "."
            : "Showing " + shown + " " + what + (term ? ' matching "' + q.value.trim() + '".' : ".");
      }
      /* An empty list with no message reads as a broken page. */
      if (empty) empty.hidden = shown !== 0;
    }
    if (q) q.addEventListener("input", apply);
    if (chips) {
      chips.addEventListener("click", function (e) {
        var b = e.target.closest(".chip");
        if (!b) return;
        filter = b.getAttribute("data-f");
        [].slice.call(chips.querySelectorAll(".chip")).forEach(function (c) {
          c.setAttribute("aria-pressed", c === b ? "true" : "false");
        });
        apply();
      });
    }
  }

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
      var order = ["Essay", "Reference", "Tool"], seen = {}, n = 0;
      order.concat([""]).forEach(function (kind) {
        var band = hits.filter(function (r) {
          return kind ? r.it.k === kind : order.indexOf(r.it.k) === -1;
        });
        if (!band.length) return;
        var head = el("li", "cmdk-group");
        head.setAttribute("role", "presentation");
        head.textContent = kind ? (kind === "Essay" ? "Essays"
                                 : kind === "Tool" ? "Tools" : "References")
                                : "Other";
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
    function open() {
      lastFocus = document.activeElement;
      pal.hidden = false;
      input.value = "";
      render();
      input.focus();
      document.body.style.overflow = "hidden";
    }
    function close() {
      pal.hidden = true;
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
      } else if (e.key === "/" && !typing && pal.hidden) {
        e.preventDefault(); open();
      } else if (e.key === "?" && !typing && pal.hidden) {
        e.preventDefault(); keys(true);
      } else if (!typing && pal.hidden && (e.key === "g" || e.key === "G")) {
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
  function keys(on) {
    var sheet = document.getElementById("keysheet");
    if (!sheet) return;
    sheet.hidden = !on;
    document.body.style.overflow = on ? "hidden" : "";
    if (on) {
      var c = sheet.querySelector(".close");
      if (c) c.focus();
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
    });
    var opener = document.getElementById("keysbtn");
    if (opener) opener.addEventListener("click", function () { keys(true); });
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
        noteEl = document.getElementById("resultnote"),
        none = document.getElementById("noresults"),
        f = "all", total = 0;
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
    if (chipsEl) chipsEl.addEventListener("click", function (e) {
      var b = e.target.closest(".chip"); if (!b) return;
      f = b.getAttribute("data-f");
      [].slice.call(chipsEl.querySelectorAll(".chip")).forEach(function (c) {
        c.setAttribute("aria-pressed", c === b ? "true" : "false");
      });
      run();
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
    }
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        var j = jobs.filter(function (x) { return x.el === e.target; })[0];
        if (j) { animate(j); io.unobserve(e.target); }
      });
    }, { threshold: 0.4 });
    jobs.forEach(function (j) { paint(j, 0); io.observe(j.el); });
    /* If something goes wrong with the observer the numbers must not be
       left at zero, which would be a lie rather than an animation. */
    setTimeout(function () { jobs.forEach(function (j) { if (!j.done) { j.done = true; paint(j, j.to); } }); }, 4000);
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
      requestAnimationFrame(function () { bar.style.width = (w / widest * 100).toFixed(1) + "%"; });
    }
    function clear() {
      /* a short hold, so crossing a gap between two rows does not make
         the rail flicker back to its resting state */
      hold = setTimeout(function () {
        out.hidden = true; rest.hidden = false; bar.style.width = "0";
      }, 260);
    }
    rows.forEach(function (r) {
      r.addEventListener("mouseenter", function () { show(r); });
      r.addEventListener("focus", function () { show(r); });
      r.addEventListener("mouseleave", clear);
      r.addEventListener("blur", clear);
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
