/* The reading kit for a long piece (over five thousand words), injected by
   the build inside a marked block, so a piece never carries it by hand.

   Three things, all enhancements: the page reads the same with scripts off.

   1. A section index, built from the same heading anchors the Atlas
      harvests (h2 and h3 with ids), on pages that carry no contents rail of
      their own. It sits as a small panel that opens from a button, tracks
      the section in view, and is skipped where the page already has one.
   2. A reading position: where the reader was on this page, kept in
      localStorage under the page's own name and restored on the next visit
      when the page opens without a hash. Nothing leaves the machine.
   3. Print: before printing, every sticky or fixed element is released to
      static so nothing overlaps the sheet; afterwards it is put back. */
(function () {
  "use strict";
  var doc = document, slug = (location.pathname.split("/").pop() || "index.html").replace(/\.html$/, "");

  /* ---- 1. the section index ---- */
  function hasOwnIndex() {
    if (doc.querySelector(".docbar, .toc, nav.rail, #navlist")) return true;
    var navs = doc.querySelectorAll("nav");
    for (var i = 0; i < navs.length; i++) {
      if (navs[i].querySelectorAll('a[href^="#"]').length >= 5 && !navs[i].id.match(/^__/)) return true;
    }
    return false;
  }
  function buildIndex() {
    if (hasOwnIndex()) return;
    var main = doc.querySelector('main, [role="main"]') || doc.body;
    var heads = [].slice.call(main.querySelectorAll("h2[id], h3[id]")).filter(function (h) {
      return h.textContent.trim().length > 2 && !h.closest("#__rb, #__long-idx, footer, nav");
    });
    if (heads.length < 4) return;
    var wrap = doc.createElement("div");
    wrap.id = "__long-idx";
    wrap.setAttribute("data-count", heads.length);
    var btn = doc.createElement("button");
    btn.type = "button"; btn.id = "__long-btn"; btn.setAttribute("aria-expanded", "false"); btn.setAttribute("aria-controls", "__long-list");
    btn.textContent = "Sections";
    var panel = doc.createElement("nav");
    panel.id = "__long-list"; panel.setAttribute("aria-label", "Sections of this piece"); panel.hidden = true;
    var ol = doc.createElement("ol");
    heads.forEach(function (h) {
      var li = doc.createElement("li"); li.className = "l" + h.tagName.slice(1);
      var a = doc.createElement("a"); a.href = "#" + h.id; a.textContent = h.textContent.trim().replace(/\s+/g, " ");
      li.appendChild(a); ol.appendChild(li);
    });
    panel.appendChild(ol);
    wrap.appendChild(btn); wrap.appendChild(panel);
    doc.body.appendChild(wrap);
    function open(o) { panel.hidden = !o; btn.setAttribute("aria-expanded", String(o)); wrap.classList.toggle("open", o); }
    btn.addEventListener("click", function () { open(panel.hidden); });
    panel.addEventListener("click", function (e) { if (e.target.closest("a")) open(false); });
    doc.addEventListener("keydown", function (e) { if (e.key === "Escape" && !panel.hidden) { open(false); btn.focus(); } });
    /* the section in view, on one throttled scroll handler */
    var links = [].slice.call(ol.querySelectorAll("a")), cur = -1, ticking = false;
    function run() {
      ticking = false;
      var best = -1;
      for (var i = 0; i < heads.length; i++) { if (heads[i].getBoundingClientRect().top < 140) best = i; else break; }
      if (best !== cur) {
        if (cur > -1) links[cur].removeAttribute("aria-current");
        cur = best;
        if (cur > -1) links[cur].setAttribute("aria-current", "true");
        btn.textContent = cur > -1 ? "Sections · " + (cur + 1) + " of " + heads.length : "Sections";
      }
    }
    function queue() { if (!ticking) { ticking = true; requestAnimationFrame(run); } }
    addEventListener("scroll", queue, { passive: true }); run();
  }

  /* ---- 2. the reading position ---- */
  function position() {
    var key = "read." + slug, saved = null;
    try { saved = JSON.parse(localStorage.getItem(key) || "null"); } catch (e) {}
    if (saved && !location.hash && saved.y > 400 && Date.now() - saved.t < 30 * 864e5
        && Math.abs((doc.documentElement.scrollHeight || 0) - saved.h) < saved.h * 0.15) {
      requestAnimationFrame(function () { scrollTo(0, saved.y); });
    }
    var t = null;
    addEventListener("scroll", function () {
      if (t) return;
      t = setTimeout(function () {
        t = null;
        try { localStorage.setItem(key, JSON.stringify({ y: Math.round(scrollY), h: doc.documentElement.scrollHeight, t: Date.now() })); } catch (e) {}
      }, 400);
    }, { passive: true });
  }

  /* ---- 3. print releases sticky and fixed elements ---- */
  function print() {
    var released = [];
    addEventListener("beforeprint", function () {
      released = [];
      [].slice.call(doc.body.querySelectorAll("*")).forEach(function (el) {
        var p = getComputedStyle(el).position;
        if (p === "sticky" || p === "fixed") { released.push([el, el.style.position]); el.style.position = "static"; }
      });
      [].slice.call(doc.querySelectorAll("details")).forEach(function (d) { d.dataset.__was = d.open ? "1" : ""; d.open = true; });
    });
    addEventListener("afterprint", function () {
      released.forEach(function (r) { r[0].style.position = r[1]; });
      [].slice.call(doc.querySelectorAll("details")).forEach(function (d) { if ("__was" in d.dataset) { d.open = d.dataset.__was === "1"; delete d.dataset.__was; } });
    });
  }

  function start() { buildIndex(); position(); print(); }
  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", start); else start();
})();
