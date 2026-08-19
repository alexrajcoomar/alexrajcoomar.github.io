/* ============================================================
   The atlas globe.

   This script draws a view of the page it is on. Every mark comes from a real
   link already in the document, so the list under the globe is not a fallback
   bolted on afterwards, it is the source: turn this file off and the page is
   still the complete, linked table of contents for the corpus.

   No framework, no topology data, no WebGL. A Fibonacci lattice put the
   document centroids on the sphere at build time; all this file does is
   rotate, project orthographically, and draw.
   ============================================================ */
(function () {
  "use strict";

  var stage = document.getElementById("astage");
  var list = document.getElementById("atlaslist");
  var cv = document.getElementById("acanvas");
  if (!stage || !list || !cv || !cv.getContext) return;

  var reduced = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ------------------------------------------------- read the page ---- */
  var pts = [], regions = [];
  [].forEach.call(list.querySelectorAll(".areg"), function (sec, ri) {
    var c = (sec.getAttribute("data-c") || "0,0,1").split(",").map(Number);
    var reg = {
      i: ri,
      slug: sec.getAttribute("data-s"),
      title: sec.getAttribute("data-t") || "",
      url: sec.getAttribute("data-u") || "",
      kind: sec.getAttribute("data-k") || "",
      surface: sec.getAttribute("data-surface") || "course",
      x: c[0], y: c[1], z: c[2],
      n: 0
    };
    regions.push(reg);
    [].forEach.call(sec.querySelectorAll(".apt"), function (li) {
      var a = li.querySelector("a");
      if (!a) return;
      var p = (li.getAttribute("data-p") || "0,0,1").split(",").map(Number);
      pts.push({
        x: p[0], y: p[1], z: p[2],
        t: a.textContent.trim(),
        lt: a.textContent.trim().toLowerCase(),
        href: a.getAttribute("href"),
        r: reg,
        on: true,
        /* filled in every frame */
        sx: 0, sy: 0, sz: 0
      });
      reg.n++;
    });
  });
  if (pts.length < 8) return;

  /* ------------------------------------------------------- colours ---- */
  /* Read from the stylesheet rather than restated here, so the globe follows
     the theme the reader chose and there is one definition of the palette. */
  var C = {};
  function readColours() {
    var s = getComputedStyle(document.documentElement);
    C.ind = s.getPropertyValue("--accent").trim() || "#14509b";
    C.cou = s.getPropertyValue("--ink-3").trim() || "#6f6c63";
    C.too = s.getPropertyValue("--tool").trim() || "#0f6b58";
    C.rule = s.getPropertyValue("--rule").trim() || "#ddd9cf";
    C.ink = s.getPropertyValue("--ink").trim() || "#16150f";
  }
  readColours();
  new MutationObserver(readColours).observe(document.documentElement,
    { attributes: true, attributeFilter: ["data-theme"] });
  if (window.matchMedia) {
    var mq = window.matchMedia("(prefers-color-scheme: dark)");
    (mq.addEventListener ? mq.addEventListener.bind(mq, "change")
      : mq.addListener.bind(mq))(readColours);
  }

  function rgba(hex, a) {
    var h = hex.replace("#", "");
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var n = parseInt(h, 16);
    return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," +
      (n & 255) + "," + a.toFixed(3) + ")";
  }

  /* ---------------------------------------------------------- state --- */
  var ctx = cv.getContext("2d");
  var dpr = 1, W = 0, H = 0, cx = 0, cy = 0, R = 0;
  var yaw = 0.6, pitch = -0.34, spin = reduced ? 0 : 0.055;
  var vYaw = 0, vPitch = 0, dragging = false, lastX = 0, lastY = 0, moved = 0;
  var hover = null, filter = "", shown = pts.length;
  var labels = [], labelAt = 0;

  var labelBox = document.getElementById("alabels");
  var card = document.getElementById("acard");
  var cardT = card.querySelector(".ac-t");
  var cardD = card.querySelector(".ac-d");
  var countEl = document.getElementById("acount");

  /* Measured, not estimated. A guess at seven pixels a character is wrong by
     enough on tracked uppercase to let two labels overlap, which is exactly
     what it did. */
  var _mcache = {};
  function measure(text, font) {
    var k = font + "|" + text;
    if (_mcache[k] !== undefined) return _mcache[k];
    ctx.save();
    ctx.font = font;
    var w = ctx.measureText(text).width;
    ctx.restore();
    return (_mcache[k] = w);
  }
  function fontOf(el, fallback) {
    var s2 = getComputedStyle(el);
    var f = s2.fontWeight + " " + s2.fontSize + "/" + s2.lineHeight + " " + s2.fontFamily;
    return f.indexOf("px") > -1 ? f : fallback;
  }

  function size() {
    var rect = stage.getBoundingClientRect();
    dpr = Math.min(2, window.devicePixelRatio || 1);
    W = Math.max(240, rect.width);
    H = Math.max(240, rect.height);
    cv.width = Math.round(W * dpr);
    cv.height = Math.round(H * dpr);
    cv.style.width = W + "px";
    cv.style.height = H + "px";
    cx = W / 2;
    cy = H / 2;
    /* fill the stage rather than sitting in the middle of it */
    /* leave a ring of clear space for the labels that sit outside it */
    R = Math.min(W * 0.30, H * 0.40);
  }

  /* ------------------------------------------------------ projection -- */
  function project() {
    var cyaw = Math.cos(yaw), syaw = Math.sin(yaw);
    var cpit = Math.cos(pitch), spit = Math.sin(pitch);
    for (var i = 0; i < pts.length; i++) {
      var p = pts[i];
      /* around Y, then around X: two rotations, no matrix library */
      var x1 = p.x * cyaw + p.z * syaw;
      var z1 = -p.x * syaw + p.z * cyaw;
      var y2 = p.y * cpit - z1 * spit;
      var z2 = p.y * spit + z1 * cpit;
      p.sx = cx + x1 * R;
      p.sy = cy - y2 * R;
      p.sz = z2;
    }
    for (var j = 0; j < regions.length; j++) {
      var r = regions[j];
      var rx = r.x * cyaw + r.z * syaw;
      var rz = -r.x * syaw + r.z * cyaw;
      var ry = r.y * cpit - rz * spit;
      r.sx = cx + rx * R;
      r.sy = cy - ry * R;
      r.sz = r.y * spit + rz * cpit;
    }
  }

  /* ----------------------------------------------------------- draw --- */
  function draw() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);

    /* the silhouette, so the marks read as sitting on a sphere rather than
       floating in a cloud. A guide, not data, so it stays near-invisible. */
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, Math.PI * 2);
    ctx.strokeStyle = rgba(C.rule, 0.55);
    ctx.lineWidth = 1;
    ctx.stroke();

    /* leaders, under the marks: a hairline from each named mark out to its
       label on the ring, so a reader can tell which mark a name belongs to */
    ctx.strokeStyle = rgba(C.rule, 0.9);
    ctx.lineWidth = 1;
    for (var q = 0; q < labels.length; q++) {
      if (labels[q].hidden) continue;
      var lp = labels[q].p;
      if (lp.lx === undefined) continue;
      ctx.beginPath();
      ctx.moveTo(lp.sx, lp.sy);
      ctx.lineTo(lp.lx + (lp.lft ? 4 : -4), lp.ly);
      ctx.stroke();
    }

    /* back hemisphere first, so nearer marks sit on top of farther ones */
    var order = pts.slice().sort(function (a, b) { return a.sz - b.sz; });
    for (var i = 0; i < order.length; i++) {
      var p = order[i];
      var t = (p.sz + 1) / 2;                 /* 0 at the back, 1 at the front */
      var a = (0.10 + 0.80 * t) * (p.on ? 1 : 0.10);
      if (a < 0.02) continue;
      var rad = 1.0 + 2.4 * t;
      var isHover = hover === p;
      var near = hover && hover.r === p.r && p.on;
      if (isHover) { rad += 2.2; a = 1; }
      else if (near) { a = Math.min(1, a + 0.22); rad += 0.5; }

      ctx.beginPath();
      ctx.arc(p.sx, p.sy, rad, 0, Math.PI * 2);
      if (p.r.surface === "course") {
        ctx.strokeStyle = rgba(C.cou, Math.min(1, a * 1.25));
        ctx.lineWidth = 1.15;
        ctx.stroke();
      } else if (p.r.kind === "Tool") {
        ctx.fillStyle = rgba(C.too, a);
        ctx.fill();
      } else {
        ctx.fillStyle = rgba(C.ind, p.r.surface === "personal" ? a * 0.55 : a);
        ctx.fill();
      }
      if (isHover) {
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, rad + 4.5, 0, Math.PI * 2);
        ctx.strokeStyle = rgba(C.ink, 0.5);
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    }
  }

  /* --------------------------------------------------------- labels --- */
  /* Only the marks facing the reader are named, and only as many as fit
     without touching. A label that has to shrink to fit is a label the site
     does not print: nothing here goes under the same floor the rest of the
     pages hold to. */
  var LABEL_MAX = 176;
  var labelBoxes = [];
  function labelText(p) {
    return p.t.length > 34 ? p.t.slice(0, 32).replace(/[ ,:;]+$/, "") + "\u2026" : p.t;
  }
  function labelFont() {
    return labels.length ? fontOf(labels[0].el, "400 12px InterVar, sans-serif")
                         : "400 12px InterVar, sans-serif";
  }

  function pickLabels() {
    /* Labels sit outside the sphere on a ring, joined to their mark by a
       hairline, rather than on top of the point field where they would land
       in the middle of a hundred other marks. The ring is cut into slots and
       each slot keeps its single most forward-facing candidate, so the set is
       evenly spread by construction and two labels can never collide. */
    var slots = W > 1180 ? 14 : W > 820 ? 11 : 8;
    var best = new Array(slots);
    for (var i = 0; i < pts.length; i++) {
      var p = pts[i];
      if (!p.on || p.sz < 0.12) continue;
      var dx = p.sx - cx, dy = p.sy - cy;
      var rr = Math.sqrt(dx * dx + dy * dy);
      if (rr < R * 0.34) continue;              /* too near the middle to aim */
      var ang = Math.atan2(dy, dx);
      var k = Math.floor(((ang + Math.PI) / (Math.PI * 2)) * slots) % slots;
      var score = p.sz + (rr / R) * 0.35;
      if (!best[k] || score > best[k].score) best[k] = { p: p, ang: ang, score: score };
    }
    /* Measured boxes, then a single greedy pass over the whole ring. Slots
       spread the candidates out and per-side spacing handled the columns, but
       neither could see a left-hand label meeting a right-hand one over the top
       of the sphere, which is where the pairs kept landing on each other. One
       pass over one list, using the width the text will actually occupy, is the
       thing that cannot miss a case. */
    var font = labelFont();
    var ring = [];
    for (var j = 0; j < slots; j++) {
      if (!best[j]) continue;
      var b = best[j];
      var lx = cx + Math.cos(b.ang) * (R + 22);
      var ly = cy + Math.sin(b.ang) * (R + 18);
      if (ly < 12 || ly > H - 12) continue;
      b.p.lft = lx < cx;
      b.p.lx = lx;
      b.p.ly = ly;
      b.p.lw = Math.min(LABEL_MAX, measure(labelText(b.p), font) + 8);
      ring.push(b);
    }
    ring.sort(function (a, b2) { return b2.score - a.score; });
    var out = [], boxes = [];
    for (var k = 0; k < ring.length; k++) {
      var c = ring[k].p;
      var x0 = c.lft ? c.lx - c.lw : c.lx;
      var box = [x0, c.ly - 10, x0 + c.lw, c.ly + 10];
      if (box[0] < 2 || box[2] > W - 2) continue;
      var clash = false;
      for (var m = 0; m < boxes.length; m++) {
        var o = boxes[m];
        if (!(box[2] < o[0] - 8 || box[0] > o[2] + 8 ||
              box[3] < o[1] - 4 || box[1] > o[3] + 4)) { clash = true; break; }
      }
      if (clash) continue;
      boxes.push(box);
      out.push(c);
    }
    return out;
  }

  function syncLabels(force) {
    var now = performance.now();
    if (force || now - labelAt > 460) {
      labelAt = now;
      var want = pickLabels();
      var have = {};
      for (var i = 0; i < labels.length; i++) have[labels[i].p.t] = labels[i];
      var keep = [];
      for (var j = 0; j < want.length; j++) {
        var p = want[j], ex = have[p.t];
        if (ex) { keep.push(ex); delete have[p.t]; continue; }
        var el = document.createElement("a");
        el.className = "alab";
        el.href = p.href;
        el.textContent = labelText(p);
        el.setAttribute("tabindex", "-1");
        if (p.lft) el.classList.add("lft");
        labelBox.appendChild(el);
        requestAnimationFrame(function (n) {
          return function () { n.classList.add("on"); };
        }(el));
        keep.push({ p: p, el: el });
      }
      for (var t in have) {
        if (!Object.prototype.hasOwnProperty.call(have, t)) continue;
        (function (l) {
          /* Retired at once rather than faded out. A label on its way out still
             occupies its box, and the label arriving in that space does not
             know about it, which is the only overlap the geometry checks could
             not see. Arrivals still fade in, so the motion reads the same. */
          l.el.style.transition = "none";
          l.el.style.opacity = "0";
          l.el.classList.remove("on");
          setTimeout(function () {
            if (l.el.parentNode) l.el.parentNode.removeChild(l.el);
          }, 40);
        })(have[t]);
      }
      labels = keep;
    }
    /* Placed from measured text, then checked again against what the browser
       actually laid out. The estimate and the rendered box differ by a few
       pixels of padding and font resolution, and a few pixels is the whole
       difference between two labels touching and not. Anything that still
       overlaps is hidden rather than printed on top of its neighbour. */
    var kept = [];
    labelBoxes = [];
    for (var m = 0; m < labels.length; m++) {
      var L = labels[m];
      L.el.classList.toggle("lft", !!L.p.lft);
      var w = L.el.offsetWidth || L.p.lw || 120;
      var h = L.el.offsetHeight || 18;
      var lx = L.p.lft ? L.p.lx - w : L.p.lx;
      lx = Math.max(2, Math.min(W - w - 2, lx));
      var ly = L.p.ly - h / 2;
      var box = [lx, ly, lx + w, ly + h];
      var clash = false;
      for (var n3 = 0; n3 < kept.length; n3++) {
        var o = kept[n3];
        if (!(box[2] < o[0] - 6 || box[0] > o[2] + 6 ||
              box[3] < o[1] - 2 || box[1] > o[3] + 2)) { clash = true; break; }
      }
      L.el.style.transform = "translate(" + Math.round(lx) + "px," +
        Math.round(ly) + "px)";
      L.hidden = clash;
      L.el.style.opacity = clash ? 0
        : Math.max(0, Math.min(1, (L.p.sz - 0.02) * 3.2));
      if (!clash) { kept.push(box); labelBoxes.push(box); }
    }
  }


  /* -------------------------------------------------- region names ---- */
  /* The document a patch of marks belongs to, written across the patch. This
     is the part that makes it a map rather than a cloud: without it you can
     see that the marks are grouped but not what any group is. */
  var rlabels = [], rlabelAt = 0;
  function syncRegions(force) {
    var now = performance.now();
    if (force || now - rlabelAt > 460) {
      rlabelAt = now;
      var cand = regions.filter(function (r) {
        return r.sz > 0.5 && r.n > 2;
      }).sort(function (a, b) { return b.sz - a.sz; });
      var font = rlabels.length ? fontOf(rlabels[0].el, "660 11px InterVar, sans-serif")
                                : "660 11px InterVar, sans-serif";
      /* Region names start from the boxes the section labels already claimed,
         so a document name can never be printed over one of them. */
      var want = [], boxes = labelBoxes.slice();
      /* the label ring already carries the section names; three document names
         is enough to say which patch is which without crowding the field */
      var max = W > 1180 ? 3 : 2;
      for (var i = 0; i < cand.length && want.length < max; i++) {
        var r = cand[i];
        /* uppercase and tracked, so measure the string that is actually drawn */
        var w = measure(r.title.toUpperCase(), font) + r.title.length * 1.5 + 10;
        var box = [r.sx - w / 2, r.sy - 11, r.sx + w / 2, r.sy + 11];
        if (box[0] < 6 || box[2] > W - 6 || box[1] < 6 || box[3] > H - 6) continue;
        var clash = false;
        for (var k = 0; k < boxes.length; k++) {
          var b = boxes[k];
          if (!(box[2] < b[0] - 26 || box[0] > b[2] + 26 ||
                box[3] < b[1] - 22 || box[1] > b[3] + 22)) { clash = true; break; }
        }
        if (clash) continue;
        boxes.push(box);
        want.push(r);
      }
      var have = {};
      for (var j = 0; j < rlabels.length; j++) have[rlabels[j].r.slug] = rlabels[j];
      var keep = [];
      for (var m = 0; m < want.length; m++) {
        var rr = want[m], ex = have[rr.slug];
        if (ex) { keep.push(ex); delete have[rr.slug]; continue; }
        var el = document.createElement("a");
        el.className = "arlab";
        el.href = rr.url;
        el.textContent = rr.title;
        el.setAttribute("tabindex", "-1");
        labelBox.appendChild(el);
        requestAnimationFrame(function (n) {
          return function () { n.classList.add("on"); };
        }(el));
        keep.push({ r: rr, el: el });
      }
      for (var t in have) {
        if (!Object.prototype.hasOwnProperty.call(have, t)) continue;
        (function (l) {
          l.el.style.transition = "none";
          l.el.style.opacity = "0";
          l.el.classList.remove("on");
          setTimeout(function () {
            if (l.el.parentNode) l.el.parentNode.removeChild(l.el);
          }, 40);
        })(have[t]);
      }
      rlabels = keep;
    }
    for (var n2 = 0; n2 < rlabels.length; n2++) {
      var L = rlabels[n2];
      var w2 = L.el.offsetWidth || 120;
      L.el.style.transform = "translate(" + Math.round(L.r.sx - w2 / 2) + "px," +
        Math.round(L.r.sy - 8) + "px)";
      L.el.style.opacity = Math.max(0, Math.min(0.92, (L.r.sz - 0.34) * 2.6));
      L.el.classList.toggle("cur", !!(hover && hover.r === L.r));
    }
  }

  /* ---------------------------------------------------------- frame --- */
  var last = performance.now();
  function frame(now) {
    var dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    if (!dragging) {
      yaw += (spin + vYaw) * dt;
      pitch += vPitch * dt;
      vYaw *= 0.94;
      vPitch *= 0.94;
      if (Math.abs(vYaw) < 0.0006) vYaw = 0;
      if (Math.abs(vPitch) < 0.0006) vPitch = 0;
      pitch = Math.max(-1.15, Math.min(1.15, pitch));
    }
    project();
    draw();
    syncLabels(false);
    syncRegions(false);
    if (hover) placeCard();
    requestAnimationFrame(frame);
  }

  /* --------------------------------------------------------- hover ---- */
  function hit(mx, my) {
    var best = null, bd = 15 * 15;
    for (var i = 0; i < pts.length; i++) {
      var p = pts[i];
      if (p.sz <= 0 || !p.on) continue;
      var dx = p.sx - mx, dy = p.sy - my, d = dx * dx + dy * dy;
      if (d < bd || (d < 15 * 15 && best && p.sz > best.sz)) { bd = d; best = p; }
    }
    return best;
  }

  function placeCard() {
    if (!hover) return;
    var w = card.offsetWidth || 260, h = card.offsetHeight || 60;
    var x = hover.sx + 18, y = hover.sy - h / 2;
    if (x + w > W - 6) x = hover.sx - w - 18;
    y = Math.max(6, Math.min(H - h - 6, y));
    card.style.transform = "translate(" + Math.round(x) + "px," + Math.round(y) + "px)";
  }

  function setHover(p) {
    if (hover === p) return;
    hover = p;
    if (!p) { card.hidden = true; stage.classList.remove("hot"); return; }
    cardT.textContent = p.t;
    cardD.textContent = p.r.title + "  ·  " + p.r.kind;
    card.hidden = false;
    stage.classList.add("hot");
    placeCard();
  }

  /* ------------------------------------------------------- pointer ---- */
  function local(e) {
    var r = cv.getBoundingClientRect();
    return [e.clientX - r.left, e.clientY - r.top];
  }
  cv.addEventListener("pointerdown", function (e) {
    dragging = true; moved = 0;
    var l = local(e); lastX = l[0]; lastY = l[1];
    cv.setPointerCapture(e.pointerId);
    stage.classList.add("drag");
  });
  cv.addEventListener("pointermove", function (e) {
    var l = local(e);
    if (dragging) {
      var dx = l[0] - lastX, dy = l[1] - lastY;
      moved += Math.abs(dx) + Math.abs(dy);
      yaw += dx * 0.006;
      pitch = Math.max(-1.15, Math.min(1.15, pitch + dy * 0.005));
      vYaw = dx * 0.09;
      vPitch = dy * 0.07;
      lastX = l[0]; lastY = l[1];
      setHover(null);
    } else {
      setHover(hit(l[0], l[1]));
    }
  });
  function endDrag(e) {
    if (!dragging) return;
    dragging = false;
    stage.classList.remove("drag");
    try { cv.releasePointerCapture(e.pointerId); } catch (x) {}
  }
  cv.addEventListener("pointerup", function (e) {
    var wasDrag = moved > 6;
    endDrag(e);
    if (!wasDrag) {
      var l = local(e);
      var p = hit(l[0], l[1]);
      if (p) window.location.href = p.href;
    }
  });
  cv.addEventListener("pointercancel", endDrag);
  cv.addEventListener("pointerleave", function () {
    if (!dragging) setHover(null);
  });

  /* -------------------------------------------------------- search ---- */
  var q = document.getElementById("aq");
  if (q) {
    q.addEventListener("input", function () {
      filter = q.value.trim().toLowerCase();
      shown = 0;
      for (var i = 0; i < pts.length; i++) {
        var p = pts[i];
        p.on = !filter || p.lt.indexOf(filter) > -1 ||
          p.r.title.toLowerCase().indexOf(filter) > -1;
        if (p.on) shown++;
      }
      [].forEach.call(list.querySelectorAll(".areg"), function (sec) {
        var any = 0;
        [].forEach.call(sec.querySelectorAll(".apt"), function (li) {
          var a = li.querySelector("a");
          var t = (a ? a.textContent : "").toLowerCase();
          var ok = !filter || t.indexOf(filter) > -1 ||
            (sec.getAttribute("data-t") || "").toLowerCase().indexOf(filter) > -1;
          li.hidden = !ok;
          if (ok) any++;
        });
        sec.hidden = !any;
      });
      countEl.textContent = !filter
        ? "Showing all " + pts.length.toLocaleString("en-CA") + " sections."
        : "Showing " + shown.toLocaleString("en-CA") + " of " +
          pts.length.toLocaleString("en-CA") + " sections matching “" +
          q.value.trim() + "”.";
      setHover(null);
      syncLabels(true);
      syncRegions(true);
    });
  }

  /* --------------------------------------------------------- modes ---- */
  var modes = document.getElementById("amodes");
  var bGlobe = document.getElementById("aglobe");
  var bList = document.getElementById("alist");
  var key = document.getElementById("akey");
  var running = false;

  function setMode(globe) {
    stage.hidden = !globe;
    key.hidden = !globe;
    list.classList.toggle("as-index", globe);
    bGlobe.setAttribute("aria-pressed", String(globe));
    bList.setAttribute("aria-pressed", String(!globe));
    try { sessionStorage.setItem("atlas.mode", globe ? "globe" : "list"); } catch (e) {}
    if (globe) {
      size();
      project();
      syncLabels(true);
      syncRegions(true);
      if (!running) { running = true; requestAnimationFrame(frame); }
    }
  }
  bGlobe.addEventListener("click", function () { setMode(true); });
  bList.addEventListener("click", function () { setMode(false); });

  var wide = !window.matchMedia || window.matchMedia("(min-width: 900px)").matches;
  var saved = null;
  try { saved = sessionStorage.getItem("atlas.mode"); } catch (e) {}
  modes.hidden = false;
  setMode(saved ? saved === "globe" : wide);

  var rt;
  window.addEventListener("resize", function () {
    clearTimeout(rt);
    rt = setTimeout(function () {
      if (stage.hidden) return;
      size();
      project();
      syncLabels(true);
      syncRegions(true);
    }, 120);
  });
})();
