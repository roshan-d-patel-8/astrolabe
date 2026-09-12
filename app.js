(() => {
  "use strict";

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [
    ...root.querySelectorAll(selector),
  ];
  const esc = (value) =>
    String(value ?? "").replace(
      /[&<>"']/g,
      (char) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#039;",
        })[char],
    );
  const ALTITUDES = [
    {
      n: 1,
      name: "Compass",
      short: "Why",
      question: "Why?",
      detail: "Polaris · purpose · values",
    },
    {
      n: 2,
      name: "Cartography",
      short: "Where",
      question: "Where?",
      detail: "Ten domains · one field of view",
    },
    {
      n: 3,
      name: "The Real",
      short: "What",
      question: "What is true?",
      detail: "Instrument currency · system condition",
    },
    {
      n: 4,
      name: "Lens",
      short: "Measure",
      question: "How are we doing?",
      detail: "Current · target · ownership",
    },
    {
      n: 5,
      name: "Momentum",
      short: "Now",
      question: "What moves now?",
      detail: "Gate → Forge → Flow",
    },
  ];
  const SNAPSHOT = window.ASTRO_SNAPSHOT || {
    tasks: [],
    dashboards: [],
    taskCounts: {},
    generatedAt: "",
  };
  const PILLARS = window.ASTRO_PILLARS || [];
  const METRICS = window.ASTRO_METRICS || [];
  const QUESTIONS = window.ASTRO_QUESTIONS || [];
  const icon = (paths) =>
    `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
  const storage = {
    get(key) {
      try {
        return localStorage.getItem(key);
      } catch {
        return null;
      }
    },
    set(key, value) {
      try {
        localStorage.setItem(key, value);
      } catch {}
    },
  };
  const statusLabel = {
    good: "On course",
    warn: "Watch",
    critical: "Off course",
    none: "No reading",
  };

  const state = {
    altitude: Number(storage.get("astrolabe-altitude") ?? 2),
    wing: storage.get("astrolabe-wing") || "both",
    domain: null,
    stage: null,
    priority: null,
    taskQuery: "",
    fleetQuery: "",
    selected: null,
  };
  if (
    !Number.isInteger(state.altitude) ||
    state.altitude < 1 ||
    state.altitude > 5
  )
    state.altitude = 2;
  if (!["both", "h", "s"].includes(state.wing)) state.wing = "both";

  const stageLabel = { gate: "Gate", forge: "Forge", flow: "Flow" };
  const priorityRank = { high: 0, normal: 1, low: 2, none: 3 };
  const readableRealm = (realms) =>
    (realms || []).map((r) => r.replace(/\[\[|\]\]/g, "")).join(" · ") ||
    "Unclassified";
  const shortDate = (value) => {
    if (!value) return "";
    const match = String(value).match(/\d{4}-\d{2}-\d{2}/);
    return match ? match[0].slice(5) : String(value);
  };

  function renderRail() {
    const hadFocus = document.activeElement?.matches(".altitude-btn");
    $("#altitudes").innerHTML = ALTITUDES.map(
      (a) => `
      <button class="altitude-btn ${a.n === state.altitude ? "active" : ""}" data-altitude="${a.n}" aria-label="F${a.n} ${a.name}" aria-current="${a.n === state.altitude ? "page" : "false"}">
        <span class="code">F${a.n}</span><span class="short">${esc(a.name)}</span><small>${esc(a.short)}</small>
      </button>`,
    ).join("");
    $$(".altitude-btn").forEach((button) =>
      button.addEventListener("click", () =>
        setAltitude(Number(button.dataset.altitude)),
      ),
    );
    if (hadFocus)
      $(`.altitude-btn[data-altitude="${state.altitude}"]`)?.focus({
        preventScroll: true,
      });
  }

  function setAltitude(next) {
    state.altitude = Math.max(1, Math.min(5, next));
    storage.set("astrolabe-altitude", String(state.altitude));
    const meta = ALTITUDES.find((item) => item.n === state.altitude);
    $$(".panel").forEach((panel) =>
      panel.classList.toggle(
        "active",
        Number(panel.dataset.panel) === state.altitude,
      ),
    );
    $("#altitudeName").textContent = `F${meta.n} · ${meta.name}`;
    $("#altitudeQuestion").textContent = meta.name;
    $("#altitudeDetail").textContent = `${meta.question} ${meta.detail}`;
    $("#crumbAltitude").textContent = `F${meta.n} ${meta.name}`;
    $("#prevAltitude").disabled = state.altitude === 1;
    $("#nextAltitude").disabled = state.altitude === 5;
    $(".wing-switch").hidden = ![2, 4, 5].includes(state.altitude);
    document.body.dataset.altitude = String(state.altitude);
    renderRail();
    renderScope();
    updateScrollHints();
    window.dispatchEvent(
      new CustomEvent("astrolabe-altitude", { detail: state.altitude }),
    );
    window.scrollTo({
      top: 0,
      behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth",
    });
  }

  function renderWing() {
    $$(".wing-btn").forEach((button) => {
      button.classList.toggle("active", button.dataset.wing === state.wing);
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.wing === state.wing),
      );
    });
    document.body.dataset.wing = state.wing;
    $$(".domain-wing[data-wing]").forEach((el) => {
      const matches =
        state.wing === "both" ||
        el.dataset.wing === state.wing ||
        el.dataset.wing === "both";
      el.hidden = !matches;
    });
    $("#domainMatrix").style.gridTemplateColumns =
      state.wing === "both" ? "" : "1fr";
  }

  function setWing(wing) {
    state.wing = wing;
    state.domain = null;
    resetTrace();
    storage.set("astrolabe-wing", wing);
    renderWing();
    renderMetrics();
    renderBoard();
    renderScope();
  }

  function renderScope() {
    const domain = PILLARS.find((p) => p.id === state.domain);
    const filters = [
      domain?.name,
      state.stage && stageLabel[state.stage],
      state.priority && `${state.priority} priority`,
    ].filter(Boolean);
    const special =
      state.altitude === 5 && state.wing === "h"
        ? "Hathi tasks are managed outside this Skoll snapshot."
        : "";
    const notice = $("#scopeNotice");
    notice.hidden = !filters.length && !special;
    $("#scopeLabel").textContent =
      special ||
      `Focused on ${filters.join(" · ")}. Domain follows you into Lens and Momentum.`;
  }

  function focusDomain(id, altitude) {
    state.domain = id;
    const p = PILLARS.find((item) => item.id === id);
    if (p) state.wing = p.w;
    closeDrawer();
    renderWing();
    renderMetrics();
    renderBoard();
    setAltitude(altitude);
  }

  function lineage(pillar, leaf) {
    const p =
      typeof pillar === "string"
        ? PILLARS.find((item) => item.id === pillar)
        : pillar;
    if (!p) {
      resetTrace();
      return;
    }
    const wingName = p.w === "h" ? "Hathi" : "Skoll";
    $("#lineage").innerHTML = `
      <span>${leaf ? esc(leaf) : esc(p.name)}</span><i>←</i>
      <span>F4 measures</span><i>←</i>
      <span>F2 ${esc(p.name)}</span><i>←</i>
      <span>${wingName}</span><i>←</i>
      <span>F1 ${esc(p.dyad)}</span><i>←</i>
      <span>Polaris</span>`;
  }

  function resetTrace() {
    $$(".domain-row.selected").forEach((el) => el.classList.remove("selected"));
    $("#lineage").innerHTML =
      "<span>F5 action</span><i>←</i><span>F4 measure</span><i>←</i><span>F3 evidence</span><i>←</i><span>F2 domain</span><i>←</i><span>F1 value</span><i>←</i><span>Polaris</span>";
  }

  function pillarForTask(task) {
    const text =
      `${task.title} ${readableRealm(task.realms)} ${(task.tags || []).join(" ")}`.toLowerCase();
    const rules = [
      [
        "people",
        /recruit|interview|performance|feedback|chief|staff|candidate|culture/,
      ],
      [
        "access",
        /access|schedul|backlog|triag|appointment|eg[d|d]|colonoscopy|capacity/,
      ],
      [
        "quality",
        /quality|safety|ercp|remimazolam|sedation|guideline|clinical|patient|procedure/,
      ],
      [
        "experience",
        /experience|communication|email|slides|meeting|minutes|message|letter/,
      ],
      [
        "financial",
        /budget|utilization|compensation|timesheet|report|strategy|architecture|resource site|dashboard/,
      ],
    ];
    return PILLARS.find(
      (p) => p.id === rules.find(([, regex]) => regex.test(text))?.[0],
    );
  }

  function renderCompass() {
    const counts = [
      [PILLARS.length, "domains"],
      [SNAPSHOT.dashboards.length, "instruments"],
      [SNAPSHOT.tasks.length, "active Skoll tasks"],
      [METRICS.length, "recorded measures"],
      [METRICS.filter((m) => m.status === "none").length, "without a reading"],
    ];
    $("#compassReadout").innerHTML = counts
      .map(
        ([value, label], index) => `
      <div class="readout-cell r${index + 1}"><b>${value}</b><span>${label}</span></div>`,
      )
      .join("");
  }

  function renderDomains() {
    $("#domainMatrix").innerHTML = ["h", "s"]
      .map(
        (wing) =>
          `<section class="domain-wing" data-wing="${wing}"><header class="domain-wing-head"><h2>${wing === "h" ? "Hathi" : "Skoll"}</h2><span>${wing === "h" ? "The life within" : "The work in the world"} · 5 domains</span></header>${PILLARS.filter(
            (p) => p.w === wing,
          )
            .map((p, index) => {
              const measures = METRICS.filter(
                (metric) => metric.pillar === p.name,
              );
              const tasks = SNAPSHOT.tasks.filter(
                (task) => pillarForTask(task)?.id === p.id,
              );
              return `<button class="domain-row ${p.w}" data-pillar="${esc(p.id)}" data-wing="${p.w}">
        <span class="domain-name"><b>${esc(p.name)}</b><small>${esc(p.realm)}</small></span>
        <span class="domain-arrow" aria-hidden="true">${icon('<path d="M6 18 18 6M6 6h12v12"/>')}</span>
        <span class="domain-vector">${esc(p.being)}</span>
        <span class="domain-evidence"><span class="condition-dots" aria-label="${measures
          .map((m) => `${m.metric}: ${statusLabel[m.status]}`)
          .join("; ")
          .replace(
            /"/g,
            "&quot;",
          )}">${measures.map((m) => `<i class="condition-dot ${m.status}" aria-hidden="true"></i>`).join("")} <b>${measures.length}</b> ${measures.length === 1 ? "measure" : "measures"}</span><span>${p.w === "h" ? "Tasks outside this snapshot" : `<b>${tasks.length}</b> suggested tasks`}</span></span>
      </button>`;
            })
            .join("")}</section>`,
      )
      .join("");
    $$("[data-pillar]").forEach((button) =>
      button.addEventListener("click", () =>
        selectPillar(button.dataset.pillar),
      ),
    );
    renderWing();
  }

  function selectPillar(id) {
    const p = PILLARS.find((item) => item.id === id);
    if (!p) return;
    $$("[data-pillar]").forEach((node) =>
      node.classList.toggle("selected", node.dataset.pillar === id),
    );
    lineage(p);
    openDrawer({
      eyebrow: `${p.w === "h" ? "Hathi" : "Skoll"} · ${p.realm}`,
      title: p.name,
      intro: p.roles,
      sections: [
        ["Being", esc(p.being)],
        ["Becoming", esc(p.becoming)],
        [
          "2026 + horizon",
          `<ul>${p.objs.map((o) => `<li>${esc(o)}</li>`).join("")}</ul>`,
        ],
        [
          "Guardianship",
          `<b>${esc(p.companion)}</b><br>${esc(p.agent)}<br><span class="muted">Value dyad · ${esc(p.dyad)}</span>`,
        ],
      ],
    });
    $("#drawerBody").insertAdjacentHTML(
      "beforeend",
      `<div class="drawer-actions"><button class="primary-btn" id="domainMeasures">F4 · Examine measures →</button><button class="ghost-btn" id="domainTasks">F5 · Explore tasks →</button></div>`,
    );
    $("#domainMeasures").onclick = () => focusDomain(id, 4);
    $("#domainTasks").onclick = () => focusDomain(id, 5);
  }

  function dashboardGroup(dashboard) {
    const haystack =
      `${dashboard.title} ${(dashboard.tags || []).join(" ")}`.toLowerCase();
    if (/dsagi|meeting|first contact|long hall|sheikah/.test(haystack))
      return "DSA GI";
    if (/task|performance|kiroshi|health|dojo|forge/.test(haystack))
      return "Execution";
    if (/kalpa|memory|garden|penelope|chronos|time/.test(haystack))
      return "Time & memory";
    if (
      /totem|moc|philosophy|lattice|orrery|meru|holodeck|faces|middle way/.test(
        haystack,
      )
    )
      return "Knowledge";
    return "Identity";
  }

  function dashboardAge(dashboard) {
    const parsed = Date.parse(dashboard.refreshed || "");
    const reference = Date.parse(SNAPSHOT.generatedAt || "") || Date.now();
    if (!Number.isFinite(parsed))
      return { days: null, status: "unknown", label: "date unknown" };
    const days = Math.max(0, Math.floor((reference - parsed) / 86400000));
    return {
      days,
      status: days <= 14 ? "recent" : days <= 45 ? "middle" : "older",
      label: `${days}d`,
    };
  }

  function renderFleet() {
    const query = state.fleetQuery.trim().toLowerCase();
    const records = SNAPSHOT.dashboards.filter((d) =>
      `${d.title} ${d.description} ${(d.tags || []).join(" ")}`
        .toLowerCase()
        .includes(query),
    );
    const states = ["recent", "middle", "older", "unknown"];
    const ageLabels = ["0–14 days", "15–45 days", "46+ days", "Undated"];
    const totals = states.map(
      (status) =>
        records.filter((d) => dashboardAge(d).status === status).length,
    );
    $("#fleetTallies").innerHTML = states
      .map(
        (status, i) =>
          `<span class="fleet-tally"><b>${totals[i]}</b><i>${ageLabels[i]}</i></span>`,
      )
      .join("");
    $("#fleetCount").textContent =
      `${records.length} / ${SNAPSHOT.dashboards.length} instruments`;
    const sorted = records.sort(
      (a, b) => (dashboardAge(b).days ?? -1) - (dashboardAge(a).days ?? -1),
    );
    $("#fleetGrid").innerHTML =
      `<div class="fleet-scale"><span>Instrument ↗</span><span class="fleet-group">Collection</span><span class="age-axis"><span>0</span><span>30</span><span>60</span><span>90+</span></span><span>Days</span></div>` +
      (sorted
        .map((d) => {
          const age = dashboardAge(d);
          return `<a class="fleet-item" href="${esc(d.uri)}" data-dashboard="${esc(d.title)}"><b>${esc(d.title)}</b><span class="fleet-group">${esc(dashboardGroup(d))}</span><span class="age-track ${age.days === null ? "unknown" : ""}" style="--age:${(Math.min(age.days ?? 0, 90) / 90) * 100}%" aria-hidden="true"><i></i></span><small>${age.days === null ? "—" : esc(age.label)}</small></a>`;
        })
        .join("") ||
        '<div class="empty-state">No matching instruments. Try a different name.</div>');
  }

  function renderMetrics() {
    const rows = METRICS.filter(
      (r) =>
        (state.wing === "both" || r.w === state.wing) &&
        (!state.domain ||
          r.pillar === PILLARS.find((p) => p.id === state.domain)?.name),
    );
    const tallies = ["good", "warn", "critical", "none"].map(
      (status) => rows.filter((row) => row.status === status).length,
    );
    $("#metricTallies").innerHTML = [
      [tallies[3], "No reading", "none"],
      [tallies[2], "Off course", "critical"],
      [tallies[1], "Watch", "warn"],
      [tallies[0], "On course", "good"],
    ]
      .map(
        ([value, label, status]) =>
          `<div class="metric-tally ${status}"><b>${value}</b><span>${label}</span></div>`,
      )
      .join("");
    $("#metricRows").innerHTML = rows
      .map(
        (r) => `
      <div class="metric-row" data-wing="${r.w}">
        <div class="metric-label"><span>${esc(r.pillar)}</span><b>${esc(r.metric)}</b></div>
        <div class="metric-status ${r.status}"><i class="condition-dot" aria-hidden="true"></i>${esc(statusLabel[r.status])}</div>
        <div class="metric-values"><b>${esc(r.current)}</b><span>Target ${esc(r.target)}</span></div>
        <div class="metric-owner"><b>${esc(r.class)}</b><span>${esc(r.owner)}</span></div>
      </div>`,
      )
      .join("");
  }

  function taskMatches(task) {
    if (state.wing === "h") return false;
    if (state.domain && pillarForTask(task)?.id !== state.domain) return false;
    const query = state.taskQuery.trim().toLowerCase();
    if (!query) return true;
    return `${task.title} ${task.status} ${task.priority} ${task.scheduled} ${task.due} ${readableRealm(task.realms)} ${(task.tags || []).join(" ")}`
      .toLowerCase()
      .includes(query);
  }

  function renderBoard() {
    const scoped = SNAPSHOT.tasks.filter(taskMatches);
    const tasks = scoped
      .filter(
        (t) =>
          (!state.stage || t.status === state.stage) &&
          (!state.priority || t.priority === state.priority),
      )
      .sort(
        (a, b) =>
          (priorityRank[a.priority] ?? 3) - (priorityRank[b.priority] ?? 3),
      );
    const total = Math.max(1, scoped.length);
    const stages = ["gate", "forge", "flow"];
    $("#flowRibbon").innerHTML =
      `<div class="flow-heading"><b>Work in motion</b><span>Choose a stage to focus</span></div><div class="flow-bar" aria-hidden="true">${stages.map((stage) => `<span class="flow-segment" style="--weight:${(scoped.filter((t) => t.status === stage).length / total) * 100};--color:var(--${stage})"></span>`).join("")}</div><div class="stage-labels">${stages.map((stage) => `<button class="flow-stage ${state.stage === stage ? "active" : ""}" data-stage="${stage}" aria-pressed="${state.stage === stage}"><b>${scoped.filter((t) => t.status === stage).length}</b><i>${stageLabel[stage]}</i></button>`).join("")}</div>`;
    const priorities = [
      "high",
      "normal",
      "low",
      ...new Set(
        scoped
          .map((t) => t.priority)
          .filter((p) => !["high", "normal", "low"].includes(p)),
      ),
    ];
    const maxCount = Math.max(
      1,
      ...priorities.flatMap((p) =>
        stages.map(
          (s) =>
            scoped.filter((t) => t.priority === p && t.status === s).length,
        ),
      ),
    );
    $("#priorityMatrix").innerHTML =
      `<div class="priority-header"><span>Priority ↓</span>${stages.map((s) => `<span>${stageLabel[s]}</span>`).join("")}</div>` +
      priorities
        .map(
          (priority) =>
            `<div class="priority-row"><button data-priority="${esc(priority)}" class="${state.priority === priority ? "active" : ""}" aria-pressed="${state.priority === priority}">${esc(priority)}</button>${stages
              .map((stage) => {
                const count = scoped.filter(
                  (t) => t.status === stage && t.priority === priority,
                ).length;
                return `<span class="priority-bar"><i style="--share:${(count / maxCount) * 100};--color:var(--${stage})" aria-hidden="true"></i><span>${count}</span></span>`;
              })
              .join("")}</div>`,
        )
        .join("");
    ["gate", "forge", "flow"].forEach((stage) => {
      const stageTasks = tasks.filter((task) => task.status === stage);
      $(`#count-${stage}`).textContent = String(stageTasks.length);
      $(`#tasks-${stage}`).innerHTML =
        stageTasks
          .slice(0, 80)
          .map(
            (task) => `
        <button class="task-card ${esc(task.priority)}" data-task="${esc(task.id)}">
          <span class="task-signal" aria-hidden="true"></span><span class="task-title">${esc(task.title)}</span>
          <span class="task-meta">
            <span>${esc(task.priority)} priority</span>${task.scheduled ? `<span class="date">${esc(shortDate(task.scheduled))}</span>` : ""}
            ${task.due ? `<span class="date">→ ${esc(shortDate(task.due))}</span>` : ""}
          </span>
        </button>`,
          )
          .join("") || '<div class="empty-state">Clear.</div>';
    });
    $("#boardResultCount").textContent =
      `${tasks.length} of ${scoped.length} active tasks`;
    $$("[data-task]").forEach((button) =>
      button.addEventListener("click", () => selectTask(button.dataset.task)),
    );
    $$("[data-stage]").forEach(
      (b) =>
        (b.onclick = () => {
          state.stage =
            state.stage === b.dataset.stage ? null : b.dataset.stage;
          renderBoard();
          renderScope();
        }),
    );
    $$("[data-priority]").forEach(
      (b) =>
        (b.onclick = () => {
          state.priority =
            state.priority === b.dataset.priority ? null : b.dataset.priority;
          renderBoard();
          renderScope();
        }),
    );
    updateScrollHints();
  }

  function updateScrollHints() {
    $$(".task-list").forEach((list) => {
      const hint = list.nextElementSibling;
      if (!hint?.classList.contains("scroll-hint")) return;
      hint.hidden = list.scrollHeight <= list.clientHeight + 1;
      const count = list.querySelectorAll(".task-card").length;
      hint.innerHTML = `${icon('<path d="M12 4v16m-5-5 5 5 5-5"/>')}<span>Scroll to browse all ${count} tasks</span>`;
    });
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
        [
          "Board coordinates",
          `${esc(readableRealm(task.realms))}<br>${task.scheduled ? `Scheduled ${esc(shortDate(task.scheduled))}` : "Unscheduled"}${task.due ? ` · Due ${esc(shortDate(task.due))}` : ""}`,
        ],
        [
          "Suggested domain",
          `${esc(pillar?.name || "Unmapped")} · ${esc(pillar?.dyad || "No dyad assigned")}<p class="data-note">Keyword-based suggestion, not a canonical TaskNotes assignment.</p>`,
        ],
        [
          "Sync contract",
          "This page is an encrypted read model. Change status, dates, and context in the TaskNotes note; the next Astrolabe build will ingest it.",
        ],
      ],
      uri: task.uri,
    });
  }

  function openDrawer(content) {
    state.selected = content;
    $("#drawerEyebrow").textContent = content.eyebrow || "Astrolabe reading";
    $("#drawerTitle").textContent = content.title || "Selection";
    $("#drawerIntro").textContent = content.intro || "";
    $("#drawerBody").innerHTML = (content.sections || [])
      .map(
        ([title, body]) =>
          `<section class="drawer-section"><h3>${esc(title)}</h3><div>${body}</div></section>`,
      )
      .join("");
    $("#drawerOpen").hidden = !content.uri;
    if (content.uri) $("#drawerOpen").href = content.uri;
    $("#drawer").classList.add("open");
    $("#drawerBackdrop").classList.add("show");
    $("#drawer").setAttribute("aria-hidden", "false");
    openLayer($("#drawer"), $("#drawerClose"));
  }

  function closeDrawer() {
    $("#drawer").classList.remove("open");
    $("#drawerBackdrop").classList.remove("show");
    $("#drawer").setAttribute("aria-hidden", "true");
    closeLayer($("#drawer"));
  }

  let activeLayer = null,
    returnFocus = null;
  function openLayer(layer, firstFocus) {
    returnFocus = document.activeElement;
    activeLayer = layer;
    layer.inert = false;
    layer.setAttribute("role", "dialog");
    layer.setAttribute("aria-modal", "true");
    $(".app-shell").inert = true;
    document.body.style.overflow = "hidden";
    firstFocus.focus();
  }
  function closeLayer(layer) {
    if (activeLayer !== layer) return;
    layer.inert = true;
    activeLayer = null;
    $(".app-shell").inert = false;
    document.body.style.overflow = "";
    if (returnFocus?.isConnected) returnFocus.focus();
  }

  function renderPalette(query = "") {
    const q = query.trim().toLowerCase();
    const items = [
      ...PILLARS.map((p) => ({
        kind: "domain",
        title: p.name,
        detail: `${p.realm} · ${p.dyad}`,
        action: () => {
          setAltitude(2);
          selectPillar(p.id);
        },
      })),
      ...SNAPSHOT.dashboards.map((d) => ({
        kind: "dashboard",
        title: d.title,
        detail: dashboardGroup(d),
        action: () => {
          location.href = d.uri;
        },
      })),
      ...SNAPSHOT.tasks.map((t) => ({
        kind: "task",
        title: t.title,
        detail: `${stageLabel[t.status]} · ${t.priority}`,
        action: () => {
          setAltitude(5);
          selectTask(t.id);
        },
      })),
      ...ALTITUDES.map((a) => ({
        kind: "altitude",
        title: `F${a.n} ${a.name}`,
        detail: a.question,
        action: () => setAltitude(a.n),
      })),
    ]
      .filter(
        (item) =>
          !q ||
          `${item.title} ${item.detail} ${item.kind}`.toLowerCase().includes(q),
      )
      .slice(0, 40);
    $("#paletteResults").innerHTML =
      items
        .map(
          (item, index) => `
      <button class="palette-result" data-result="${index}"><span class="kind">${esc(item.kind)}</span><b>${esc(item.title)}</b><small>${esc(item.detail)}</small></button>`,
        )
        .join("") ||
      '<div class="empty-state">Nothing in this sky answers that name.</div>';
    $$("[data-result]").forEach((button) =>
      button.addEventListener("click", () => {
        closePalette();
        items[Number(button.dataset.result)].action();
      }),
    );
  }

  function openPalette() {
    $("#palette").classList.add("open");
    $("#paletteInput").value = "";
    renderPalette();
    openLayer($("#palette"), $("#paletteInput"));
  }
  function closePalette() {
    $("#palette").classList.remove("open");
    closeLayer($("#palette"));
  }
  function closeObservatory() {
    $("#observatory").classList.remove("open");
    closeLayer($("#observatory"));
  }

  function renderQuestions() {
    $("#questionGrid").innerHTML = QUESTIONS.map(
      (q, index) => `
      <article class="question"><b>${index + 1}. ${esc(q.t)}</b><p>${esc(q.c)}</p><textarea data-q="${esc(q.id)}" aria-label="Answer to ${esc(q.t)}"></textarea><div class="q-actions"><button class="save" data-q="${esc(q.id)}" disabled>Save</button><span class="saved" data-q="${esc(q.id)}"></span></div></article>`,
    ).join("");
    window.ASTRO_QUESTIONS = QUESTIONS;
  }

  function applyTheme(theme) {
    document.documentElement.dataset.theme = theme;
    storage.set("astrolabe-theme", theme);
    $("#themeToggle").innerHTML =
      `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">${theme === "dark" ? '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>' : '<circle cx="12" cy="12" r="8"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/>'}</svg>`;
    $("#themeToggle").setAttribute(
      "aria-label",
      theme === "dark" ? "Use light mode" : "Use dark mode",
    );
    window.dispatchEvent(new Event("astrolabe-theme"));
  }

  function initThree() {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const script = document.createElement("script");
    script.src =
      "https://cdn.jsdelivr.net/npm/three@0.160.1/build/three.min.js";
    script.onload = () => {
      const THREE = window.THREE;
      const canvas = $("#starfield");
      if (!THREE || !canvas) return;
      let renderer;
      try {
        renderer = new THREE.WebGLRenderer({
          canvas,
          alpha: true,
          antialias: true,
          powerPreference: "low-power",
        });
      } catch {
        document.body.classList.add("three-fallback");
        return;
      }
      renderer.setPixelRatio(Math.min(devicePixelRatio, 1.7));
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(
        46,
        innerWidth / innerHeight,
        0.1,
        100,
      );
      camera.position.set(0, 0, 11);
      const group = new THREE.Group();
      scene.add(group);

      const parseColor = (name) =>
        new THREE.Color(
          getComputedStyle(document.documentElement)
            .getPropertyValue(name)
            .trim(),
        );
      const uniforms = {
        uTime: { value: 0 },
        uBrass: { value: parseColor("--brass") },
        uInk: { value: parseColor("--ink") },
      };
      const shader = new THREE.ShaderMaterial({
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        uniforms,
        vertexShader:
          "varying vec2 vUv; void main(){vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}",
        fragmentShader: `varying vec2 vUv; uniform float uTime; uniform vec3 uBrass; uniform vec3 uInk;
          float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
          float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
          void main(){vec2 p=vUv*4.;float fog=n(p+vec2(uTime*.025,-uTime*.018))*n(p*1.8-uTime*.012);float vign=1.-smoothstep(.18,.9,distance(vUv,vec2(.72,.43)));float a=fog*vign*.075;gl_FragColor=vec4(mix(uInk,uBrass,.72),a);}`,
      });
      const plane = new THREE.Mesh(new THREE.PlaneGeometry(25, 15), shader);
      plane.position.z = -5;
      scene.add(plane);

      const ringMaterial = new THREE.LineBasicMaterial({
        color: uniforms.uBrass.value,
        transparent: true,
        opacity: 0.19,
      });
      [1.45, 2.4, 3.5, 4.7].forEach((radius, index) => {
        const points = Array.from(
          { length: 129 },
          (_, i) =>
            new THREE.Vector3(
              Math.cos((i / 128) * Math.PI * 2) * radius,
              Math.sin((i / 128) * Math.PI * 2) *
                radius *
                (0.58 + index * 0.05),
              0,
            ),
        );
        const ring = new THREE.LineLoop(
          new THREE.BufferGeometry().setFromPoints(points),
          ringMaterial.clone(),
        );
        ring.rotation.set(index * 0.22, index * 0.14, index * 0.25);
        group.add(ring);
      });
      const relic = new THREE.Mesh(
        new THREE.IcosahedronGeometry(0.72, 1),
        new THREE.MeshBasicMaterial({
          color: uniforms.uBrass.value,
          wireframe: true,
          transparent: true,
          opacity: 0.22,
        }),
      );
      group.add(relic);

      const count = 520;
      const positions = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        const radius = 2.4 + Math.random() * 6.8;
        const angle = Math.random() * Math.PI * 2;
        positions[i * 3] = Math.cos(angle) * radius;
        positions[i * 3 + 1] = Math.sin(angle) * radius * 0.62;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 4;
      }
      const starGeo = new THREE.BufferGeometry();
      starGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      const stars = new THREE.Points(
        starGeo,
        new THREE.PointsMaterial({
          color: uniforms.uBrass.value,
          size: 0.025,
          transparent: true,
          opacity: 0.48,
        }),
      );
      group.add(stars);

      let targetZ = 11 - (state.altitude - 1) * 0.38;
      let px = 0,
        py = 0;
      addEventListener(
        "pointermove",
        (event) => {
          px = (event.clientX / innerWidth - 0.5) * 0.22;
          py = (event.clientY / innerHeight - 0.5) * 0.16;
        },
        { passive: true },
      );
      addEventListener("astrolabe-altitude", (event) => {
        targetZ = 11 - (Number(event.detail) - 1) * 0.38;
        resize();
        resume();
      });
      addEventListener("astrolabe-theme", () => {
        uniforms.uBrass.value.set(parseColor("--brass"));
        uniforms.uInk.value.set(parseColor("--ink"));
        group.traverse((obj) => {
          if (obj.material?.color)
            obj.material.color.set(uniforms.uBrass.value);
        });
      });
      function resize() {
        const { width, height } = canvas.parentElement.getBoundingClientRect();
        if (!width || !height) return;
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
      }
      addEventListener("resize", resize, { passive: true });
      resize();
      const clock = new THREE.Clock();
      let frameId = null;
      function frame() {
        frameId = null;
        if (document.hidden || state.altitude !== 1) return;
        const t = clock.getElapsedTime();
        uniforms.uTime.value = t;
        camera.position.z += (targetZ - camera.position.z) * 0.035;
        group.rotation.z = t * 0.008 + px;
        group.rotation.x += (py - group.rotation.x) * 0.018;
        relic.rotation.x = t * 0.09;
        relic.rotation.y = t * 0.11;
        renderer.render(scene, camera);
        frameId = requestAnimationFrame(frame);
      }
      function resume() {
        if (frameId !== null) cancelAnimationFrame(frameId);
        frameId = null;
        if (!document.hidden && state.altitude === 1) frame();
      }
      document.addEventListener("visibilitychange", resume);
      resume();
    };
    script.onerror = () => document.body.classList.add("three-fallback");
    document.head.appendChild(script);
  }

  function bind() {
    $("#clearFocus").onclick = () => {
      state.domain = null;
      state.stage = null;
      state.priority = null;
      state.wing = "both";
      resetTrace();
      storage.set("astrolabe-wing", "both");
      renderWing();
      renderMetrics();
      renderBoard();
      renderScope();
    };
    $("#prevAltitude").addEventListener("click", () =>
      setAltitude(state.altitude - 1),
    );
    $("#nextAltitude").addEventListener("click", () =>
      setAltitude(state.altitude + 1),
    );
    $$(".wing-btn").forEach((button) =>
      button.addEventListener("click", () => setWing(button.dataset.wing)),
    );
    $("#themeToggle").addEventListener("click", () =>
      applyTheme(
        document.documentElement.dataset.theme === "dark" ? "light" : "dark",
      ),
    );
    $("#searchButton").addEventListener("click", openPalette);
    $("#palette").addEventListener("click", (event) => {
      if (event.target === $("#palette")) closePalette();
    });
    $("#paletteInput").addEventListener("input", (event) =>
      renderPalette(event.target.value),
    );
    $("#drawerClose").addEventListener("click", closeDrawer);
    $("#drawerBackdrop").addEventListener("click", closeDrawer);
    $("#fleetFilter").addEventListener("input", (event) => {
      state.fleetQuery = event.target.value;
      renderFleet();
    });
    $("#taskFilter").addEventListener("input", (event) => {
      state.taskQuery = event.target.value;
      renderBoard();
    });
    $("#observatoryButton").addEventListener("click", () => {
      $("#observatory").classList.add("open");
      openLayer($("#observatory"), $("#observatoryClose"));
    });
    $("#observatoryClose").addEventListener("click", closeObservatory);
    addEventListener("keydown", (event) => {
      const typing = /INPUT|TEXTAREA|SELECT/.test(
        document.activeElement?.tagName,
      );
      if (event.key === "Escape") {
        closeDrawer();
        closePalette();
        closeObservatory();
        return;
      }
      if (activeLayer) {
        if (event.key === "Tab") {
          const nodes = $$(
            'button:not(:disabled), a[href], input, textarea, select, [tabindex="0"]',
            activeLayer,
          ).filter((el) => !el.hidden && el.getClientRects().length);
          const first = nodes[0],
            last = nodes[nodes.length - 1];
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last?.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first?.focus();
          }
        }
        return;
      }
      if (!typing && event.key === "/") {
        event.preventDefault();
        openPalette();
      }
      if (!typing && /^[1-5]$/.test(event.key)) setAltitude(Number(event.key));
      if (!typing && event.key === "[") setAltitude(state.altitude - 1);
      if (!typing && event.key === "]") setAltitude(state.altitude + 1);
    });
  }

  function init() {
    $("#searchButton").insertAdjacentHTML(
      "afterbegin",
      icon('<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4.5 4.5"/>'),
    );
    $("#observatoryButton").innerHTML = icon(
      '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 2-2.5 2-2.5 4m0 3v.2"/>',
    );
    $("#prevAltitude").innerHTML = icon('<path d="M5 12h14"/>');
    $("#nextAltitude").innerHTML = icon('<path d="M5 12h14M12 5v14"/>');
    ["#drawerClose", "#observatoryClose"].forEach(
      (id) => ($(id).innerHTML = icon('<path d="m6 6 12 12M6 18 18 6"/>')),
    );
    const resizeObserver = new ResizeObserver(updateScrollHints);
    $$(".task-list").forEach((list, i) => {
      list.tabIndex = 0;
      list.setAttribute("role", "region");
      list.setAttribute(
        "aria-label",
        `${["Gate", "Forge", "Flow"][i]} tasks, scroll to browse`,
      );
      list.insertAdjacentHTML(
        "afterend",
        '<div class="scroll-hint" hidden></div>',
      );
      resizeObserver.observe(list);
    });
    const preferred =
      storage.get("astrolabe-theme") ||
      (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    applyTheme(preferred);
    $("#snapshotTime").textContent = SNAPSHOT.generatedAt
      ? new Date(SNAPSHOT.generatedAt).toLocaleString([], {
          dateStyle: "medium",
          timeStyle: "short",
        })
      : "snapshot unavailable";
    $("#sourceStamp").textContent = SNAPSHOT.generatedAt
      ? new Date(SNAPSHOT.generatedAt).toLocaleDateString([], {
          month: "short",
          day: "numeric",
          year: "numeric",
        })
      : "snapshot unavailable";
    renderCompass();
    renderDomains();
    renderFleet();
    renderMetrics();
    renderBoard();
    renderQuestions();
    bind();
    renderWing();
    setAltitude(state.altitude);
    initThree();
    setTimeout(() => window.dispatchEvent(new Event("astrolabe-ready")), 0);
  }

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();
