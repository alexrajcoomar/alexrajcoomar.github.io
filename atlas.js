/* ============================================================
   The Atlas.

   One camera, used twice. Six wall labels hold it and make an argument about
   the corpus; when they hand over, the reader drives the same camera to
   explore. There is no second renderer and no second state machine.

   Everything drawn comes from links already in this page: the index below the
   sphere is the data, not a fallback. Turn this file off and the page is still
   the complete, linked table of contents plus the whole argument as prose.

   No framework, no topology data, no WebGL. Two rotations, an orthographic
   projection and a zoom, done by hand.

   The loop is demand-driven. Nothing is drawn unless something moved, because
   a held wall label is a still picture and a still picture should not cost a
   frame.
   ============================================================ */
(function () {
  "use strict";

  var stage = document.getElementById("astage");
  var list = document.getElementById("atlaslist");
  var cv = document.getElementById("acanvas");
  if (!stage || !list || !cv || !cv.getContext) return;

  var reduced = false;
  var mqr = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
  if (mqr) {
    reduced = mqr.matches;
    var onmo = function () { reduced = mqr.matches; };
    (mqr.addEventListener ? mqr.addEventListener.bind(mqr, "change")
      : mqr.addListener.bind(mqr))(onmo);
  }
  var mqn = window.matchMedia && window.matchMedia("(max-width: 63.99rem)");
  function narrow() { return !mqn || mqn.matches; }
  /* Narrow: the sphere leads and the index follows. Tiny: there is no clear
     ring around the sphere to put type in at all. A tablet is the first and
     not the second. */
  var mqt = window.matchMedia && window.matchMedia("(max-width: 40rem)");
  function tiny() { return !mqt || mqt.matches; }

  /* ------------------------------------------------- read the page ---- */
  var pts = [], regions = [], byUrl = {}, bySlug = {};
  var TRAIL = {};
  try { TRAIL = JSON.parse(localStorage.getItem("atlas.trail") || "{}"); } catch (e) {}
  [].forEach.call(list.querySelectorAll(".areg"), function (sec, ri) {
    var c = (sec.getAttribute("data-c") || "0,0,1").split(",").map(Number);
    var reg = {
      i: ri,
      slug: sec.getAttribute("data-s"),
      title: sec.getAttribute("data-t") || "",
      url: sec.getAttribute("data-u") || "",
      kind: sec.getAttribute("data-k") || "",
      surface: sec.getAttribute("data-surface") || "course",
      meta: (sec.querySelector(".areg-m") || {}).textContent || "",
      el: sec,
      x: c[0], y: c[1], z: c[2],
      n: 0, items: []
    };
    regions.push(reg);
    bySlug[reg.slug] = reg;
    [].forEach.call(sec.getElementsByClassName("apt"), function (li) {
      var a = li.firstElementChild;
      if (!a || a.tagName !== "A") return;
      var p = (li.getAttribute("data-p") || "0,0,1").split(",").map(Number);
      var o = {
        x: p[0], y: p[1], z: p[2],
        t: a.textContent.trim(),
        lt: a.textContent.trim().toLowerCase(),
        href: a.getAttribute("href"),
        lvl: +(li.getAttribute("data-l") || 3),
        shared: +(li.getAttribute("data-n") || 1),
        /* the documents that actually carry a shared heading, so pointing at
           one can draw the measured fan to its owners */
        own: (li.getAttribute("data-o") || "").split(",").filter(Boolean),
        /* passages this browser has opened; recorded by site.js, read here,
           never sent anywhere */
        seen: !!TRAIL[a.getAttribute("href")],
        r: reg,
        on: true, sx: 0, sy: 0, sz: 0
      };
      /* The six tools are the marks that are not headings: label 01 says so
         in prose, and the picture now says it too. They stand off the sphere
         on the channel the stems established, altitude for the marks whose
         position means something different. Their bearing is unchanged, so
         nothing about where they are is invented; only their kind is drawn. */
      if (reg.kind === "Tool") {
        o.tool = true;
        o.x *= 1.13; o.y *= 1.13; o.z *= 1.13;
      }
      pts.push(o);
      byUrl[o.href] = o;
      reg.items.push(o);
      reg.n++;
    });
  });
  if (pts.length < 8) return;

  var FACTS = {};
  try {
    FACTS = JSON.parse(document.getElementById("afacts").textContent);
  } catch (e) { FACTS = {}; }

  /* Links the corpus records between documents, harvested at build time from
     each document's own prose. One entry per linked pair, with the direction
     kept, built once here so drawing them later allocates nothing. */
  regions.forEach(function (g) { g.lk = []; });
  (FACTS.lk || []).forEach(function (e) {
    var a = bySlug[e[0]], b = bySlug[e[1]];
    if (!a || !b) return;
    var have = null;
    for (var li = 0; li < a.lk.length; li++) {
      if (a.lk[li].g === b) { have = a.lk[li]; break; }
    }
    if (have) { have.out = true; }
    else { a.lk.push({ g: b, out: true, into: false }); }
    var back = null;
    for (var lj = 0; lj < b.lk.length; lj++) {
      if (b.lk[lj].g === a) { back = b.lk[lj]; break; }
    }
    if (back) { back.into = true; }
    else { b.lk.push({ g: a, out: false, into: true }); }
  });

  /* ------------------------------------------------------- colours ---- */
  var C = {};
  function readColours() {
    var s = getComputedStyle(document.documentElement);
    function v(n, d) { return s.getPropertyValue(n).trim() || d; }
    C.ind = v("--accent", "#14509b");
    C.cou = v("--ink-3", "#6f6c63");
    C.too = v("--tool", "#0f6b58");
    C.ref = v("--ref", "#8a5410");
    C.rule = v("--rule", "#ddd9cf");
    C.strong = v("--rule-strong", "#bfb9aa");
    /* --edge is the stylesheet's non-text-contrast token, 3.5:1 on paper.
       Every category a key names is drawn at least that strong. */
    C.edge = v("--edge", "#8a847c");
    C.ink = v("--ink", "#16150f");
    C.paper = v("--paper", "#faf9f6");
    _tc = {};
    invalidate();
  }
  readColours();
  new MutationObserver(readColours).observe(document.documentElement,
    { attributes: true, attributeFilter: ["data-theme"] });
  if (window.matchMedia) {
    var mqd = window.matchMedia("(prefers-color-scheme: dark)");
    (mqd.addEventListener ? mqd.addEventListener.bind(mqd, "change")
      : mqd.addListener.bind(mqd))(readColours);
  }
  /* The draw loop asks for the same few colours at nearly the same alphas
     1,373 times a frame. Building the string each time was one allocation
     per mark per frame; quantising alpha to 1/48ths (invisible at these
     sizes) makes the strings cacheable, and the cache empties whenever the
     theme swaps the palette under it. */
  var _tc = {};
  function tone2(hex, a) {
    var q = (a * 48 + 0.5) | 0;
    var k = hex + q;
    return _tc[k] || (_tc[k] = rgba(hex, q / 48));
  }
  function rgba(hex, a) {
    var h = hex.replace("#", "");
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var n = parseInt(h, 16);
    return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," +
      (n & 255) + "," + Math.max(0, Math.min(1, a)).toFixed(3) + ")";
  }

  /* ---------------------------------------------------------- maths --- */
  function nrm(v) {
    var m = Math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) || 1;
    return [v[0] / m, v[1] / m, v[2] / m];
  }
  /* the rotation that brings a unit vector to face the reader */
  function facing(v) {
    return { yaw: Math.atan2(-v[0], v[2]),
             pitch: Math.atan2(v[1], Math.sqrt(v[0] * v[0] + v[2] * v[2])) };
  }
  function shortest(a, b) {
    var d = (b - a) % (Math.PI * 2);
    if (d > Math.PI) d -= Math.PI * 2;
    if (d < -Math.PI) d += Math.PI * 2;
    return a + d;
  }

  /* ---------------------------------------------------------- state --- */
  var ctx = cv.getContext("2d");
  /* No 2D context, no globe: a blocked or failed canvas leaves the
     server-rendered page exactly as shipped, index visible, every link
     live, instead of a blank stage over a hidden index. */
  if (!ctx) return;
  var dpr = 1, W = 0, H = 0, cx = 0, cy = 0, R0 = 0;
  var cam = { yaw: 0.6, pitch: -0.34, zoom: 1 };
  var vYaw = 0, vPitch = 0, dragging = false, lastX = 0, lastY = 0, moved = 0;
  var hover = null, filter = "", shown = pts.length;
  var mode = "tour", step = 0, focus = null, staged = null, turned = false;
  var tween = null, booted = false;
  /* the drift says "this turns" and then gets out of the way */
  var DRIFT = 0.05, driftUntil = 0;

  var labelBox = document.getElementById("alabels");
  var card = document.getElementById("acard");
  var cardT = card.querySelector(".ac-t");
  var cardD = card.querySelector(".ac-d");
  var countEl = document.getElementById("acount");
  var hintEl = document.getElementById("ahint");
  var crumb = document.getElementById("acrumb");
  var crumbNow = document.getElementById("acrumbnow");
  var stageKey = document.getElementById("astagekey");
  var plates = [].slice.call(document.querySelectorAll(".plate"));
  var guide = document.getElementById("aguide");
  var freebar = document.getElementById("afree");
  var navbar = document.getElementById("anav");
  var docPanel = document.getElementById("adoc");
  var results = document.getElementById("ares");
  var restore = document.getElementById("arestore");
  var caption = document.getElementById("acap");

  function R() { return R0 * cam.zoom; }

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
    /* the sphere leaves a ring of clear space for the labels around it */
    /* the tallest stem stands 24% of a radius off the surface, so the narrow
       layout leaves it room rather than letting it cross the hint below */
    R0 = narrow() ? Math.min(W * 0.395, H * 0.395) : Math.min(W * 0.29, H * 0.39);
    invalidate();
  }

  /* ---------------------------------------------------- the loop ------ */
  /* Demand driven: `kick` schedules one frame and the frame reschedules only
     while something is moving. A held stop costs nothing. */
  var raf = 0, dirty = true, last = 0, visible = true;
  function invalidate() { dirty = true; kick(); }
  function kick() {
    if (raf || !visible || stage.hidden) return;
    raf = requestAnimationFrame(frame);
  }
  function frame(now) {
    raf = 0;
    var dt = last ? Math.min(0.05, (now - last) / 1000) : 0.016;
    last = now;
    var moving = stepTween(now);
    var drifting = false;
    if (!moving && !dragging) {
      if (mode === "free" && !focus && !turned && !reduced && now < driftUntil) {
        /* eases out over its last second rather than stopping dead */
        var k = Math.min(1, (driftUntil - now) / 900);
        cam.yaw += DRIFT * k * dt;
        drifting = true;
      }
      cam.yaw += vYaw * dt;
      cam.pitch += vPitch * dt;
      vYaw *= 0.94; vPitch *= 0.94;
      if (Math.abs(vYaw) < 0.0006) vYaw = 0;
      if (Math.abs(vPitch) < 0.0006) vPitch = 0;
      cam.pitch = Math.max(-1.15, Math.min(1.15, cam.pitch));
    }
    var busy = moving || dragging || drifting || vYaw !== 0 || vPitch !== 0;
    /* the reference frame rises while the sphere is being turned and settles
       out of the way when it stops */
    var wantGrid = (dragging || vYaw !== 0 || vPitch !== 0) ? 1 : 0;
    if (gridA !== wantGrid) {
      var st = dt * (wantGrid ? 4.5 : 2.2);
      gridA = wantGrid ? Math.min(1, gridA + st) : Math.max(0, gridA - st);
      if (reduced) gridA = wantGrid;
      busy = true;
    }
    if (busy || dirty) {
      project();
      draw();
      syncLabels(false);
      syncRegions(false);
      if (hover) placeCard();
      dirty = false;
    }
    if (busy) kick();
    else { syncLabels(true); syncRegions(true); }
  }
  if (window.IntersectionObserver) {
    new IntersectionObserver(function (es) {
      visible = es[0].isIntersecting;
      if (visible) { last = 0; invalidate(); }
    }, { rootMargin: "120px" }).observe(stage);
  }

  /* ------------------------------------------------------ projection -- */
  function project() {
    syncRot();
    var cyaw = _cy1, syaw = _sy1, cpit = _cp1, spit = _sp1, r = _r1;
    for (var i = 0; i < pts.length; i++) {
      var p = pts[i];
      var x1 = p.x * cyaw + p.z * syaw;
      var z1 = -p.x * syaw + p.z * cyaw;
      var y2 = p.y * cpit - z1 * spit;
      p.sx = cx + x1 * r;
      p.sy = cy - y2 * r;
      p.sz = p.y * spit + z1 * cpit;
    }
    for (var j = 0; j < regions.length; j++) {
      var g = regions[j];
      var rx = g.x * cyaw + g.z * syaw;
      var rz = -g.x * syaw + g.z * cyaw;
      var ry = g.y * cpit - rz * spit;
      g.sx = cx + rx * r;
      g.sy = cy - ry * r;
      g.sz = g.y * spit + rz * cpit;
    }
  }
  /* The rotation terms are constant for a frame. screenOf used to work them
     out again for every vertex, which is four trig calls per point: with a
     graticule, three construction circles and a seven-line fan that is several
     thousand a frame, and it was the whole of the frame budget the grid cost. */
  var _cy1 = 1, _sy1 = 0, _cp1 = 1, _sp1 = 0, _r1 = 0;
  function syncRot() {
    _cy1 = Math.cos(cam.yaw); _sy1 = Math.sin(cam.yaw);
    _cp1 = Math.cos(cam.pitch); _sp1 = Math.sin(cam.pitch);
    _r1 = R();
  }
  var _t = [0, 0, 0];
  function screenOf(v) {
    var x1 = v[0] * _cy1 + v[2] * _sy1;
    var z1 = -v[0] * _sy1 + v[2] * _cy1;
    _t[0] = cx + x1 * _r1;
    _t[1] = cy - (v[1] * _cp1 - z1 * _sp1) * _r1;
    _t[2] = v[1] * _sp1 + z1 * _cp1;
    return _t;
  }

  /* ----------------------------------------------------------- fly ---- */
  function flyTo(to, ms) {
    if (reduced) {
      if (to.yaw !== undefined) cam.yaw = to.yaw;
      if (to.pitch !== undefined) cam.pitch = to.pitch;
      if (to.zoom !== undefined) cam.zoom = to.zoom;
      tween = null;
      project(); invalidate(); syncLabels(true); syncRegions(true);
      return;
    }
    tween = {
      from: { yaw: cam.yaw, pitch: cam.pitch, zoom: cam.zoom },
      to: {
        yaw: to.yaw === undefined ? cam.yaw : shortest(cam.yaw, to.yaw),
        pitch: to.pitch === undefined ? cam.pitch : to.pitch,
        zoom: to.zoom === undefined ? cam.zoom : to.zoom
      },
      t0: performance.now(),
      dur: ms || 1050
    };
    vYaw = vPitch = 0;
    invalidate();
  }
  function ease(t) {
    /* slow out of the old view, quick through the middle, settle rather than
       stop: the reader is meant to be able to follow one mark the whole way */
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }
  function stepTween(now) {
    if (!tween) return false;
    var k = Math.min(1, (now - tween.t0) / tween.dur), e = ease(k);
    cam.yaw = tween.from.yaw + (tween.to.yaw - tween.from.yaw) * e;
    cam.pitch = tween.from.pitch + (tween.to.pitch - tween.from.pitch) * e;
    /* zoom interpolated in log space so the approach feels even */
    cam.zoom = Math.exp(Math.log(tween.from.zoom) +
      (Math.log(tween.to.zoom) - Math.log(tween.from.zoom)) * e);
    if (k >= 1) { tween = null; syncLabels(true); syncRegions(true); }
    return true;
  }

  /* --------------------------------------------------------- staging -- */
  /* Each label is a camera position plus a rule for what is lit and what
     construction geometry is drawn. The geometry is the point: a caption
     asserts, a drawn cap circle demonstrates. Every radius, parallel and arc
     comes from facts(), measured off the placement pass that put the marks
     where they are; none of it is a round number that looked right. */
  var STAGES = {
    flag: function () {
      var g = bySlug[FACTS.flag];
      var p = byUrl[FACTS.flagOne];
      if (!g) return STAGES.free();
      var f = facing([g.x, g.y, g.z]);
      return { cam: { yaw: f.yaw, pitch: f.pitch, zoom: 1.22 },
               lit: function (q) {
                 if (p && q === p) return 2.4;
                 return q.r === g ? 1.7 : 0.92;
               },
               tone: function (q) { return q.r === g ? "ind" : "field"; },
               /* the whole heading: the label names it whole */
               name: p ? [p] : [], full: true,
               geom: [{ cap: g, deg: FACTS.flagCap }],
               regions: [g],
               key: [["ind", g.title + ", " + g.n + " sections"],
                     ["field", "the rest of the corpus"]] };
    },
    big: function () {
      var g = bySlug[FACTS.big];
      if (!g) return STAGES.free();
      var f = facing([g.x, g.y, g.z]);
      return { cam: { yaw: f.yaw, pitch: f.pitch, zoom: 1.22 },
               lit: function (q) {
                 if (q.r === g) return 1.6;
                 return inCap(q, g, FACTS.cap) ? 1.15 : 0.55;
               },
               tone: function (q) { return q.r === g ? "ind" : (inCap(q, g, FACTS.cap) ? "warn" : "field"); },
               geom: [{ cap: g, deg: FACTS.cap }],
               regions: [g],
               key: [["ind", g.title + ", " + g.n + " sections"],
                     ["warn", "marks from other documents inside the same circle"]] };
    },
    pair: function () {
      var a = bySlug[FACTS.pairA], b = bySlug[FACTS.pairB];
      if (!a || !b) return STAGES.free();
      var mid = FACTS.pairMid ? nrm(FACTS.pairMid) : nrm([a.x + b.x, a.y + b.y, a.z + b.z]);
      var f = facing(mid);
      var mids = {};
      (FACTS.mids || []).forEach(function (u) { if (byUrl[u]) mids[u] = 1; });
      return { cam: { yaw: f.yaw, pitch: f.pitch, zoom: 1.34 },
               lit: function (q) {
                 if (mids[q.href]) return 2.4;
                 if (q.r === a || q.r === b) return 1.15;
                 return 0.55;
               },
               tone: function (q) {
                 return mids[q.href] ? "warn" : (q.r === a || q.r === b ? "ind" : "field");
               },
               name: (FACTS.mids || []).map(function (u) { return byUrl[u]; })
                       .filter(Boolean),
               /* the caps as measured, and the arc the label calls a ruler */
               geom: [{ cap: a, deg: FACTS.pairCapA },
                      { cap: b, deg: FACTS.pairCapB },
                      { arc: [a.x, a.y, a.z], to: [b.x, b.y, b.z], tick: true }],
               regions: [a, b],
               key: [["warn", "headings these two documents share"],
                     ["ind", "everything else in the two documents"]] };
    },
    knot: function () {
      var kc = FACTS.knotC || [0, 0, 1];
      var f = facing(kc);
      /* Held dead centre, a radial stem points at the reader and projects to
         nothing: the one stop whose argument is elevation would show none of
         it. The camera sits off to three-quarters so the pile-up is read in
         profile, which is the only angle at which height is a length. */
      f = { yaw: f.yaw + 0.34, pitch: f.pitch - 0.62 };
      var kn = {};
      (FACTS.knot || []).forEach(function (u) { if (byUrl[u]) kn[u] = 1; });
      var owners = (FACTS.knotOwners || []).map(function (s) { return bySlug[s]; })
        .filter(Boolean);
      return { cam: { yaw: f.yaw, pitch: f.pitch, zoom: 1.15 },
               lit: function (q) { return kn[q.href] ? 2.4 : 0.55; },
               tone: function (q) { return kn[q.href] ? "warn" : "field"; },
               name: (FACTS.knot || []).map(function (u) { return byUrl[u]; })
                       .filter(Boolean).slice(0, 5),
               geom: [{ fan: kc, to: owners }],
               /* named destinations: a line to an unlabelled place measures nothing */
               regions: owners, regionAll: true,
               key: [["warn", "the shared template, averaged to one place"]] };
    },
    north: function () {
      var exc = {};
      (FACTS.exc || []).forEach(function (u) { if (byUrl[u]) exc[u] = 1; });
      return { cam: { yaw: cam.yaw, pitch: 0, zoom: 1.05 },
               lit: function (q) {
                 if (exc[q.href]) return 2.2;
                 /* the label counts below the line too, so it stays legible */
                 return q.r.surface === "independent"
                   ? (q.y >= FACTS.parY ? 1.9 : 1.6) : 1.25;
               },
               tone: function (q) {
                 if (exc[q.href]) return "ring";
                 return q.r.surface === "independent" ? "ind" : "field";
               },
               geom: [{ parallel: FACTS.parY }],
               key: [["ind", "independent work"],
                     ["ring", "above the line but not independent"],
                     ["field", "everything else"]] };
    },
    free: function () {
      return { cam: { yaw: cam.yaw, pitch: -0.28, zoom: 1 },
               lit: null, geom: [] };
    }
  };

  function inCap(q, g, deg) {
    var d = q.x * g.x + q.y * g.y + q.z * g.z;
    return Math.acos(Math.max(-1, Math.min(1, d))) * 180 / Math.PI <= deg;
  }

  /* ----------------------------------------------------------- draw --- */
  function drawSilhouette() {
    /* The one line that says "sphere". In --rule at 60% it measured 1.05:1 on
       paper: in the code and not on the screen.

       The shading around it is deliberately all OUTSIDE the disc. A gradient
       laid over the marks would darken the background every mark is measured
       against, and at the alpha that reads as a lit sphere it pushes the
       receded field under the 3:1 floor. Put the same light outside the limb
       and the object gains its edge for nothing. */
    var r = R();
    ctx.save();
    var g = ctx.createRadialGradient(cx, cy, r, cx, cy, r * 1.13);
    g.addColorStop(0, rgba(C.edge, dark() ? 0.30 : 0.16));
    g.addColorStop(0.45, rgba(C.edge, dark() ? 0.10 : 0.05));
    g.addColorStop(1, rgba(C.edge, 0));
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(cx, cy, r * 1.13, 0, Math.PI * 2);
    ctx.arc(cx, cy, r, 0, Math.PI * 2, true);
    ctx.fill();
    ctx.restore();

    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.strokeStyle = rgba(C.edge, focus ? 0.85 : 0.6);
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  function dark() {
    var p = C.paper.replace("#", "");
    return parseInt(p.slice(0, 2), 16) < 128;
  }

  /* A reference frame you get while you are turning it and not before. The
     grid is genuine (parallels every 30 degrees, meridians every 30) so it
     tells you which way is up, and because it fades out when the sphere
     settles it never sits behind the marks in the state a reader reads. */
  var gridA = 0, _grid = null;
  function gridLines() {
    if (_grid) return _grid;
    var out = [], i, k, th, n = 72, D = Math.PI / 180;
    for (k = -60; k <= 60; k += 30) {
      var y = Math.sin(k * D), rr = Math.sqrt(Math.max(0, 1 - y * y)), line = [];
      for (i = 0; i <= n; i++) {
        th = i / n * Math.PI * 2;
        line.push([Math.cos(th) * rr, y, Math.sin(th) * rr]);
      }
      out.push(line);
    }
    for (k = 0; k < 180; k += 30) {
      var ca = Math.cos(k * D), sa = Math.sin(k * D), l2 = [];
      for (i = 0; i <= n; i++) {
        th = i / n * Math.PI * 2;
        l2.push([Math.cos(th) * ca, Math.sin(th), Math.cos(th) * sa]);
      }
      out.push(l2);
    }
    return (_grid = out);
  }
  function drawGraticule(a) {
    if (a < 0.01) return;
    var lines = gridLines();
    ctx.save();
    ctx.strokeStyle = tone2(C.edge, 0.5 * a);
    ctx.lineWidth = 1;
    ctx.setLineDash([1, 3]);
    for (var g = 0; g < lines.length; g++) {
      /* the equator is the reference the eye holds onto while the sphere
         turns, so it alone is drawn solid, a second pass below */
      if (g === 2) continue;
      var line = lines[g], started = false;
      ctx.beginPath();
      for (var i = 0; i < line.length; i++) {
        var v = line[i];
        var x1 = v[0] * _cy1 + v[2] * _sy1;
        var z1 = -v[0] * _sy1 + v[2] * _cy1;
        if (v[1] * _sp1 + z1 * _cp1 < 0.02) { started = false; continue; }
        var sx = cx + x1 * _r1, sy = cy - (v[1] * _cp1 - z1 * _sp1) * _r1;
        if (!started) { ctx.moveTo(sx, sy); started = true; }
        else ctx.lineTo(sx, sy);
      }
      ctx.stroke();
    }
    ctx.setLineDash([]);
    ctx.strokeStyle = tone2(C.edge, 0.7 * a);
    var eq = lines[2], est = false;
    ctx.beginPath();
    for (var e2 = 0; e2 < eq.length; e2++) {
      var ev = eq[e2];
      var ex1 = ev[0] * _cy1 + ev[2] * _sy1;
      var ez1 = -ev[0] * _sy1 + ev[2] * _cy1;
      if (ev[1] * _sp1 + ez1 * _cp1 < 0.02) { est = false; continue; }
      var esx = cx + ex1 * _r1, esy = cy - (ev[1] * _cp1 - ez1 * _sp1) * _r1;
      if (!est) { ctx.moveTo(esx, esy); est = true; }
      else ctx.lineTo(esx, esy);
    }
    ctx.stroke();
    /* the poles, crosshair-marked when they face the reader: the fixed points
       every meridian shares, which is exactly what makes them worth marking */
    for (var pv = -1; pv <= 1; pv += 2) {
      var pd = pv * _sp1; /* depth of the pole [0,pv,0] after rotation */
      if (pd < 0.02) continue;
      var psx = cx, psy = cy - (pv * _cp1) * _r1;
      ctx.beginPath();
      ctx.moveTo(psx - 5, psy); ctx.lineTo(psx + 5, psy);
      ctx.moveTo(psx, psy - 5); ctx.lineTo(psx, psy + 5);
      ctx.stroke();
    }
    ctx.setLineDash([1, 3]);
    ctx.restore();
  }

  /* The 37 headings that more than one document carries are the only marks
     whose position is a compromise: they sit at the mean of their documents
     rather than inside any one of them. They are now the only marks that
     leave the surface, by an amount that is their share count. Stop 04's
     argument, that averaging strands a heading between everything that owns
     it, stops being a sentence and becomes a shape. */
  function stemLen(n) { return 0.045 + 0.032 * (n - 1); }
  function drawStems(back) {
    var i, p, h, base, tip;
    ctx.save();
    ctx.lineWidth = 1.1;
    for (i = 0; i < pts.length; i++) {
      p = pts[i];
      if (p.tool && p.on) {
        /* the tether from the surface to the standing mark, in the tool
           colour, so altitude reads as construction rather than error */
        if ((p.sz < 0) !== back) continue;
        var tl = staged && staged.lit ? staged.lit(p) : (focus ? (p.r === focus ? 2.1 : 0.34) : 1);
        if (tl < 0.5) continue;
        base = screenOf([p.x / 1.13, p.y / 1.13, p.z / 1.13]);
        var tb = (p.sz / 1.13 + 1) / 2;
        ctx.strokeStyle = rgba(C.too, (0.25 + 0.45 * tb) * (back ? 0.45 : 1));
        ctx.beginPath();
        ctx.moveTo(base[0], base[1]);
        ctx.lineTo(p.sx, p.sy);
        ctx.stroke();
        continue;
      }
      if (p.shared < 2 || !p.on) continue;
      if ((p.sz < 0) !== back) continue;
      var lit = staged && staged.lit ? staged.lit(p) : (focus ? (p.r === focus ? 2.1 : 0.34) : 1);
      if (lit < 0.5) continue;
      h = 1 + stemLen(p.shared);
      base = screenOf([p.x, p.y, p.z]);
      var bx = base[0], by = base[1];
      tip = screenOf([p.x * h, p.y * h, p.z * h]);
      var t = (p.sz + 1) / 2;
      var a = (0.30 + 0.55 * t) * (back ? 0.45 : 1);
      ctx.strokeStyle = rgba(C.ref, a);
      ctx.beginPath();
      ctx.moveTo(bx, by);
      ctx.lineTo(tip[0], tip[1]);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(tip[0], tip[1], 1.5 + 0.6 * t, 0, Math.PI * 2);
      ctx.fillStyle = rgba(C.ref, Math.min(1, a + 0.15));
      ctx.fill();
    }
    ctx.restore();
  }

  /* a small circle of angular radius deg about a centre, drawn as the polygon
     it projects to. This is the construction line that turns "a document is an
     area" from a claim into something the reader can measure by eye. */
  function drawCap(g, deg, dash) {
    var c = [g.x, g.y, g.z];
    var up = Math.abs(c[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0];
    var e1 = nrm([up[1] * c[2] - up[2] * c[1],
                  up[2] * c[0] - up[0] * c[2],
                  up[0] * c[1] - up[1] * c[0]]);
    var e2 = nrm([c[1] * e1[2] - c[2] * e1[1],
                  c[2] * e1[0] - c[0] * e1[2],
                  c[0] * e1[1] - c[1] * e1[0]]);
    var rad = deg * Math.PI / 180, ca = Math.cos(rad), sa = Math.sin(rad);
    ctx.save();
    if (dash) ctx.setLineDash([3, 4]);
    ctx.strokeStyle = rgba(C.ink, 0.55);
    ctx.lineWidth = 1;
    var started = false;
    ctx.beginPath();
    for (var i = 0; i <= 96; i++) {
      var th = i / 96 * Math.PI * 2;
      var v = [c[0] * ca + (e1[0] * Math.cos(th) + e2[0] * Math.sin(th)) * sa,
               c[1] * ca + (e1[1] * Math.cos(th) + e2[1] * Math.sin(th)) * sa,
               c[2] * ca + (e1[2] * Math.cos(th) + e2[2] * Math.sin(th)) * sa];
      var s = screenOf(v);
      if (s[2] < -0.02) { started = false; continue; }
      if (!started) { ctx.moveTo(s[0], s[1]); started = true; }
      else ctx.lineTo(s[0], s[1]);
    }
    ctx.stroke();
    ctx.restore();
  }

  function drawParallel(y) {
    var r = Math.sqrt(Math.max(0, 1 - y * y));
    ctx.save();
    ctx.strokeStyle = rgba(C.ink, 0.6);
    ctx.lineWidth = 1.1;
    var started = false;
    ctx.beginPath();
    for (var i = 0; i <= 128; i++) {
      var th = i / 128 * Math.PI * 2;
      var s = screenOf([Math.cos(th) * r, y, Math.sin(th) * r]);
      if (s[2] < -0.02) { started = false; continue; }
      if (!started) { ctx.moveTo(s[0], s[1]); started = true; }
      else ctx.lineTo(s[0], s[1]);
    }
    ctx.stroke();
    ctx.restore();
  }

  /* a great-circle arc between two places, with a tick at its midpoint. Stop
     three calls it a ruler: it measures where the shared headings were put. */
  function drawArc(a, b, tick) {
    var A = nrm(a), B = nrm(b);
    var dot = Math.max(-1, Math.min(1, A[0] * B[0] + A[1] * B[1] + A[2] * B[2]));
    var om = Math.acos(dot), so = Math.sin(om) || 1e-6;
    ctx.save();
    ctx.strokeStyle = rgba(C.ink, 0.5);
    ctx.lineWidth = 1;
    var started = false;
    ctx.beginPath();
    for (var i = 0; i <= 64; i++) {
      var t = i / 64;
      var k1 = Math.sin((1 - t) * om) / so, k2 = Math.sin(t * om) / so;
      var s = screenOf([A[0] * k1 + B[0] * k2, A[1] * k1 + B[1] * k2,
                        A[2] * k1 + B[2] * k2]);
      if (s[2] < -0.02) { started = false; continue; }
      if (!started) { ctx.moveTo(s[0], s[1]); started = true; }
      else ctx.lineTo(s[0], s[1]);
    }
    ctx.stroke();
    if (tick) {
      var m = nrm([A[0] + B[0], A[1] + B[1], A[2] + B[2]]);
      var s2 = screenOf(m);
      if (s2[2] >= -0.02) {
        var mx = s2[0], my = s2[1];
        ctx.beginPath();
        ctx.moveTo(mx, my - 6); ctx.lineTo(mx, my + 6);
        ctx.strokeStyle = rgba(C.ink, 0.75);
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }
    }
    ctx.restore();
  }

  /* A chord between two documents the corpus links. Same great circle as the
     ruler above, quieter, and its tick is directional: it sits at 0.72 of the
     way toward the document being linked, perpendicular to the path, so a
     mutual pair reads as one chord ticked at both ends. Drawn only while a
     document is being pointed at, so it costs nothing at rest. */
  function drawChord(a, b, tickAB, tickBA) {
    var A = nrm([a.x, a.y, a.z]), B = nrm([b.x, b.y, b.z]);
    var dot = Math.max(-1, Math.min(1, A[0] * B[0] + A[1] * B[1] + A[2] * B[2]));
    var om = Math.acos(dot), so = Math.sin(om) || 1e-6;
    ctx.save();
    ctx.strokeStyle = tone2(C.ink, 0.34);
    ctx.lineWidth = 1;
    var started = false;
    ctx.beginPath();
    for (var i = 0; i <= 48; i++) {
      var t = i / 48;
      var k1 = Math.sin((1 - t) * om) / so, k2 = Math.sin(t * om) / so;
      var s = screenOf([A[0] * k1 + B[0] * k2, A[1] * k1 + B[1] * k2,
                        A[2] * k1 + B[2] * k2]);
      if (s[2] < -0.02) { started = false; continue; }
      if (!started) { ctx.moveTo(s[0], s[1]); started = true; }
      else { ctx.lineTo(s[0], s[1]); }
    }
    ctx.stroke();
    if (tickAB) chordTick(A, B, om, so, 0.72);
    if (tickBA) chordTick(A, B, om, so, 0.28);
    ctx.restore();
  }
  function chordTick(A, B, om, so, t) {
    var k1 = Math.sin((1 - t) * om) / so, k2 = Math.sin(t * om) / so;
    var k3 = Math.sin((1 - t - 0.02) * om) / so, k4 = Math.sin((t + 0.02) * om) / so;
    var s = screenOf([A[0] * k1 + B[0] * k2, A[1] * k1 + B[1] * k2,
                      A[2] * k1 + B[2] * k2]);
    if (s[2] < -0.02) return;
    var s2 = screenOf([A[0] * k3 + B[0] * k4, A[1] * k3 + B[1] * k4,
                       A[2] * k3 + B[2] * k4]);
    var dx = s2[0] - s[0], dy = s2[1] - s[1];
    var dl = Math.sqrt(dx * dx + dy * dy) || 1;
    var px = -dy / dl * 4, py = dx / dl * 4;
    ctx.beginPath();
    ctx.moveTo(s[0] - px, s[1] - py); ctx.lineTo(s[0] + px, s[1] + py);
    ctx.strokeStyle = tone2(C.ink, 0.55);
    ctx.lineWidth = 1.2;
    ctx.stroke();
  }

  /* great-circle arcs from one place to several, drawn dotted: the only lines
     on this sphere, and they are drawn only to show that the thing they
     connect is nowhere near what owns it */
  function drawFan(from, targets) {
    ctx.save();
    ctx.setLineDash([2, 5]);
    ctx.strokeStyle = rgba(C.ink, 0.46);
    ctx.lineWidth = 1;
    targets.forEach(function (g) {
      var a = nrm(from), b = nrm([g.x, g.y, g.z]);
      var dot = Math.max(-1, Math.min(1, a[0] * b[0] + a[1] * b[1] + a[2] * b[2]));
      var om = Math.acos(dot), so = Math.sin(om) || 1e-6;
      var started = false;
      ctx.beginPath();
      for (var i = 0; i <= 48; i++) {
        var t = i / 48;
        var k1 = Math.sin((1 - t) * om) / so, k2 = Math.sin(t * om) / so;
        var s = screenOf([a[0] * k1 + b[0] * k2, a[1] * k1 + b[1] * k2,
                          a[2] * k1 + b[2] * k2]);
        if (s[2] < -0.02) { started = false; continue; }
        if (!started) { ctx.moveTo(s[0], s[1]); started = true; }
        else ctx.lineTo(s[0], s[1]);
      }
      ctx.stroke();
    });
    ctx.restore();
  }

  var order = [];
  function draw() {
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    drawSilhouette();
    drawGraticule(gridA);
    drawStems(true);
    /* Flown in, the silhouette runs off the frame, so the document's own cap
       is drawn as the boundary the reader is inside. */
    if (focus) drawCap(focus, focusCapDeg(focus), true);

    (staged && staged.geom || []).forEach(function (g) {
      if (g.cap) drawCap(g.cap, g.deg, true);
      if (g.parallel !== undefined) drawParallel(g.parallel);
      if (g.fan) drawFan(g.fan, g.to);
      if (g.arc) drawArc(g.arc, g.to, g.tick);
    });
    /* pointing at a shared heading draws the measured fan to the documents
       that carry it: the relationship the placement recorded, shown only
       while it is asked about, and never inside an authored stop */
    if (hover && hover.own && hover.own.length && !staged && !focus) {
      var htg = [];
      for (var ho = 0; ho < hover.own.length; ho++) {
        var hg = bySlug[hover.own[ho]];
        if (hg) htg.push(hg);
      }
      if (htg.length) drawFan([hover.x, hover.y, hover.z], htg);
    }

    /* pointing at a document draws the links its prose records: a chord to
       each document it links or that links it, the tick nearer the linked
       one. Asked-for like the fan, and gone the moment the pointer moves on */
    var att = (hover && hover.r) || wlR;
    if (att && att.lk && att.lk.length && !staged && !focus) {
      for (var lc = 0; lc < att.lk.length; lc++) {
        var lke = att.lk[lc];
        drawChord(att, lke.g, lke.out, lke.into);
      }
    }

    /* leaders under the marks */
    ctx.strokeStyle = rgba(C.strong, 0.9);
    ctx.lineWidth = 1;
    for (var q = 0; q < labels.length; q++) {
      var L = labels[q];
      if (L.hidden || !L.lead) continue;
      var lp = L.p;
      ctx.beginPath();
      ctx.moveTo(lp.sx, lp.sy);
      ctx.lineTo(L.ax, L.ay);
      ctx.stroke();
    }

    if (order.length !== pts.length) order = pts.slice();
    order.sort(function (a, b) { return a.sz - b.sz; });

    var litFn = staged && staged.lit, toneFn = staged && staged.tone;
    for (var i = 0; i < order.length; i++) {
      var p = order[i];
      var t = (p.sz + 1) / 2;
      var boost = litFn ? litFn(p) : (p.on ? 1 : 0.14);
      if (!litFn && !p.on) boost = 0.14;
      if (filter && !litFn) boost = p.on ? 2.1 : 0.22;
      if (focus) boost = p.r === focus ? 2.1 : 0.34;
      /* the survey: while it holds a document, that territory carries the
         emphasis and the rest recedes a step, never below legibility */
      if (svy.on && svy.r && !litFn && !filter && !focus) {
        boost = p.r === svy.r ? 1.5 : 0.82;
      }
      /* a document name under the pointer lights its territory; relative,
         so an authored stop keeps its structure while the named cap comes
         forward. The connection drawn is the one the data records. */
      if (wlR && !focus) {
        boost = p.r === wlR ? Math.max(boost, 1.7) : boost * 0.55;
      }
      var a = (0.10 + 0.80 * t) * Math.min(2.4, boost);
      if (a < 0.02) continue;
      /* size follows heading level, which is what the first label claims */
      var lv = 4 - Math.min(4, p.lvl);
      var rad = (0.75 + lv * 0.3) + 2.0 * t;
      var isHover = hover === p && !peeked;
      var kin = hover && hover.r === p.r && !focus;
      var tone = toneFn ? toneFn(p) : null;
      if (focus) {
        /* the document keeps its encoding; the neighbours recede */
        if (p.r !== focus) tone = "field";
        else rad += 1.1;
      }
      if (filter && p.on && !litFn) { rad += 1.5; tone = "hit"; }
      if (isHover) { rad += 2.4; a = 1; }
      else if (kin) { a = Math.min(1, a + 0.2); }

      ctx.beginPath();
      ctx.arc(p.sx, p.sy, rad, 0, Math.PI * 2);
      if (tone === "warn" || tone === "hit") {
        ctx.fillStyle = tone2(tone === "hit" ? C.ind : C.ref, a); ctx.fill();
      } else if (tone === "ring") {
        /* counted by the label, so drawn as a ring a reader can point at */
        ctx.strokeStyle = tone2(C.ref, Math.min(1, a));
        ctx.lineWidth = 1.4; ctx.stroke();
      } else if (tone === "field") {
        /* the receded corpus, at the non-text-contrast token */
        ctx.fillStyle = tone2(C.edge, a); ctx.fill();
      } else if (tone === "ind") {
        ctx.fillStyle = tone2(C.ind, a); ctx.fill();
      } else if (p.r.surface === "course") {
        ctx.strokeStyle = tone2(C.cou, Math.min(1, a * 1.25));
        ctx.lineWidth = 1.15; ctx.stroke();
      } else if (p.r.kind === "Tool") {
        ctx.fillStyle = tone2(C.too, a); ctx.fill();
      } else {
        /* lighter accent, but not under the 3:1 floor for a keyed
           category: measured at the pixel, 4.4:1 on paper */
        ctx.fillStyle = tone2(C.ind, p.r.surface === "personal" ? a * 0.85 : a);
        ctx.fill();
      }
      if (!staged && p.seen) {
        /* a passage this browser has opened, ringed: the reader's own
           trail through the corpus, kept in this browser alone */
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, rad + 2.6, 0, Math.PI * 2);
        ctx.strokeStyle = tone2(C.ink, Math.min(0.55, 0.2 + 0.35 * t));
        ctx.lineWidth = 1;
        ctx.stroke();
      }
      if (isHover) {
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, rad + 4.5, 0, Math.PI * 2);
        ctx.strokeStyle = rgba(C.ink, 0.6); ctx.lineWidth = 1; ctx.stroke();
      } else if (staged && staged.name && staged.name.length <= 2 &&
                 staged.name.indexOf(p) > -1) {
        /* one mark, named: findable in a field of 1,246 others */
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, rad + 5.5, 0, Math.PI * 2);
        ctx.strokeStyle = rgba(C.ink, 0.7); ctx.lineWidth = 1; ctx.stroke();
      }
    }
    drawStems(false);
  }

  /* --------------------------------------------------------- labels --- */
  function labelMax() { return focus ? 136 : 190; }
  var labels = [], labelAt = 0, labelBoxes = [], namedNote = false;
  var COL = 132;
  /* the steepest a leader may run, as a rise over its horizontal reach */
  var SLOPE = 0.85;

  function gap() { return focus ? 15 : 22; }
  /* the crumb and the hint own the top and bottom bands */
  function padTop() { return focus || (staged && staged.name) ? 30 : 12; }
  function padBot() { return narrow() ? 12 : 34; }
  function ringX() {
    /* Clear of the thing being named, not of the whole sphere: flown in, the
       cap is smaller than the frame even when the sphere is not. */
    if (focus) {
      var capR = R() * Math.sin(focusCapDeg(focus) * Math.PI / 180);
      return Math.max(70, Math.min(capR + 18, cx - 108));
    }
    return tiny() ? cx - 8 : Math.min(R() + 24, Math.max(120, cx - 92));
  }

  function labelText(p, full) {
    if (full) return p.t;
    /* Flown in, the panel carries every heading in full, so a name on the
       sphere only has to identify a dot, and a short one fits beside it. */
    var lim = focus ? (tiny() ? 20 : 24) : tiny() ? 30 : 44;
    return p.t.length > lim
      ? p.t.slice(0, lim - 2).replace(/[ ,:;—-]+$/, "") + "…" : p.t;
  }
  var _mc = {}, _mcn = 0;
  function measure(text, font) {
    var k = font + "|" + text;
    if (_mc[k] !== undefined) return _mc[k];
    if (_mcn > 900) { _mc = {}; _mcn = 0; }
    ctx.save(); ctx.font = font;
    var w = ctx.measureText(text).width;
    ctx.restore();
    _mcn++;
    return (_mc[k] = w);
  }
  var _font = null;
  function labelFont() {
    if (_font) return _font;
    var probe = document.createElement("a");
    probe.className = "alab";
    probe.style.visibility = "hidden";
    labelBox.appendChild(probe);
    var s = getComputedStyle(probe);
    var f = s.fontWeight + " " + s.fontSize + " " + s.fontFamily;
    labelBox.removeChild(probe);
    _font = f.indexOf("px") > -1 ? f : "400 12px InterVar, sans-serif";
    return _font;
  }

  /* Which marks earn a name. Occlusion first — a mark on the far side is not a
     candidate at all — then relevance: a mark the current label is about, or
     one the search matched, or a shallower heading, outranks a fourth-level
     heading nobody asked about. */
  function priority(p) {
    /* A staged view names only what its label is talking about. Ten unrelated
       headings scattered over a claim about something else is noise dressed as
       richness. */
    if (staged && staged.lit) {
      if (!staged.name || staged.name.indexOf(p) < 0) return -1;
      return 10 + p.sz;
    }
    if (p.sz < 0.18) return -1;
    if (!p.on) return -1;
    var s = p.sz;
    if (focus && p.r === focus) s += 2;
    if (filter && p.on) s += 1.5;
    if (!filter && !focus) s += (4 - Math.min(4, p.lvl)) * 0.12;
    if (p.shared > 1) s += 0.25;
    return s;
  }

  function pickLabels() {
    /* At phone width there is no clear ring to put type in, so the names go
       to the index: one caption a reader can read beats eight they cannot. */
    if (tiny() && !(staged && staged.name)) return [];

    var cand = [];
    for (var i = 0; i < pts.length; i++) {
      var pr = priority(pts[i]);
      if (pr < 0) continue;
      cand.push({ p: pts[i], score: pr });
    }
    if (!cand.length) return [];
    cand.sort(function (a, b) { return b.score - a.score; });

    var g = gap();
    var top = padTop(), bot = H - padBot();
    var perCol = Math.max(3, Math.floor((bot - top) / g));
    var side = Math.max(60, cx - ringX());
    var maxBands = Math.max(1, Math.min(3, Math.floor(side / COL)));
    var want = focus ? focus.n
      : tiny() ? 3 : (staged && staged.name) ? staged.name.length
      : W > 1180 ? 16 : narrow() ? 8 : 12;
    var cap = Math.min(cand.length, perCol * 2 * maxBands, want);

    var take = cand.slice(0, cap).map(function (c) { return c.p; });
    var font = labelFont(), full = !!(staged && staged.full);
    take.forEach(function (p) {
      p.ltxt = labelText(p, full);
      p.lw = Math.min(labelMax(), measure(p.ltxt, font) + 10);
    });
    return take;
  }

  /* Two jobs on two clocks. Selection is throttled: a name that appears and
     vanishes twice a second is worse than no name. Placement runs every frame,
     because the marks do, and a pinned ladder sweeps its leaders across each
     other as they travel. */
  function placeLadder(take) {
    if (!take || !take.length) return [];
    var g = gap();
    var top = padTop(), bot = H - padBot();
    var perCol = Math.max(3, Math.floor((bot - top) / g));
    var side = Math.max(60, cx - ringX());
    var maxBands = Math.max(1, Math.min(3, Math.floor(side / COL)));
    var out = [];
    /* First, name marks where they stand: a heading beside its own dot needs
       no leader, so it cannot cross one. Only what will not fit goes to the
       ladder. */
    var placedBoxes = [], rest = [];
    var inPlaceOk = focus || (staged && staged.name) || !tiny();
    for (var ip = 0; ip < take.length && inPlaceOk; ip++) {
      var q0 = take[ip];
      var w0 = q0.lw || 120, h0 = g - 2;
      var opts = q0.sx < cx
        ? [[q0.sx - 10 - w0, true], [q0.sx + 10, false]]
        : [[q0.sx + 10, false], [q0.sx - 10 - w0, true]];
      var set = false;
      for (var oi = 0; oi < opts.length && !set; oi++) {
        var bx0 = opts[oi][0], by0 = q0.sy - h0 / 2;
        if (bx0 < 3 || bx0 + w0 > W - 3 || by0 < top || by0 + h0 > bot) continue;
        /* Inside a document, a name lying across the cap is the point. Outside
           one, it is a name lying across nine hundred other marks, so the
           whole corpus keeps its names in the clear ring and the ladder takes
           anything that will not fit there. */
        if (!focus) {
          var mx0 = bx0 + w0 / 2, dxr = mx0 - cx, dyr = q0.sy - cy;
          if (Math.sqrt(dxr * dxr + dyr * dyr) < R() * 0.92) continue;
        }
        var bad0 = false;
        for (var pb = 0; pb < placedBoxes.length; pb++) {
          var o0 = placedBoxes[pb];
          if (!(bx0 + w0 < o0[0] - 6 || bx0 > o0[2] + 6 ||
                by0 + h0 < o0[1] - 3 || by0 > o0[3] + 3)) { bad0 = true; break; }
        }
        if (bad0) continue;
        placedBoxes.push([bx0, by0, bx0 + w0, by0 + h0]);
        q0.lft = opts[oi][1];
        q0.lx = opts[oi][1] ? bx0 + w0 : bx0;
        q0.ly = q0.sy;
        out.push(q0);
        set = true;
      }
      if (!set) rest.push(q0);
    }
    if (!inPlaceOk) rest = take.slice();

    [true, false].forEach(function (isLeft) {
      var col = rest.filter(function (p) { return (p.sx < cx) === isLeft; });
      if (!col.length) return;
      var nb = Math.max(1, Math.min(maxBands, Math.ceil(col.length / perCol)));
      /* Bands fill by how far out the mark already is, so a leader that
         reaches further starts further out. */
      col.sort(function (a, b) { return isLeft ? a.sx - b.sx : b.sx - a.sx; });
      var per = Math.ceil(col.length / nb);
      for (var b = 0; b < nb; b++) {
        /* inside a band, names keep their marks' vertical order */
        var slice = col.slice(b * per, (b + 1) * per)
          .sort(function (a, b2) { return a.sy - b2.sy; });
        var band = nb - 1 - b;
        var lx = isLeft ? cx - ringX() - band * COL : cx + ringX() + band * COL;
        var y = top;
        for (var k = 0; k < slice.length; k++) {
          var q = slice[k];
          y = Math.max(y, Math.min(q.sy, bot - (slice.length - k) * g));
          if (y > bot) { q.lx = undefined; continue; }
          /* Vertical order alone does not stop a hairball: one near-vertical
             leader slices across every shallow one beside it. Capping the
             slope is what makes crossing rare rather than unlikely. */
          var run = Math.abs(lx - q.sx);
          if (Math.abs(y - q.sy) > SLOPE * run + 6) { q.lx = undefined; continue; }
          var qw = q.lw || 120, qbx = isLeft ? lx - qw : lx, qby = y - (g - 2) / 2;
          var hitp = false;
          for (var pb2 = 0; pb2 < placedBoxes.length; pb2++) {
            var o2 = placedBoxes[pb2];
            if (!(qbx + qw < o2[0] - 6 || qbx > o2[2] + 6 ||
                  qby + g - 2 < o2[1] - 3 || qby > o2[3] + 3)) { hitp = true; break; }
          }
          if (hitp) { q.lx = undefined; continue; }
          placedBoxes.push([qbx, qby, qbx + qw, qby + g - 2]);
          q.lft = isLeft;
          q.lx = lx;
          q.ly = y;
          out.push(q);
          y += g;
        }
      }
    });
    return out;
  }

  var chosen = [];
  function syncLabels(force) {
    var now = performance.now();
    if (force || now - labelAt > 900) {
      labelAt = now;
      chosen = pickLabels();
      var want = placeLadder(chosen), have = {};
      for (var i = 0; i < labels.length; i++) have[labels[i].p.href] = labels[i];
      var keep = [];
      for (var j = 0; j < want.length; j++) {
        var p = want[j], ex = have[p.href];
        if (ex) {
          if (ex.txt !== p.ltxt) { ex.el.textContent = p.ltxt; ex.txt = p.ltxt; ex.w = 0; }
          keep.push(ex); delete have[p.href]; continue;
        }
        var el = document.createElement("a");
        el.className = "alab" + (focus ? " tight" : "") +
          ((staged && staged.full) ? " full" : "");
        el.href = p.href;
        el.textContent = p.ltxt;
        el.setAttribute("tabindex", "-1");
        el.setAttribute("aria-hidden", "true");
        labelBox.appendChild(el);
        (function (n) {
          requestAnimationFrame(function () { n.classList.add("on"); });
        })(el);
        keep.push({ p: p, el: el, txt: p.ltxt, w: 0, h: 0 });
      }
      for (var t in have) {
        if (!Object.prototype.hasOwnProperty.call(have, t)) continue;
        (function (l) {
          /* retired at once rather than faded: a label on its way out still
             occupies its box, and the one arriving there cannot see it */
          l.el.style.transition = "none";
          l.el.style.opacity = "0";
          l.el.classList.remove("on");
          setTimeout(function () {
            if (l.el.parentNode) l.el.parentNode.removeChild(l.el);
          }, 40);
        })(have[t]);
      }
      labels = keep;
      for (var z = 0; z < labels.length; z++) labels[z].latch = false;
    } else {
      /* same names, current positions */
      placeLadder(chosen);
    }
    var kept = [];
    labelBoxes = [];
    for (var m = 0; m < labels.length; m++) {
      var L = labels[m];
      if (L.p.lx === undefined) {
        L.hidden = true; L.el.classList.add("off"); L.el.style.opacity = 0; continue;
      }
      L.el.classList.toggle("lft", !!L.p.lft);
      /* Measured once, not once a frame: offsetWidth in the draw loop forced
         a synchronous layout sixty times a second. */
      if (!L.w) { L.w = L.el.offsetWidth || L.p.lw || 120; L.h = L.el.offsetHeight || 17; }
      var w = L.w, h = L.h;
      var lx = L.p.lft ? L.p.lx - w : L.p.lx;
      lx = Math.max(2, Math.min(W - w - 2, lx));
      var ly = L.p.ly - h / 2;
      var box = [lx, ly, lx + w, ly + h];
      /* Latched, and hidden without a fade: fading leaves the overlap on
         screen for the length of the fade, and an unlatched test would blink
         as the sphere turned. A name that loses its place waits. */
      var clash = L.latch;
      for (var n = 0; !clash && n < kept.length; n++) {
        var o = kept[n];
        if (!(box[2] < o[0] - 6 || box[0] > o[2] + 6 ||
              box[3] < o[1] - 3 || box[1] > o[3] + 3)) { clash = true; }
      }
      if (clash) L.latch = true;
      L.el.classList.toggle("off", clash);
      L.el.style.transform = "translate(" + Math.round(lx) + "px," + Math.round(ly) + "px)";
      L.hidden = clash;
      L.el.style.opacity = clash ? 0 : Math.max(0, Math.min(1, (L.p.sz - 0.02) * 4.4));
      /* a name sitting on its own mark needs no line to it */
      L.ax = L.p.lft ? box[2] + 3 : box[0] - 3;
      L.ay = L.p.ly;
      L.lead = Math.abs(L.ax - L.p.sx) + Math.abs(L.ay - L.p.sy) > 14;
      if (!clash) { kept.push(box); labelBoxes.push(box); }
    }
    /* Reported from what actually survived the overlap pass, not from what was
       created: a claim about how much is named has to count what is legible. */
    if (namedNote && focus) {
      var where = narrow() ? "below" : "beside the sphere";
      hintEl.textContent = kept.length >= focus.n
        ? "All " + focus.n + " sections named. Click any mark to open it."
        : kept.length === 0
          ? "All " + focus.n + " sections of this document are listed " + where + "."
          : kept.length + " of " + focus.n + " named here. Every one of them is listed " +
            where + ".";
    }
  }

  /* ---------------------------------------------------- region names -- */
  var rlabels = [], rlabelAt = 0;
  function syncRegions(force) {
    var now = performance.now();
    if (force || now - rlabelAt > 900) {
      rlabelAt = now;
      var cand = regions.filter(function (r) {
        if (tiny()) return false;
        if (focus) return r === focus;
        if (staged && staged.lit) {
          return !!(staged.regions && staged.regions.indexOf(r) > -1);
        }
        /* no caption over a territory with nothing in it */
        if (filter) return r.sz > 0.5 && r.items.some(function (p) { return p.on; });
        return r.sz > 0.5 && r.n > 2;
      }).sort(function (a, b) {
        /* the document the survey is holding is named first, always */
        if (svy.on && svy.r) {
          if (a === svy.r) return -1;
          if (b === svy.r) return 1;
        }
        /* captions are the only words on the sphere: the independent work
           outranks a bigger course reference for them */
        var ai = a.surface === "independent" ? 1 : 0;
        var bi = b.surface === "independent" ? 1 : 0;
        if (ai !== bi) return bi - ai;
        return b.sz - a.sz;
      });
      var font = "660 11px " + (labelFont().split(" ").slice(2).join(" ") || "InterVar, sans-serif");
      var want = [], boxes = labelBoxes.slice();
      var max = (staged && staged.regionAll) ? 7
        : (focus || (staged && staged.regions)) ? 3 : (W > 1180 ? 3 : 2);
      for (var i = 0; i < cand.length && want.length < max; i++) {
        var r = cand[i];
        if (r.sz < 0.1) continue;
        /* a long name in tracked capitals runs clear across the sphere */
        var ttl = r.title.length > 26 ? r.title.slice(0, 24).replace(/[ ,:;—-]+$/, "") + "…" : r.title;
        r.cap = ttl;
        var w = measure(ttl.toUpperCase(), font) + ttl.length * 1.5 + 10;
        var box = [r.sx - w / 2, r.sy - 11, r.sx + w / 2, r.sy + 11];
        if (box[0] < 6 || box[2] > W - 6 || box[1] < 6 || box[3] > H - 6) continue;
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
        el.textContent = rr.cap || rr.title;
        el.setAttribute("tabindex", "-1");
        el.setAttribute("aria-hidden", "true");
        labelBox.appendChild(el);
        (function (n) {
          requestAnimationFrame(function () { n.classList.add("on"); });
        })(el);
        keep.push({ r: rr, el: el, w: 0 });
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
    /* A caption chosen when it was clear drifts into type as the sphere
       turns, so the test is part of the frame and the caption stands down. */
    var rboxes = labelBoxes.slice();
    for (var n2 = 0; n2 < rlabels.length; n2++) {
      var L = rlabels[n2];
      if (!L.w) L.w = L.el.offsetWidth || 120;
      var bx = Math.round(L.r.sx - L.w / 2), byy = Math.round(L.r.sy - 8);
      var rb = [bx, byy, bx + L.w, byy + 16];
      var bad = rb[0] < 4 || rb[2] > W - 4 || rb[1] < 2 || rb[3] > H - 2;
      for (var kk = 0; !bad && kk < rboxes.length; kk++) {
        var ob = rboxes[kk];
        if (!(rb[2] < ob[0] - 10 || rb[0] > ob[2] + 10 ||
              rb[3] < ob[1] - 6 || rb[1] > ob[3] + 6)) bad = true;
      }
      L.el.style.transform = "translate(" + bx + "px," + byy + "px)";
      L.el.style.opacity = bad ? 0
        : Math.max(0, Math.min(0.95, (L.r.sz - 0.3) * 2.8));
      L.el.classList.toggle("cur", !!(hover && hover.r === L.r));
      if (!bad) rboxes.push(rb);
    }
  }

  /* --------------------------------------------------------- hover ---- */
  function hit(mx, my) {
    var best = null, bd = 16 * 16;
    for (var i = 0; i < pts.length; i++) {
      var p = pts[i];
      if (p.sz <= 0 || !p.on) continue;
      if (focus && p.r !== focus) continue;
      var dx = p.sx - mx, dy = p.sy - my, d = dx * dx + dy * dy;
      if (d < bd) { bd = d; best = p; }
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
    if (!p) { card.hidden = true; stage.classList.remove("hot"); invalidate(); return; }
    cardT.textContent = p.t;
    cardD.textContent = p.r.title + "  ·  " + p.r.kind +
      (p.shared > 1 ? "  ·  in " + p.shared + " documents" : "");
    card.hidden = false;
    stage.classList.add("hot");
    placeCard();
    invalidate();
  }

  /* ------------------------------------------------------- pointer ---- */
  /* The staged view is live. Refusing the pointer made the first wall label a
     liar: it says the passage opens on a click. Turning it by hand steps out
     of the authored framing and offers it back. */
  function local(e) {
    var r = cv.getBoundingClientRect();
    return [e.clientX - r.left, e.clientY - r.top];
  }
  cv.addEventListener("pointerdown", function (e) {
    dragging = true; moved = 0; tween = null;
    driftUntil = 0;
    var l = local(e); lastX = l[0]; lastY = l[1];
    try { cv.setPointerCapture(e.pointerId); } catch (x) {}
    stage.classList.add("drag");
    kick();
  });
  cv.addEventListener("pointermove", function (e) {
    var l = local(e);
    if (dragging) {
      var dx = l[0] - lastX, dy = l[1] - lastY;
      moved += Math.abs(dx) + Math.abs(dy);
      cam.yaw += dx * 0.006;
      cam.pitch = Math.max(-1.15, Math.min(1.15, cam.pitch + dy * 0.005));
      vYaw = dx * 0.09; vPitch = dy * 0.07;
      lastX = l[0]; lastY = l[1];
      if (moved > 8 && mode === "tour" && !turned) markTurned();
      setHover(null);
      invalidate();
    } else {
      setHover(hit(l[0], l[1]));
    }
  });
  function endDrag(e) {
    if (!dragging) return;
    dragging = false;
    stage.classList.remove("drag");
    try { cv.releasePointerCapture(e.pointerId); } catch (x) {}
    kick();
  }
  cv.addEventListener("pointerup", function (e) {
    var wasDrag = moved > 6;
    endDrag(e);
    if (wasDrag) return;
    var l = local(e), p = hit(l[0], l[1]);
    if (p) { window.location.href = p.href; return; }
    if (mode === "tour") return;
    /* an empty patch inside a document's territory selects that document */
    if (!focus) {
      var g = nearestRegion(l[0], l[1]);
      if (g) setFocus(g);
    }
  });
  cv.addEventListener("pointercancel", endDrag);
  cv.addEventListener("pointerleave", function () { if (!dragging) setHover(null); });

  function nearestRegion(mx, my) {
    var best = null, bd = 70 * 70;
    for (var i = 0; i < regions.length; i++) {
      var g = regions[i];
      if (g.sz <= 0.1) continue;
      var dx = g.sx - mx, dy = g.sy - my, d = dx * dx + dy * dy;
      if (d < bd) { bd = d; best = g; }
    }
    return best;
  }

  function markTurned() {
    turned = true;
    if (restore) restore.hidden = false;
    if (caption) caption.textContent = "You have turned it yourself.";
  }
  if (restore) {
    restore.addEventListener("click", function () {
      turned = false;
      restore.hidden = true;
      if (caption) caption.textContent = "";
      if (mode === "tour") showStage(plates[step].getAttribute("data-stage"));
      else setFocus(focus);
    });
  }

  /* ---------------------------------------------------------- focus --- */
  /* The cap the reader is inside, in degrees, from the marks themselves. */
  function focusCapDeg(g) {
    if (g.capDeg !== undefined) return g.capDeg;
    var m = 0;
    for (var i = 0; i < g.items.length; i++) {
      var p = g.items[i];
      var d = p.x * g.x + p.y * g.y + p.z * g.z;
      var a = Math.acos(Math.max(-1, Math.min(1, d))) * 180 / Math.PI;
      if (a > m) m = a;
    }
    return (g.capDeg = m);
  }

  function setFocus(g) {
    focus = g;
    if (g) {
      var f = facing([g.x, g.y, g.z]);
      /* the cap fills the stage, but never so far that the silhouette leaves
         the frame: the "on a sphere" cue matters most at depth */
      var want = Math.max(1.2, Math.min(2.3, 2.35 - Math.sqrt(g.n) * 0.085));
      var lim = (Math.min(cx, cy) - 10) / (R0 || 1);
      flyTo({ yaw: f.yaw, pitch: f.pitch, zoom: Math.min(want, Math.max(1.15, lim)) }, 1000);
      crumb.hidden = false;
      crumbNow.textContent = g.title + "  ·  " + g.n +
        (g.n === 1 ? " section" : " sections");
      hintEl.textContent = "";
      namedNote = true;
      showDoc(g);
      document.body.classList.add("atlas-indoc");
      [].forEach.call(list.querySelectorAll(".areg"), function (s) {
        s.classList.toggle("cur", s.getAttribute("data-s") === g.slug);
      });
    } else {
      flyTo({ pitch: -0.28, zoom: 1 }, 850);
      crumb.hidden = true;
      namedNote = false;
      hintEl.textContent = defaultHint();
      showDoc(null);
      document.body.classList.remove("atlas-indoc");
      [].forEach.call(list.querySelectorAll(".areg"), function (s) {
        s.classList.remove("cur");
      });
    }
    syncLabels(true); syncRegions(true); invalidate();
  }

  /* The panel carries the focused document in full: every section as a real
     link, in order. The sphere names what it has room for and says how many;
     the panel is where "every one of them" is kept, and the only version of a
     flight a keyboard can take. */
  function showDoc(g) {
    if (!docPanel) return;
    if (!g) {
      docPanel.hidden = true; docPanel.innerHTML = "";
      if (mode === "free") showDocList();
      return;
    }
    var h = document.createElement("div");
    h.className = "adoc-h";
    var a = document.createElement("a");
    a.href = g.url; a.className = "adoc-t"; a.textContent = g.title;
    var m = document.createElement("p");
    m.className = "adoc-m"; m.textContent = g.meta;
    var n = document.createElement("p");
    n.className = "adoc-n";
    n.textContent = g.n + (g.n === 1 ? " section" : " sections") + ", all listed here";
    h.appendChild(a); h.appendChild(m); h.appendChild(n);
    var ol = document.createElement("ol");
    ol.className = "adoc-l";
    g.items.forEach(function (p) {
      var li = document.createElement("li");
      li.setAttribute("data-l", String(p.lvl));
      var link = document.createElement("a");
      link.href = p.href;
      link.textContent = p.t;
      link.addEventListener("focus", function () { setHover(p); });
      link.addEventListener("blur", function () { setHover(null); });
      link.addEventListener("mouseenter", function () { setHover(p); });
      link.addEventListener("mouseleave", function () { setHover(null); });
      li.appendChild(link);
      ol.appendChild(li);
    });
    docPanel.innerHTML = "";
    docPanel.appendChild(h);
    docPanel.appendChild(ol);
    docPanel.hidden = false;
  }

  /* The hint said "choose a document" over a page with no visible list of
     documents. Free mode names all fifty, in library order, which is the order
     stop five explains. Sphere, document, section becomes three visible steps
     rather than a model the reader has to infer. */
  function showDocList() {
    if (!docPanel || focus) return;
    var h = document.createElement("div");
    h.className = "adoc-h";
    var t = document.createElement("p");
    t.className = "adoc-k";
    t.textContent = "Fifty documents";
    var n = document.createElement("p");
    n.className = "adoc-n";
    n.textContent = "Independent work first. Choose one and the camera flies to it.";
    h.appendChild(t); h.appendChild(n);
    var ol = document.createElement("ul");
    ol.className = "adoc-r";
    regions.forEach(function (r) {
      var li = document.createElement("li");
      var b = document.createElement("button");
      b.type = "button";
      b.className = "adoc-b";
      b.setAttribute("data-surface", r.surface);
      var nm = document.createElement("span");
      nm.className = "adoc-bt";
      nm.textContent = r.title;
      var ct = document.createElement("span");
      ct.className = "adoc-bn";
      ct.textContent = String(r.n);
      b.appendChild(nm); b.appendChild(ct);
      b.addEventListener("click", function () { setFocus(r); });
      b.addEventListener("mouseenter", function () { peek(r); });
      b.addEventListener("mouseleave", function () { peek(null); });
      b.addEventListener("focus", function () { peek(r); });
      b.addEventListener("blur", function () { peek(null); });
      li.appendChild(b);
      ol.appendChild(li);
    });
    docPanel.innerHTML = "";
    docPanel.appendChild(h);
    docPanel.appendChild(ol);
    docPanel.hidden = false;
  }
  /* pointing at a name lights its territory: one set of fifty, two views */
  var peeked = null;
  function peek(r) {
    if (peeked === r) return;
    peeked = r;
    setHover(r && r.items.length ? r.items[0] : null);
    invalidate();
  }

  function defaultHint() {
    return narrow() ? "Drag to turn it. Choose a document below to fly to it."
      : "Drag to turn it. Point at a mark to read the section, click to open it. Choose a document to fly in.";
  }
  document.getElementById("acrumbout").addEventListener("click", function () {
    setFocus(null);
  });

  /* ---------------------------------------------------------- stages -- */
  function showStage(name, snap) {
    staged = STAGES[name] ? STAGES[name]() : null;
    /* On a phone the stage is short and the hint and key sit close under it:
       a staged zoom past 1 pushes the sphere's lower quarter beneath them.
       The composition is the desktop's; the phone gets the whole object. */
    if (staged && staged.cam && narrow()) {
      staged.cam.zoom = Math.min(staged.cam.zoom, 1);
    }
    if (staged && staged.cam) {
      if (snap) {
        /* The opening view is a composed picture, not an arrival: flying into
           it redraws 1,247 marks for 1,100ms and there is no earlier view to
           have been following. Moves between stops still fly, because there
           the motion is what says the two pictures are of one object. */
        cam.yaw = staged.cam.yaw; cam.pitch = staged.cam.pitch;
        cam.zoom = staged.cam.zoom; tween = null;
        project();
      } else flyTo(staged.cam, 1100);
    }
    if (staged && staged.key && staged.key.length) {
      stageKey.hidden = false;
      stageKey.innerHTML = "";
      staged.key.forEach(function (k) {
        var s = document.createElement("span");
        s.className = "sk sk-" + k[0];
        s.appendChild(document.createTextNode(k[1]));
        stageKey.appendChild(s);
      });
    } else {
      stageKey.hidden = true;
      stageKey.textContent = "";
    }
    syncLabels(true); syncRegions(true); invalidate();
  }

  function setStep(i, push) {
    step = Math.max(0, Math.min(plates.length - 1, i));
    turned = false;
    if (restore) restore.hidden = true;
    if (caption) caption.textContent = "";
    plates.forEach(function (pl, k) {
      pl.hidden = k !== step;
      pl.setAttribute("aria-hidden", String(k !== step));
    });
    [].forEach.call(guide.querySelectorAll("a"), function (a, k) {
      if (k === step) a.setAttribute("aria-current", "step");
      else a.removeAttribute("aria-current");
    });
    var prev = document.getElementById("pprev"), next = document.getElementById("pnext");
    prev.setAttribute("aria-disabled", String(step === 0));
    prev.href = "#label-" + Math.max(1, step);
    var lastStep = step === plates.length - 1;
    if (lastStep) {
      next.textContent = "Start exploring →";
      next.href = "#atlas";
    } else {
      next.textContent = "Next label →";
      next.href = "#label-" + (step + 2);
    }
    /* the last plate hands over, so it must not name an arrow that goes
       nowhere; both hints name what is true of a staged view */
    hintEl.textContent = lastStep
      ? "Drag the sphere, or take the whole corpus below."
      : "Drag to turn it, or press → for the next label.";
    showStage(plates[step].getAttribute("data-stage"), !booted);
    if (push && booted) {
      try { history.replaceState(null, "", "#label-" + (step + 1)); } catch (e) {}
    }
    try { sessionStorage.setItem("atlas.step", String(step)); } catch (e) {}
  }

  function toFree(remember) {
    mode = "free";
    var wasGlobe = bGlobe.getAttribute("aria-pressed") === "true";
    staged = null;
    turned = false;
    if (restore) restore.hidden = true;
    if (caption) caption.textContent = "";
    document.body.classList.add("atlas-free");
    document.body.classList.remove("atlas-indoc");
    plates.forEach(function (pl) { pl.hidden = true; });
    guide.hidden = true;
    navbar.hidden = true;
    freebar.hidden = false;
    stageKey.hidden = true;
    hintEl.textContent = defaultHint();
    flyTo({ pitch: -0.28, zoom: 1 }, 800);
    driftUntil = performance.now() + ((reduced || narrow()) ? 0 : 5200);
    showDocList();
    setView(wasGlobe);
    if (remember) {
      try { localStorage.setItem("atlas.seen", "1"); } catch (e) {}
    }
    syncLabels(true); syncRegions(true); invalidate();
  }
  function toTour(i) {
    mode = "tour";
    focus = null;
    showDoc(null);
    document.body.classList.remove("atlas-free");
    document.body.classList.remove("atlas-indoc");
    guide.hidden = false;
    navbar.hidden = false;
    freebar.hidden = true;
    crumb.hidden = true;
    if (results) { results.hidden = true; results.innerHTML = ""; }
    setStep(i || 0, true);
    setView(bGlobe.getAttribute("aria-pressed") === "true");
  }

  document.getElementById("pnext").addEventListener("click", function (e) {
    e.preventDefault();
    if (step === plates.length - 1) toFree(true); else setStep(step + 1, true);
  });
  document.getElementById("pprev").addEventListener("click", function (e) {
    e.preventDefault();
    if (step > 0) setStep(step - 1, true);
  });
  document.getElementById("pskip").addEventListener("click", function (e) {
    e.preventDefault(); toFree(true);
    var q0 = document.getElementById("aq");
    if (q0) q0.focus();
  });
  document.getElementById("preplay").addEventListener("click", function () {
    toTour(0);
    var b = document.getElementById("pnext");
    if (b) b.focus();
  });
  [].forEach.call(guide.querySelectorAll("a"), function (a, k) {
    a.addEventListener("click", function (e) { e.preventDefault(); setStep(k, true); });
  });

  /* -------------------------------------------------------- search ---- */
  /* A query used to change one sentence and leave the sphere alone, so it
     produced an emptier picture rather than a more informative one. It now
     lights the hits, swings the camera to their centre of mass, and writes a
     list of real anchors a keyboard can walk. */
  var q = document.getElementById("aq");
  var searchTimer = 0;
  function runSearch() {
    filter = q.value.trim().toLowerCase();
    if (filter && mode === "tour") toFree(true);
    shown = 0;
    var hits = [], sum = [0, 0, 0];
    for (var i = 0; i < pts.length; i++) {
      var p = pts[i];
      p.on = !filter || p.lt.indexOf(filter) > -1 ||
        p.r.title.toLowerCase().indexOf(filter) > -1;
      if (p.on) {
        shown++;
        if (filter && hits.length < 5000) {
          hits.push(p); sum[0] += p.x; sum[1] += p.y; sum[2] += p.z;
        }
      }
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
    var qt = q.value.trim();
    countEl.textContent = !filter
      ? "Showing all " + pts.length.toLocaleString("en-CA") + " sections."
      : shown === 0
        ? "No section matches “" + qt + "”."
        : "Showing " + shown.toLocaleString("en-CA") + " of " +
          pts.length.toLocaleString("en-CA") + " sections matching “" + qt + "”.";
    showResults(hits, qt);
    /* a search is also a move: turn to where the word actually lives */
    if (filter && hits.length && !focus) {
      var m = Math.sqrt(sum[0] * sum[0] + sum[1] * sum[1] + sum[2] * sum[2]);
      if (m > 0.05) {
        var f = facing([sum[0] / m, sum[1] / m, sum[2] / m]);
        flyTo({ yaw: f.yaw, pitch: f.pitch }, 700);
      }
    }
    setHover(null);
    driftUntil = 0;
    syncLabels(true); syncRegions(true); invalidate();
  }
  function showResults(hits, qt) {
    if (!results) return;
    if (!filter) { results.hidden = true; results.innerHTML = ""; return; }
    results.innerHTML = "";
    if (!hits.length) {
      var e = document.createElement("p");
      e.className = "ares-empty";
      e.textContent = "Try a shorter word, or the name of a document. " +
        "The whole corpus is still on the sphere; clearing the box brings it back.";
      results.appendChild(e);
      results.hidden = false;
      return;
    }
    var byreg = [], seen = {};
    hits.forEach(function (p) {
      if (!seen[p.r.slug]) { seen[p.r.slug] = []; byreg.push(p.r); }
      seen[p.r.slug].push(p);
    });
    byreg.sort(function (a, b) { return seen[b.slug].length - seen[a.slug].length; });
    var shownN = 0;
    var ol = document.createElement("ol");
    ol.className = "ares-l";
    for (var i = 0; i < byreg.length && shownN < 14; i++) {
      var r = byreg[i], group = seen[r.slug];
      var head = document.createElement("li");
      head.className = "ares-g";
      head.textContent = r.title + " · " + group.length;
      ol.appendChild(head);
      for (var j = 0; j < group.length && shownN < 14; j++, shownN++) {
        var li = document.createElement("li");
        var a = document.createElement("a");
        a.href = group[j].href;
        a.textContent = group[j].t;
        (function (p) {
          a.addEventListener("focus", function () { setHover(p); });
          a.addEventListener("blur", function () { setHover(null); });
        })(group[j]);
        li.appendChild(a);
        ol.appendChild(li);
      }
    }
    results.appendChild(ol);
    if (hits.length > shownN) {
      var more = document.createElement("p");
      more.className = "ares-more";
      more.textContent = "and " + (hits.length - shownN).toLocaleString("en-CA") +
        " more, every one of them lit on the sphere. The full list has them all.";
      results.appendChild(more);
    }
    results.hidden = false;
  }
  if (q) {
    q.addEventListener("input", function () {
      clearTimeout(searchTimer);
      /* the count line is a live region; announcing every keystroke turns a
         status into a stutter */
      searchTimer = setTimeout(runSearch, 140);
    });
    q.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && q.value) {
        e.preventDefault(); q.value = ""; runSearch();
      }
    });
  }

  /* --------------------------------------------------------- modes ---- */
  var bGlobe = document.getElementById("aglobe");
  var bList = document.getElementById("alist");

  /* Clipped to a single pixel, the index kept all 1,247 links in the tab
     order, so a sighted keyboard user fell into thirteen hundred stops with no
     visible focus. It is a disclosure now: away while the sphere is showing,
     one labelled control back, and visible with real focus rings when open. */
  function setView(globe) {
    stage.hidden = !globe;
    /* Wide: the sphere is the view and the index is one control away.
       Narrow: they share the page, collapsed to fifty document rows. During
       the tour it waits: six labels and 1,247 links is a pile, not a
       sequence. */
    list.hidden = globe && (!narrow() || mode === "tour");
    list.classList.toggle("as-compact", globe && narrow());
    bGlobe.setAttribute("aria-pressed", String(globe));
    bList.setAttribute("aria-pressed", String(!globe));
    document.body.classList.toggle("atlas-listview", !globe);
    setCompact(globe && narrow());
    try { sessionStorage.setItem("atlas.view", globe ? "globe" : "list"); } catch (e) {}
    /* at boot this ran twice and solved the whole ladder each time; the frame
       loop does it once, after first paint */
    if (globe) { size(); project(); if (booted) { syncLabels(true); syncRegions(true); } kick(); }
  }
  bGlobe.addEventListener("click", function () { setView(true); });
  bList.addEventListener("click", function () { setView(false); });

  /* the whole corpus in one thumb's worth of scrolling, each document's
     sections one tap away */
  var compact = null, pendingCompact = null;
  function setCompact(on) {
    if (!enhanced) { pendingCompact = on; return; }
    if (compact === on) return;
    compact = on;
    [].forEach.call(list.querySelectorAll(".areg"), function (sec) {
      var ol = sec.querySelector(".areg-l");
      var btn = sec.querySelector(".areg-open");
      if (!ol) return;
      if (on) {
        if (!btn) {
          btn = document.createElement("button");
          btn.type = "button";
          btn.className = "areg-open";
          btn.setAttribute("aria-expanded", "false");
          btn.textContent = "Show sections";
          btn.addEventListener("click", function () {
            var open = btn.getAttribute("aria-expanded") === "true";
            btn.setAttribute("aria-expanded", String(!open));
            btn.textContent = open ? "Show sections" : "Hide sections";
            ol.hidden = open;
          });
          sec.appendChild(btn);
        }
        btn.hidden = false;
        ol.hidden = btn.getAttribute("aria-expanded") !== "true";
      } else {
        if (btn) btn.hidden = true;
        ol.hidden = false;
      }
    });
  }

  /* A document heading flies the camera to that document. A hundred buttons
     and a layout invalidation have nothing to do with first paint, so they
     wait until the main thread is free. */
  var enhanced = false;
  function enhanceIndex() {
    if (enhanced) return;
    enhanced = true;
    [].forEach.call(list.getElementsByClassName("areg"), function (sec) {
      var head = sec.querySelector(".areg-h");
      if (!head || !head.querySelector("a")) return;
      var b = document.createElement("button");
      b.type = "button";
      b.className = "areg-fly";
      b.textContent = "Show on the sphere";
      b.addEventListener("click", function () {
        var g = bySlug[sec.getAttribute("data-s")];
        if (!g) return;
        if (mode === "tour") toFree(true);
        setView(true);
        setFocus(g);
        stage.scrollIntoView({ block: "center",
          behavior: reduced ? "auto" : "smooth" });
      });
      head.appendChild(b);
    });
    if (pendingCompact !== null) { var c = pendingCompact; pendingCompact = null; setCompact(c); }
  }
  function whenIdle(fn) {
    if (window.requestIdleCallback) requestIdleCallback(fn, { timeout: 1800 });
    else setTimeout(fn, 240);
  }

  /* ------------------------------------------------------ keyboard ---- */
  document.addEventListener("keydown", function (e) {
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || e.metaKey || e.ctrlKey || e.altKey) return;
    if (mode === "tour") {
      if (e.key === "ArrowRight" || e.key === " ") {
        e.preventDefault();
        if (step === plates.length - 1) toFree(true); else setStep(step + 1, true);
      } else if (e.key === "ArrowLeft") {
        e.preventDefault(); if (step > 0) setStep(step - 1, true);
      } else if (e.key === "Escape") {
        e.preventDefault(); toFree(true);
      }
      return;
    }
    if (e.key === "Escape" && focus) { e.preventDefault(); setFocus(null); }
  });

  var rt;
  window.addEventListener("resize", function () {
    clearTimeout(rt);
    rt = setTimeout(function () {
      _font = null; _mc = {}; _mcn = 0;
      for (var i = 0; i < labels.length; i++) labels[i].w = 0;
      for (var j = 0; j < rlabels.length; j++) rlabels[j].w = 0;
      setView(bGlobe.getAttribute("aria-pressed") === "true");
      if (stage.hidden) return;
      size(); project(); syncLabels(true); syncRegions(true); invalidate();
    }, 120);
  });

  /* ------------------------------------------------------- survey ----
     Left alone in free view, the camera surveys the shelf: it flies from
     document to document on a nearest-neighbour path and holds each one for
     a time proportional to its section count, so the motion is the corpus
     reading itself out, not an idle spin. Any input, anywhere, hands the
     camera straight back and re-arms the clock. Off under reduced motion,
     off on phones, off while the stage is off screen. */
  var svy = { on: false, r: null, t1: 0, idle: 0, seq: [], i: 0 };
  function svyStop() {
    if (svy.t1) { clearTimeout(svy.t1); svy.t1 = 0; }
    if (svy.on) { svy.on = false; svy.r = null; tween = null; invalidate(); }
  }
  function svyCancel() { svyStop(); svyArm(); }
  function svyArm() {
    clearTimeout(svy.idle);
    if (reduced) return;
    svy.idle = setTimeout(svyMaybe, 12000);
  }
  function svyMaybe() {
    if (mode !== "free" || focus || narrow() || !visible || document.hidden) {
      svyArm(); return;
    }
    /* the lap: start with whatever is front and centre, then always the
       nearest territory not yet held */
    var fv = [-Math.sin(cam.yaw) * Math.cos(cam.pitch),
              Math.sin(cam.pitch),
              Math.cos(cam.yaw) * Math.cos(cam.pitch)];
    var left = regions.slice(), seq = [], cur = fv;
    while (left.length) {
      var bi = 0, bd = -2;
      for (var i2 = 0; i2 < left.length; i2++) {
        var g2 = left[i2];
        var d2 = g2.x * cur[0] + g2.y * cur[1] + g2.z * cur[2];
        if (d2 > bd) { bd = d2; bi = i2; }
      }
      var pick = left.splice(bi, 1)[0];
      seq.push(pick);
      cur = [pick.x, pick.y, pick.z];
    }
    svy.seq = seq; svy.i = 0; svy.on = true;
    svyStep();
  }
  function svyStep() {
    if (!svy.on) return;
    if (svy.i >= svy.seq.length) {
      /* one full lap, then rest; the clock re-arms and a still reader gets
         another lap after the same quiet interval */
      svyStop(); svyArm(); return;
    }
    var g = svy.seq[svy.i++];
    svy.r = g;
    var f = facing([g.x, g.y, g.z]);
    flyTo({ yaw: f.yaw, pitch: f.pitch, zoom: 1 }, 1500);
    /* dwell time is the one motion rate here, and it is data: milliseconds
       proportional to the document's section count, as the key says */
    svy.t1 = setTimeout(svyStep, 1500 + 1100 + g.n * 24);
    invalidate();
  }
  /* ------------------------------------------------- word-light ------
     Prose that names a document is live: pointing at the name lights the
     territory, and choosing it flies in. The words carry data-reg, written
     at build time from the same slugs the placement uses. */
  var wlR = null;
  function wlSet(r) {
    if (wlR === r) return;
    wlR = r;
    invalidate();
  }
  (function () {
    var host = document.getElementById("aplates");
    if (!host) return;
    function regOf(e) {
      var el = e.target && e.target.closest && e.target.closest(".lw");
      return el ? bySlug[el.getAttribute("data-reg")] || null : null;
    }
    host.addEventListener("mouseover", function (e) { var r = regOf(e); if (r) wlSet(r); });
    host.addEventListener("mouseout", function (e) { if (regOf(e)) wlSet(null); });
    host.addEventListener("focusin", function (e) { var r = regOf(e); if (r) wlSet(r); });
    host.addEventListener("focusout", function (e) { if (regOf(e)) wlSet(null); });
    function go(e) {
      var r = regOf(e);
      if (!r) return;
      e.preventDefault();
      wlSet(null);
      if (mode !== "free") toFree(true);
      setFocus(r);
    }
    host.addEventListener("click", go);
    host.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") go(e);
    });
  })();

  document.addEventListener("pointerdown", svyCancel, true);
  document.addEventListener("keydown", svyCancel, true);
  document.addEventListener("wheel", svyCancel, true);
  document.addEventListener("input", svyCancel, true);
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) svyStop(); else svyCancel();
  });
  svyArm();

  /* Boot. A returning reader is not made to sit through the labels again, and
     a deep link to one of them wins over both.

     Nothing reads geometry before the index is put away: measuring the stage
     first forced a full layout with 1,247 items still in flow. setView sizes
     the stage itself. */
  /* The sphere's first face is chosen against the data rather than
     inherited: the camera opens on the computed centre of the independent
     work. Both the tour's first stop and a returning reader's free view
     start from the strongest face. */
  if (FACTS.homeC) {
    var hc0 = facing(FACTS.homeC);
    cam.yaw = hc0.yaw; cam.pitch = hc0.pitch;
  }
  /* A reader who arrives from one of the documents finds that document
     front and centre: the sphere orients around where they just were. */
  var cameFrom = null;
  try {
    if (document.referrer) {
      var ru = new URL(document.referrer);
      if (ru.origin === location.origin) {
        var rb = ru.pathname.split("/").pop();
        for (var rf = 0; rf < regions.length; rf++) {
          if (regions[rf].url === rb) { cameFrom = regions[rf]; break; }
        }
      }
    }
  } catch (e) {}
  if (cameFrom) {
    var cf0 = facing([cameFrom.x, cameFrom.y, cameFrom.z]);
    cam.yaw = cf0.yaw; cam.pitch = cf0.pitch;
  }
  var seen = false, wanted = -1;
  try { seen = localStorage.getItem("atlas.seen") === "1"; } catch (e) {}
  var m0 = /^#label-(\d)$/.exec(location.hash || "");
  if (m0) wanted = +m0[1] - 1;

  var savedView = null;
  try { savedView = sessionStorage.getItem("atlas.view"); } catch (e) {}
  setView(savedView ? savedView === "globe" : true);

  if (wanted >= 0) { toTour(wanted); }
  else if (seen) {
    toFree(false);
    if (cameFrom) {
      hintEl.textContent = "You came from \u201c" + cameFrom.title +
        "\u201d: its territory is front and centre. Drag to turn the rest.";
    }
  }
  else { toTour(0); }
  booted = true;
  invalidate();
  /* One section a day, the same for every visit that day, drawn from the
     corpus itself: the owner asked that the page hand something back each
     time it is opened. Deterministic from the date, so a return visit the
     same day lands on the same passage. */
  (function () {
    var el = document.getElementById("atoday");
    if (!el || !pts.length) return;
    var day = Math.floor(Date.now() / 864e5);
    var p = pts[day % pts.length];
    var a = document.createElement("a");
    a.href = p.href;
    a.textContent = p.t;
    el.appendChild(document.createTextNode("Today\u2019s section: "));
    el.appendChild(a);
    el.appendChild(document.createTextNode(" \u00b7 " + p.r.title));
    el.hidden = false;
  })();
  whenIdle(enhanceIndex);
})();
