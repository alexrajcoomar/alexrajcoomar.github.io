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
      var t = input.value.trim().toLowerCase();
      var hits = work.map(function (it) { return { it: it, s: score(it, t) }; })
                     .filter(function (r) { return r.s > 0; })
                     .sort(function (a, b) { return b.s - a.s; })
                     .slice(0, 9);
      if (!hits.length) {
        results.innerHTML = '<li class="cmdk-empty">Nothing matches that. Try a course code, or a word from a title.</li>';
        items = [];
        return;
      }
      results.innerHTML = hits.map(function (r, n) {
        var it = r.it;
        return '<li role="option" id="cmdk-o' + n + '" aria-selected="' + (n === 0) + '"' +
          (n === 0 ? ' class="on"' : "") + '><a href="' + it.u + '">' +
          '<span><span class="t">' + it.t + "</span>" +
          (it.s ? '<span class="s"> — ' + it.s + "</span>" : "") + "</span>" +
          '<span class="s">' + it.k + (it.c ? " &middot; " + it.c : "") + "</span></a></li>";
      }).join("");
      items = [].slice.call(results.children);
      cur = 0;
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
      }
    });
  }

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
  })();
})();
