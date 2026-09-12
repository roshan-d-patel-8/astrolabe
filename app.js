(() => {
  "use strict";

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[char]));
  const ALTITUDES = [
    { n: 0, name: "Ground", short: "Presence", question: "Am I here?", detail: "Return beneath measurement and language." },
    { n: 1, name: "Compass", short: "Meaning", question: "Why does this matter?", detail: "Polaris: identity, values, mission, and vision." },
    { n: 2, name: "Cartography", short: "Domains", question: "What am I driving?", detail: "Ten living domains held in one relational map." },
    { n: 3, name: "Monocle", short: "Systems", question: "What is actually true?", detail: "The dashboard fleet and the condition of the instruments." },
    { n: 4, name: "Lens", short: "Measure", question: "What do the numbers say?", detail: "Drive, watch, and loop measures against an explicit glidepath." },
    { n: 5, name: "Momentum", short: "Action", question: "What exactly gets done?", detail: "The current TaskNotes board, rendered as an encrypted vault snapshot." },
    { n: 6, name: "Andon", short: "Capacity", question: "Am I flooded?", detail: "Capacity gates that can contract the entire system back to presence." },
  ];
  const SNAPSHOT = window.ASTRO_SNAPSHOT || { tasks: [], dashboards: [], taskCounts: {}, generatedAt: "" };
  const PILLARS = window.ASTRO_PILLARS || [];
  const METRICS = window.ASTRO_METRICS || [];
  const QUESTIONS = window.ASTRO_QUESTIONS || [];

  const state = {
    altitude: Number(localStorage.getItem("astrolabe-altitude") ?? 2),
    wing: localStorage.getItem("astrolabe-wing") || "both",
    taskQuery: "",
    fleetQuery: "",
    selected: null,
  };
  if (!Number.isInteger(state.altitude) || state.altitude < 0 || state.altitude > 6) state.altitude = 2;

  const stageLabel = { gate: "Gate", forge: "Forge", flow: "Flow" };
  const priorityRank = { high: 0, normal: 1, low: 2, none: 3 };
  const readableRealm = (realms) => (realms || []).map((r) => r.replace(/\[\[|\]\]/g, "")).join(" · ") || "Unclassified";
  const shortDate = (value) => {
    if (!value) return "";
    const match = String(value).match(/\d{4}-\d{2}-\d{2}/);
    return match ? match[0].slice(5) : String(value);
  };

  function renderRail() {
    $("#altitudes").innerHTML = ALTITUDES.map((a) => `
      <button class="altitude-btn ${a.n === state.altitude ? "active" : ""}" data-altitude="${a.n}" aria-label="F${a.n} ${a.name}" aria-current="${a.n === state.altitude ? "page" : "false"}">
        <span class="code">F${a.n}</span><span class="short">${esc(a.short)}</span>
      </button>`).join("");
    $$(".altitude-btn").forEach((button) => button.addEventListener("click", () => setAltitude(Number(button.dataset.altitude))));
  }

  function setAltitude(next) {
    state.altitude = Math.max(0, Math.min(6, next));
    localStorage.setItem("astrolabe-altitude", String(state.altitude));
    const meta = ALTITUDES[state.altitude];
    $$(".panel").forEach((panel) => panel.classList.toggle("active", Number(panel.dataset.panel) === state.altitude));
    $("#altitudeName").textContent = `F${meta.n} · ${meta.name}`;
    $("#altitudeQuestion").textContent = meta.question;
    $("#altitudeDetail").textContent = meta.detail;
    $("#crumbAltitude").textContent = `F${meta.n} ${meta.name}`;
    $("#prevAltitude").disabled = state.altitude === 0;
    $("#nextAltitude").disabled = state.altitude === 6;
    document.body.dataset.altitude = String(state.altitude);
    renderRail();
    window.dispatchEvent(new CustomEvent("astrolabe-altitude", { detail: state.altitude }));
    window.scrollTo({ top: 0, behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
  }

  function renderWing() {
    $$(".wing-btn").forEach((button) => button.classList.toggle("active", button.dataset.wing === state.wing));
    document.body.dataset.wing = state.wing;
    $$("[data-wing]").forEach((el) => {
      const matches = state.wing === "both" || el.dataset.wing === state.wing || el.dataset.wing === "both";
      el.hidden = !matches;
    });
  }

  function setWing(wing) {
    state.wing = wing;
    localStorage.setItem("astrolabe-wing", wing);
    renderWing();
    renderMetrics();
  }

  function lineage(pillar, leaf) {
    const p = typeof pillar === "string" ? PILLARS.find((item) => item.id === pillar) : pillar;
    if (!p) return;
    const wingName = p.w === "h" ? "Hathi" : "Skoll";
    $("#lineage").innerHTML = `
      <span>${leaf ? esc(leaf) : esc(p.name)}</span><i>←</i>
      <span>F4 ${esc(p.becoming)}</span><i>←</i>
      <span>F2 ${esc(p.name)}</span><i>←</i>
      <span>${wingName}</span><i>←</i>
      <span>F1 ${esc(p.dyad)}</span><i>←</i>
      <span>Polaris</span>`;
  }

  function pillarForTask(task) {
    const text = `${task.title} ${readableRealm(task.realms)} ${(task.tags || []).join(" ")}`.toLowerCase();
    const rules = [
      ["people", /recruit|interview|performance|feedback|chief|staff|candidate|culture/],
      ["access", /access|schedul|backlog|triag|appointment|eg[d|d]|colonoscopy|capacity/],
      ["quality", /quality|safety|ercp|remimazolam|sedation|guideline|clinical|patient|procedure/],
      ["experience", /experience|communication|email|slides|meeting|minutes|message|letter/],
      ["financial", /budget|utilization|compensation|timesheet|report|strategy|architecture|resource site|dashboard/],
    ];
    return PILLARS.find((p) => p.id === (rules.find(([, regex]) => regex.test(text)) || ["financial"])[0]);
  }

  function renderPillars() {
    const positions = [[17,25],[33,15],[70,18],[85,32],[84,67],[68,83],[34,85],[15,69],[28,50],[72,50]];
    $("#pillarNodes").innerHTML = PILLARS.map((p, index) => `
      <button class="pillar-node ${p.w}" data-pillar="${esc(p.id)}" data-wing="${p.w}" style="left:${positions[index][0]}%;top:${positions[index][1]}%">
        <b>${esc(p.name)}</b><small>${esc(p.realm)}</small>
      </button>`).join("");
    $("#pillarLedger").innerHTML = PILLARS.map((p) => `
      <button class="ledger-row ${p.w}" data-pillar="${esc(p.id)}" data-wing="${p.w}"><i></i><span>${esc(p.name)}</span><small>${esc(p.realm)}</small></button>`).join("");
    $$('[data-pillar]').forEach((button) => button.addEventListener("click", () => selectPillar(button.dataset.pillar)));
  }

  function selectPillar(id) {
    const p = PILLARS.find((item) => item.id === id);
    if (!p) return;
    $$('[data-pillar]').forEach((node) => node.classList.toggle("selected", node.dataset.pillar === id));
    lineage(p);
    openDrawer({
      eyebrow: `${p.w === "h" ? "Hathi" : "Skoll"} · ${p.realm}`,
      title: p.name,
      intro: p.roles,
      sections: [
        ["Being", p.being], ["Becoming", p.becoming], ["2026 + horizon", `<ul>${p.objs.map((o) => `<li>${esc(o)}</li>`).join("")}</ul>`],
        ["Guardianship", `<b>${esc(p.companion)}</b><br>${esc(p.agent)}<br><span class="muted">Value dyad · ${esc(p.dyad)}</span>`],
      ],
    });
  }

  function dashboardGroup(dashboard) {
    const haystack = `${dashboard.title} ${(dashboard.tags || []).join(" ")}`.toLowerCase();
    if (/dsagi|meeting|first contact|long hall|sheikah/.test(haystack)) return "DSA GI";
    if (/task|performance|kiroshi|health|dojo|forge/.test(haystack)) return "Execution";
    if (/kalpa|memory|garden|penelope|chronos|time/.test(haystack)) return "Time & memory";
    if (/totem|moc|philosophy|lattice|orrery|meru|holodeck|faces|middle way/.test(haystack)) return "Knowledge";
    return "Identity";
  }

  function renderFleet() {
    const query = state.fleetQuery.trim().toLowerCase();
    const records = SNAPSHOT.dashboards.filter((d) => `${d.title} ${d.description} ${(d.tags || []).join(" ")}`.toLowerCase().includes(query));
    $("#fleetCount").textContent = `${records.length} of ${SNAPSHOT.dashboards.length} instruments`;
    $("#fleetGrid").innerHTML = records.map((d) => `
      <a class="fleet-item" href="${esc(d.uri)}" data-dashboard="${esc(d.title)}">
        <span class="eyebrow">${esc(dashboardGroup(d))}</span>
        <b>${esc(d.title)}</b>
        <p>${esc(d.description)}</p>
        <small>refreshed ${esc(d.refreshed || "unknown")} · open in Obsidian ↗</small>
      </a>`).join("") || '<div class="empty-state">No instrument answers that search.</div>';
  }

  function renderMetrics() {
    const rows = METRICS.filter((r) => state.wing === "both" || r.w === state.wing);
    const tallies = ["good", "warn", "critical", "none"].map((status) => rows.filter((row) => row.status === status).length);
    $("#metricTallies").innerHTML = [
      [tallies[0], "on course"], [tallies[1], "watch closely"], [tallies[2], "off course"], [tallies[3], "instrument blind"],
    ].map(([value, label]) => `<div class="metric-tally"><b>${value}</b><span>${label}</span></div>`).join("");
    $("#metricRows").innerHTML = rows.map((r) => `
      <tr data-wing="${r.w}">
        <td><span class="status-dot ${r.status}"></span><span class="metric-pillar">${esc(r.pillar)}</span></td>
        <td>${esc(r.metric)}</td><td class="mono">${esc(r.current)}</td><td>${esc(r.target)}</td>
        <td><span class="class-chip">${esc(r.class)}</span></td><td>${esc(r.owner)}</td>
      </tr>`).join("");
  }

  function taskMatches(task) {
    const query = state.taskQuery.trim().toLowerCase();
    if (!query) return true;
    return `${task.title} ${task.status} ${task.priority} ${readableRealm(task.realms)} ${(task.tags || []).join(" ")}`.toLowerCase().includes(query);
  }

  function renderBoard() {
    const tasks = SNAPSHOT.tasks.filter(taskMatches).sort((a, b) => (priorityRank[a.priority] ?? 3) - (priorityRank[b.priority] ?? 3));
    ["gate", "forge", "flow"].forEach((stage) => {
      const stageTasks = tasks.filter((task) => task.status === stage);
      $(`#count-${stage}`).textContent = String(stageTasks.length);
      $(`#tasks-${stage}`).innerHTML = stageTasks.slice(0, 80).map((task) => `
        <button class="task-card ${esc(task.priority)}" data-task="${esc(task.id)}">
          <span class="task-title">${esc(task.title)}</span>
          <span class="task-meta">
            <span class="task-chip">${esc(task.type || "task")}</span>
            ${task.scheduled ? `<span class="date">scheduled ${esc(shortDate(task.scheduled))}</span>` : ""}
            ${task.due ? `<span class="date">due ${esc(shortDate(task.due))}</span>` : ""}
            <span>${esc(task.priority || "normal")}</span>
          </span>
        </button>`).join("") || '<div class="empty-state">Clear.</div>';
    });
    $("#boardResultCount").textContent = `${tasks.length} active billets`;
    $$('[data-task]').forEach((button) => button.addEventListener("click", () => selectTask(button.dataset.task)));
  }

  function selectTask(id) {
    const task = SNAPSHOT.tasks.find((item) => item.id === id);
    if (!task) return;
    const pillar = pillarForTask(task);
    lineage(pillar, task.title);
    openDrawer({
      eyebrow: `${stageLabel[task.status] || task.status} · ${task.priority} priority`,
      title: task.title,
      intro: task.excerpt || "The canonical note carries the full context.",
      sections: [
        ["Board coordinates", `${esc(readableRealm(task.realms))}<br>${task.scheduled ? `Scheduled ${esc(shortDate(task.scheduled))}` : "Unscheduled"}${task.due ? ` · Due ${esc(shortDate(task.due))}` : ""}`],
        ["Axis lineage", `${esc(pillar?.name || "Unmapped")} · ${esc(pillar?.dyad || "No dyad assigned")}`],
        ["Sync contract", "This page is an encrypted read model. Change status, dates, and context in the TaskNotes note; the next Astrolabe build will ingest it."],
      ],
      uri: task.uri,
    });
  }

  function openDrawer(content) {
    state.selected = content;
    $("#drawerEyebrow").textContent = content.eyebrow || "Astrolabe reading";
    $("#drawerTitle").textContent = content.title || "Selection";
    $("#drawerIntro").textContent = content.intro || "";
    $("#drawerBody").innerHTML = (content.sections || []).map(([title, body]) => `<section class="drawer-section"><h3>${esc(title)}</h3><div>${body}</div></section>`).join("");
    $("#drawerOpen").hidden = !content.uri;
    if (content.uri) $("#drawerOpen").href = content.uri;
    $("#drawer").classList.add("open");
    $("#drawerBackdrop").classList.add("show");
    $("#drawer").setAttribute("aria-hidden", "false");
  }

  function closeDrawer() {
    $("#drawer").classList.remove("open");
    $("#drawerBackdrop").classList.remove("show");
    $("#drawer").setAttribute("aria-hidden", "true");
  }

  function renderPalette(query = "") {
    const q = query.trim().toLowerCase();
    const items = [
      ...PILLARS.map((p) => ({ kind: "domain", title: p.name, detail: `${p.realm} · ${p.dyad}`, action: () => { setAltitude(2); selectPillar(p.id); } })),
      ...SNAPSHOT.dashboards.map((d) => ({ kind: "dashboard", title: d.title, detail: dashboardGroup(d), action: () => { location.href = d.uri; } })),
      ...SNAPSHOT.tasks.map((t) => ({ kind: "task", title: t.title, detail: `${stageLabel[t.status]} · ${t.priority}`, action: () => { setAltitude(5); selectTask(t.id); } })),
      ...ALTITUDES.map((a) => ({ kind: "altitude", title: `F${a.n} ${a.name}`, detail: a.question, action: () => setAltitude(a.n) })),
    ].filter((item) => !q || `${item.title} ${item.detail} ${item.kind}`.toLowerCase().includes(q)).slice(0, 40);
    $("#paletteResults").innerHTML = items.map((item, index) => `
      <button class="palette-result" data-result="${index}"><span class="kind">${esc(item.kind)}</span><b>${esc(item.title)}</b><small>${esc(item.detail)}</small></button>`).join("") || '<div class="empty-state">Nothing in this sky answers that name.</div>';
    $$('[data-result]').forEach((button) => button.addEventListener("click", () => { items[Number(button.dataset.result)].action(); closePalette(); }));
  }

  function openPalette() {
    $("#palette").classList.add("open");
    $("#paletteInput").value = "";
    renderPalette();
    setTimeout(() => $("#paletteInput").focus(), 0);
  }
  function closePalette() { $("#palette").classList.remove("open"); }

  function renderQuestions() {
    $("#questionGrid").innerHTML = QUESTIONS.map((q, index) => `
      <article class="question"><b>${index + 1}. ${esc(q.t)}</b><p>${esc(q.c)}</p><textarea data-q="${esc(q.id)}" aria-label="Answer to ${esc(q.t)}"></textarea><div class="q-actions"><button class="save" data-q="${esc(q.id)}" disabled>Save</button><span class="saved" data-q="${esc(q.id)}"></span></div></article>`).join("");
    window.ASTRO_QUESTIONS = QUESTIONS;
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("astrolabe-theme", theme);
    $("#themeToggle").textContent = theme === "dark" ? "☀" : "◐";
    $("#themeToggle").setAttribute("aria-label", theme === "dark" ? "Use light mode" : "Use dark mode");
    window.dispatchEvent(new Event("astrolabe-theme"));
  }

  function initThree() {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.min.js";
    script.onload = () => {
      const THREE = window.THREE;
      const canvas = $("#starfield");
      if (!THREE || !canvas) return;
      const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: "low-power" });
      renderer.setPixelRatio(Math.min(devicePixelRatio, 1.7));
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(46, innerWidth / innerHeight, .1, 100);
      camera.position.set(0, 0, 11);
      const group = new THREE.Group(); scene.add(group);

      const parseColor = (name) => new THREE.Color(getComputedStyle(document.documentElement).getPropertyValue(name).trim());
      const uniforms = { uTime: { value: 0 }, uBrass: { value: parseColor("--brass") }, uInk: { value: parseColor("--ink") } };
      const shader = new THREE.ShaderMaterial({
        transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, uniforms,
        vertexShader: "varying vec2 vUv; void main(){vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}",
        fragmentShader: `varying vec2 vUv; uniform float uTime; uniform vec3 uBrass; uniform vec3 uInk;
          float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
          float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
          void main(){vec2 p=vUv*4.;float fog=n(p+vec2(uTime*.025,-uTime*.018))*n(p*1.8-uTime*.012);float vign=1.-smoothstep(.18,.9,distance(vUv,vec2(.72,.43)));float a=fog*vign*.075;gl_FragColor=vec4(mix(uInk,uBrass,.72),a);}`,
      });
      const plane = new THREE.Mesh(new THREE.PlaneGeometry(25, 15), shader); plane.position.z = -5; scene.add(plane);

      const ringMaterial = new THREE.LineBasicMaterial({ color: uniforms.uBrass.value, transparent: true, opacity: .19 });
      [1.45, 2.4, 3.5, 4.7].forEach((radius, index) => {
        const points = Array.from({ length: 129 }, (_, i) => new THREE.Vector3(Math.cos(i / 128 * Math.PI * 2) * radius, Math.sin(i / 128 * Math.PI * 2) * radius * (.58 + index * .05), 0));
        const ring = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(points), ringMaterial.clone());
        ring.rotation.set(index * .22, index * .14, index * .25); group.add(ring);
      });
      const relic = new THREE.Mesh(new THREE.IcosahedronGeometry(.72, 1), new THREE.MeshBasicMaterial({ color: uniforms.uBrass.value, wireframe: true, transparent: true, opacity: .22 }));
      group.add(relic);

      const count = 520;
      const positions = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        const radius = 2.4 + Math.random() * 6.8;
        const angle = Math.random() * Math.PI * 2;
        positions[i * 3] = Math.cos(angle) * radius;
        positions[i * 3 + 1] = Math.sin(angle) * radius * .62;
        positions[i * 3 + 2] = (Math.random() - .5) * 4;
      }
      const starGeo = new THREE.BufferGeometry(); starGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      const stars = new THREE.Points(starGeo, new THREE.PointsMaterial({ color: uniforms.uBrass.value, size: .025, transparent: true, opacity: .48 })); group.add(stars);

      let targetZ = 11 - state.altitude * .32;
      let px = 0, py = 0;
      addEventListener("pointermove", (event) => { px = (event.clientX / innerWidth - .5) * .22; py = (event.clientY / innerHeight - .5) * .16; }, { passive: true });
      addEventListener("astrolabe-altitude", (event) => { targetZ = 11 - Number(event.detail) * .32; });
      addEventListener("astrolabe-theme", () => { uniforms.uBrass.value.set(parseColor("--brass")); uniforms.uInk.value.set(parseColor("--ink")); group.traverse((obj) => { if (obj.material?.color) obj.material.color.set(uniforms.uBrass.value); }); });
      function resize() { renderer.setSize(innerWidth, innerHeight, false); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); }
      addEventListener("resize", resize, { passive: true }); resize();
      const clock = new THREE.Clock();
      function frame() {
        const t = clock.getElapsedTime(); uniforms.uTime.value = t;
        camera.position.z += (targetZ - camera.position.z) * .035;
        group.rotation.z = t * .008 + px; group.rotation.x += (py - group.rotation.x) * .018;
        relic.rotation.x = t * .09; relic.rotation.y = t * .11;
        renderer.render(scene, camera); requestAnimationFrame(frame);
      }
      frame();
    };
    script.onerror = () => document.body.classList.add("three-fallback");
    document.head.appendChild(script);
  }

  function bind() {
    $("#prevAltitude").addEventListener("click", () => setAltitude(state.altitude - 1));
    $("#nextAltitude").addEventListener("click", () => setAltitude(state.altitude + 1));
    $$(".wing-btn").forEach((button) => button.addEventListener("click", () => setWing(button.dataset.wing)));
    $("#themeToggle").addEventListener("click", () => applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark"));
    $("#searchButton").addEventListener("click", openPalette);
    $("#palette").addEventListener("click", (event) => { if (event.target === $("#palette")) closePalette(); });
    $("#paletteInput").addEventListener("input", (event) => renderPalette(event.target.value));
    $("#drawerClose").addEventListener("click", closeDrawer);
    $("#drawerBackdrop").addEventListener("click", closeDrawer);
    $("#fleetFilter").addEventListener("input", (event) => { state.fleetQuery = event.target.value; renderFleet(); });
    $("#taskFilter").addEventListener("input", (event) => { state.taskQuery = event.target.value; renderBoard(); });
    $("#observatoryButton").addEventListener("click", () => $("#observatory").classList.add("open"));
    $("#observatoryClose").addEventListener("click", () => $("#observatory").classList.remove("open"));
    addEventListener("keydown", (event) => {
      const typing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName);
      if (event.key === "Escape") { closeDrawer(); closePalette(); $("#observatory").classList.remove("open"); }
      if (!typing && event.key === "/") { event.preventDefault(); openPalette(); }
      if (!typing && /^[0-6]$/.test(event.key)) setAltitude(Number(event.key));
      if (!typing && event.key === "[") setAltitude(state.altitude - 1);
      if (!typing && event.key === "]") setAltitude(state.altitude + 1);
    });
  }

  function init() {
    const preferred = localStorage.getItem("astrolabe-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    applyTheme(preferred);
    $("#snapshotTime").textContent = SNAPSHOT.generatedAt ? new Date(SNAPSHOT.generatedAt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "snapshot unavailable";
    $("#liveTaskCount").textContent = String(SNAPSHOT.tasks.length);
    $("#dashboardCount").textContent = String(SNAPSHOT.dashboards.length);
    $("#conditionGate").textContent = String(SNAPSHOT.taskCounts?.gate ?? 0);
    $("#conditionForge").textContent = String(SNAPSHOT.taskCounts?.forge ?? 0);
    $("#conditionFlow").textContent = String(SNAPSHOT.taskCounts?.flow ?? 0);
    $("#andonGate").textContent = String(SNAPSHOT.taskCounts?.gate ?? 0);
    $("#andonSnapshot").textContent = SNAPSHOT.generatedAt ? `Generated ${new Date(SNAPSHOT.generatedAt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}.` : "Snapshot unavailable.";
    $("#sourceStamp").textContent = SNAPSHOT.source || "Vault snapshot";
    renderPillars(); renderFleet(); renderMetrics(); renderBoard(); renderQuestions(); bind(); renderWing(); setAltitude(state.altitude); initThree();
    setTimeout(() => window.dispatchEvent(new Event("astrolabe-ready")), 0);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true }); else init();
})();
