/* Harigovind R — portfolio
   No framework, no build step. Four small things: the live gyroid, the sticky
   nav + scroll spy, reveal-on-scroll, and falling petals. */
(() => {
  "use strict";

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ───────────────────────────────────────────────── gyroid
     The scaffold surface is sin x·cos y + sin y·cos z + sin z·cos x = 0.
     Drawing the |f| < t band gives the strut cross-section.

     Naively that is six trig calls per pixel per frame. But x depends only on
     the column and y only on the row, so the sines and cosines are precomputed
     into lookup tables once, and z is constant across a frame -- which leaves
     two multiplies and two adds per pixel. That is what makes it cheap enough
     to animate. */
  const canvas = document.getElementById("gyroid");
  if (canvas && canvas.getContext) {
    const ctx = canvas.getContext("2d", { alpha: true });
    const N = canvas.width;                 // square
    const SPAN = 8.6 * Math.PI;             // periods across the panel
    const T = 0.36;                         // strut half-thickness
    const EDGE = 0.20;                      // lit rim falloff

    // The slice degenerates into plain stripes outside z ~ 0.60-0.95 -- at the
    // ends of that range one of sin z / cos z vanishes and the surface collapses
    // to parallel waves. So z oscillates strictly inside the band, and the
    // motion comes mostly from drifting the sampling phase instead.
    const Z_MID = 0.78, Z_AMP = 0.18;

    const sx = new Float32Array(N), cx = new Float32Array(N);
    const img = ctx.createImageData(N, N);
    const buf = img.data;
    const t3 = new Float32Array(N);

    function frame(z, phase) {
      for (let i = 0; i < N; i++) {          // 2N trig calls, vs 6 per pixel
        const a = (i / (N - 1)) * SPAN + phase;
        sx[i] = Math.sin(a); cx[i] = Math.cos(a);
      }
      const sinz = Math.sin(z), cosz = Math.cos(z);
      for (let i = 0; i < N; i++) t3[i] = sinz * cx[i];

      let p = 0;
      for (let j = 0; j < N; j++) {
        const cyj = cx[j], aj = sx[j] * cosz;
        for (let i = 0; i < N; i++) {
          const f = sx[i] * cyj + aj + t3[i];
          const d = f < 0 ? -f : f;
          if (d < T) {                       // solid strut
            buf[p] = 26; buf[p + 1] = 16; buf[p + 2] = 44; buf[p + 3] = 242;
          } else if (d < T + EDGE) {         // lit rim
            const k = 1 - (d - T) / EDGE;
            buf[p] = 152; buf[p + 1] = 234; buf[p + 2] = 238;
            buf[p + 3] = (k * k * 210) | 0;
          } else {
            buf[p + 3] = 0;
          }
          p += 4;
        }
      }
      ctx.putImageData(img, 0, 0);
    }

    if (reduced) {
      frame(Z_MID, 0);
    } else {
      let visible = true, last = 0, raf = 0;
      const FPS = 30, STEP = 1000 / FPS;

      const loop = (now) => {
        raf = requestAnimationFrame(loop);
        if (!visible || now - last < STEP) return;
        last = now;
        frame(Z_MID + Z_AMP * Math.sin(now / 7000), now / 9000);
      };

      // stop drawing when the hero scrolls away or the tab is hidden
      const hero = document.querySelector(".hero");
      if (hero && "IntersectionObserver" in window) {
        new IntersectionObserver(
          ([e]) => { visible = e.isIntersecting; },
          { threshold: 0 }
        ).observe(hero);
      }
      document.addEventListener("visibilitychange", () => {
        if (document.hidden) { cancelAnimationFrame(raf); raf = 0; }
        else if (!raf) { last = 0; raf = requestAnimationFrame(loop); }
      });

      raf = requestAnimationFrame(loop);
    }
  }

  /* ───────────────────────────────────────────── nav + spy */
  const nav = document.getElementById("nav");
  const onScroll = () => nav && nav.classList.toggle("is-stuck", window.scrollY > 24);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  const links = [...document.querySelectorAll(".nav__list a")];
  const byId = new Map(links.map((a) => [a.getAttribute("href").slice(1), a]));
  const sections = [...byId.keys()]
    .map((id) => document.getElementById(id))
    .filter(Boolean);

  if (sections.length && "IntersectionObserver" in window) {
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        links.forEach((a) => a.classList.remove("is-active"));
        const a = byId.get(e.target.id);
        if (a) a.classList.add("is-active");
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    sections.forEach((s) => spy.observe(s));
  }

  /* ────────────────────────────────────────────────── reveal */
  const revealables = [...document.querySelectorAll(".reveal")];
  if (!("IntersectionObserver" in window) || reduced) {
    revealables.forEach((el) => el.classList.add("is-in"));
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        e.target.classList.add("is-in");
        io.unobserve(e.target);
      });
    }, { rootMargin: "0px 0px -12% 0px", threshold: 0.06 });
    revealables.forEach((el) => io.observe(el));
  }


  /* ──────────────────────────────────────── skill constellation
     Layout is precomputed by assets/build_constellation.py and inlined as JSON,
     so the live graph and the animated SVG in the GitHub README are guaranteed
     to be the same picture. Here we only draw it and wire up the highlighting. */
  const host = document.getElementById("constel-svg");
  const dataEl = document.getElementById("graph-data");
  if (host && dataEl) {
    const NS = "http://www.w3.org/2000/svg";
    const g = JSON.parse(dataEl.textContent);
    const byId = new Map(g.nodes.map((n) => [n.id, n]));
    const el = (t, a) => {
      const e = document.createElementNS(NS, t);
      for (const k in a) e.setAttribute(k, a[k]);
      return e;
    };

    // adjacency, used for both the highlight and the text fallback
    const near = new Map(g.nodes.map((n) => [n.id, []]));
    g.edges.forEach((e) => { near.get(e.p).push(e.s); near.get(e.s).push(e.p); });

    const defs = el("defs");
    defs.innerHTML =
      '<filter id="cglow" x="-70%" y="-70%" width="240%" height="240%">' +
      '<feGaussianBlur stdDeviation="4" result="b"/><feMerge>' +
      '<feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>';
    host.appendChild(defs);

    const gEdges = el("g", { class: "constel__edges" });
    const gNodes = el("g", { class: "constel__nodes" });
    host.append(gEdges, gNodes);

    const edgeEls = g.edges.map((e) => {
      const path = el("path", { d: e.d, class: "edge", "data-p": e.p, "data-s": e.s });
      gEdges.appendChild(path);
      return path;
    });

    const nodeEls = new Map();
    g.nodes.forEach((n) => {
      const isP = n.type === "project";
      const grp = el("g", {
        class: "node node--" + n.type,
        "data-id": n.id,
        tabindex: "0",
        role: "button",
        "aria-label": `${n.label}: ${near.get(n.id).length} connection${
          near.get(n.id).length === 1 ? "" : "s"}`,
      });
      if (isP) {
        const r = 11;
        grp.appendChild(el("path", {
          class: "mark",
          d: `M${n.x},${n.y - r} L${n.x + r},${n.y} L${n.x},${n.y + r} L${n.x - r},${n.y} Z`,
        }));
      } else {
        grp.appendChild(el("circle", { class: "mark", cx: n.x, cy: n.y, r: n.r }));
      }

      // label placement mirrors the generator: outward, or clear of the node
      const ang = Math.atan2(n.y - g.h / 2 - 6, n.x - g.w / 2);
      const ca = Math.cos(ang);
      let anchor = "middle", dx = 0, dy = Math.sin(ang) < 0 ? -(n.r + 10) : n.r + 19;
      if (Math.abs(ca) >= 0.3) {
        anchor = ca > 0 ? "start" : "end";
        dx = ca > 0 ? n.r + 9 : -(n.r + 9);
        dy = 4;
      }
      const t = el("text", {
        class: "label", x: n.x + dx, y: n.y + dy, "text-anchor": anchor,
      });
      t.textContent = n.label;
      grp.appendChild(t);
      gNodes.appendChild(grp);
      nodeEls.set(n.id, grp);
    });

    const hint = document.getElementById("constel-hint");
    const hintHTML = hint ? hint.innerHTML : "";
    let active = null;

    function show(id) {
      active = id;
      host.classList.add("is-focus");
      const lit = new Set([id, ...near.get(id)]);
      nodeEls.forEach((n, k) => n.classList.toggle("is-lit", lit.has(k)));
      edgeEls.forEach((e, i) => {
        const ed = g.edges[i];
        e.classList.toggle("is-lit", ed.p === id || ed.s === id);
      });
      if (hint) {
        const n = byId.get(id);
        const others = near.get(id).map((k) => byId.get(k).label);
        hint.innerHTML =
          `<b>${n.label}</b> — ${n.type === "skill" ? "used in" : "built with"} ` +
          others.map((o) => `<i>${o}</i>`).join(", ");
      }
    }

    function clear() {
      active = null;
      host.classList.remove("is-focus");
      nodeEls.forEach((n) => n.classList.remove("is-lit"));
      edgeEls.forEach((e) => e.classList.remove("is-lit"));
      if (hint) hint.innerHTML = hintHTML;
    }

    nodeEls.forEach((grp, id) => {
      grp.addEventListener("mouseenter", () => show(id));
      grp.addEventListener("focus", () => show(id));
      grp.addEventListener("blur", clear);
      grp.addEventListener("keydown", (ev) => {
        if (ev.key === "Escape") { clear(); grp.blur(); }
      });
      // touch: tap to pin, tap again to release
      grp.addEventListener("click", (ev) => {
        ev.stopPropagation();
        active === id ? clear() : show(id);
      });
    });
    host.addEventListener("mouseleave", () => { if (!active) clear(); });
    document.addEventListener("click", (ev) => {
      if (active && !host.contains(ev.target)) clear();
    });

    // text fallback, for narrow screens and screen readers
    const list = document.getElementById("constel-list");
    if (list) {
      g.nodes.filter((n) => n.type === "skill").forEach((n) => {
        const li = document.createElement("li");
        li.innerHTML = `<b>${n.label}</b> — ` +
          near.get(n.id).map((k) => byId.get(k).label).join(", ");
        list.appendChild(li);
      });
    }
  }

  /* ────────────────────────────────────────────────── petals */
  const petals = document.getElementById("petals");
  if (petals && !reduced) {
    const frag = document.createDocumentFragment();
    for (let i = 0; i < 16; i++) {
      const el = document.createElement("i");
      el.className = "petal";
      const s = 0.65 + Math.random() * 0.9;
      el.style.left = (Math.random() * 100).toFixed(2) + "%";
      el.style.transform = `scale(${s.toFixed(2)})`;
      el.style.opacity = (0.45 + Math.random() * 0.5).toFixed(2);
      el.style.animationDuration = (9 + Math.random() * 11).toFixed(1) + "s";
      el.style.animationDelay = (-Math.random() * 18).toFixed(1) + "s";
      frag.appendChild(el);
    }
    petals.appendChild(frag);
  }
})();
