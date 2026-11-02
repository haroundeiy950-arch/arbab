(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const esc = (value) => App.escapeHtml(value);
  let latest = null;
  let refreshing = false;
  let refreshTimer = null;

  function chipText(node, text) {
    if (!node) return;
    const label = node.querySelector("span:last-child");
    if (label) label.textContent = text;
  }

  function setChip(node, enabled, onText, offText, warning = false) {
    if (!node) return;
    node.classList.toggle("off", !enabled);
    node.classList.toggle("warn", Boolean(warning));
    chipText(node, enabled ? onText : offText);
  }

  function eventThumb(event, small = false) {
    if (event.snapshot_url) {
      return `<img class="${small ? "alert-thumb" : ""}" src="${esc(event.snapshot_url)}" alt="" loading="lazy">`;
    }
    return `<div class="event-thumb-fallback"><svg><use href="#${App.kindIcon(event.kind)}"></use></svg></div>`;
  }

  function eventCard(event) {
    const description = App.localizedDescription(event);
    return `
      <article class="event-card" data-event-id="${event.id}" tabindex="0">
        <div class="event-thumb-box">
          ${event.snapshot_url ? `<img src="${esc(event.snapshot_url)}" alt="" loading="lazy">` : `<div class="event-thumb-fallback"><svg><use href="#${App.kindIcon(event.kind)}"></use></svg></div>`}
          <div class="event-thumb-top">
            <span class="badge ${App.severityClass(event.severity)}">${esc(App.t(`severity.${event.severity}`))}</span>
            <span class="badge">${esc(App.t(`kind.${event.kind}`))}</span>
          </div>
        </div>
        <div class="event-body">
          <div class="event-title">${esc(event.title)}</div>
          ${event.person_name ? `<div class="event-person">${esc(event.person_name)}</div>` : ""}
          <div class="event-foot"><span>${esc(App.timeAgo(event.created_at))}</span><span>#${event.id}</span></div>
        </div>
      </article>`;
  }

  function bindEventCards(root) {
    if (!root) return;
    root.querySelectorAll("[data-event-id]").forEach((card) => {
      const open = () => App.openEvent(Number(card.dataset.eventId), () => refresh());
      card.addEventListener("click", open);
      card.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          open();
        }
      });
    });
  }

  function renderStats(status) {
    const camera = status.camera || {};
    const events = status.events || {};
    const audio = status.audio || {};
    const agent = status.agent || {};
    $("stat-people").textContent = camera.people_count ?? 0;
    $("stat-known").textContent = camera.known_count ?? 0;
    $("stat-unknown").textContent = camera.unknown_count ?? 0;
    $("stat-alerts").textContent = events.last24 ?? 0;
    $("stat-unique").textContent = camera.unique_seen ?? 0;
    $("stat-alerts").title = App.t("dash.alertCount", { count: events.last24 ?? 0 });

    $("camera-source").textContent = camera.source ? `${camera.source}` : "source ...";
    $("video-fps").textContent = `${camera.fps ?? 0} fps`;
    $("video-demo").hidden = !camera.demo;
    setChip($("ai-state"), Boolean(camera.models && camera.models.ai_enabled), App.t("dash.aiOn"), App.t("dash.aiOff"));
    setChip($("audio-state"), Boolean(audio.monitoring), App.t("dash.audioOn"), App.t("dash.audioOff"), Boolean(audio.monitoring && !audio.mic_available));
    const rec = $("rec-state");
    if (rec) rec.hidden = !camera.recording;
    const recordLabel = $("record-label");
    if (recordLabel) recordLabel.textContent = camera.recording ? App.t("dash.stopRecording") : App.t("dash.startRecording");
    const recordButton = $("btn-record");
    if (recordButton) recordButton.classList.toggle("btn-primary", Boolean(camera.recording));

    const models = camera.models || {};
    const pipes = [
      ["pipe-objects", models.objects],
      ["pipe-pose", models.pose],
      ["pipe-faces", models.faces],
      ["pipe-ocr", models.plates],
      ["pipe-mic", audio.mic_available],
      ["pipe-agent", agent.provider ? true : false]
    ];
    pipes.forEach(([id, ok]) => {
      const node = $(id);
      if (!node) return;
      node.textContent = ok ? App.t("dash.ready") : (id === "pipe-mic" ? (audio.mic_error ? App.t("dash.notReady") : App.t("dash.notReady")) : App.t("dash.notReady"));
      node.classList.toggle("ok", Boolean(ok));
      node.classList.toggle("warn", !ok && id === "pipe-mic" && audio.monitoring);
    });
    const mic = $("pipe-mic");
    if (mic && audio.monitoring && !audio.mic_available) {
      mic.textContent = App.t("dash.notReady");
      mic.title = audio.mic_error || "";
    }
    const agentChip = $("agent-chip");
    if (agentChip) agentChip.textContent = agent.provider || "local-rag";
    const transcript = $("last-transcript");
    const transcriptText = $("last-transcript-text");
    const speech = (status.recent_events || []).find((event) => (event.kind === "speech" || event.kind === "question") && event.transcript);
    if (transcript && transcriptText) {
      transcript.hidden = !speech;
      transcriptText.textContent = speech ? speech.transcript : "";
    }
    const updated = $("feed-updated");
    if (updated) updated.textContent = `updated ${App.formatTime(new Date().toISOString(), false)}`;

    renderThreat(camera.alarm);
  }

  function renderThreat(alarm) {
    const card = $("threat-card");
    const title = card ? card.querySelector(".threat-title") : null;
    const sub = card ? card.querySelector(".threat-sub") : null;
    const chip = $("alarm-chip");
    if (title) title.textContent = alarm ? App.t("dash.activeThreat") : App.t("dash.noThreat");
    if (sub) sub.textContent = alarm ? (App.lang === "ar" ? (alarm.ar || App.t("dash.activeThreatSub")) : (alarm.en || App.t("dash.activeThreatSub"))) : App.t("dash.noThreatSub");
    if (card) card.classList.toggle("alert", Boolean(alarm));
    if (chip) {
      chip.textContent = App.soundEnabled ? App.t("dash.soundOn") : App.t("dash.soundOff");
      chip.classList.toggle("on", App.soundEnabled);
    }
  }

  function renderAlerts(events) {
    const root = $("recent-alerts");
    if (!root) return;
    const alerts = events.filter((event) => event.severity === "critical" || event.severity === "warning").slice(0, 5);
    if (!alerts.length) {
      root.innerHTML = `<div class="empty-inline">${esc(App.t("dash.noThreatSub"))}</div>`;
      return;
    }
    root.innerHTML = alerts.map((event) => `
      <div class="alert-row" data-event-id="${event.id}" tabindex="0">
        <span class="sev-bar ${App.severityClass(event.severity)}"></span>
        ${event.snapshot_url ? `<img class="alert-thumb" src="${esc(event.snapshot_url)}" alt="" loading="lazy">` : `<div class="alert-thumb event-thumb-fallback"><svg><use href="#${App.kindIcon(event.kind)}"></use></svg></div>`}
        <div class="alert-body">
          <div class="alert-title">${esc(event.title)}</div>
          <div class="alert-meta"><span>${esc(App.t(`kind.${event.kind}`))}</span><span>·</span><span>${esc(App.timeAgo(event.created_at))}</span></div>
        </div>
      </div>`).join("");
    bindEventCards(root);
  }

  function renderActivity(events) {
    const root = $("activity-feed");
    if (!root) return;
    const interesting = new Set(["gesture", "plate", "speech", "question", "inquiry", "motion", "phone", "crowd", "glasses", "risk_scan"]);
    const items = events.filter((event) => interesting.has(event.kind)).slice(0, 6);
    if (!items.length) {
      root.innerHTML = `<div class="empty-inline">${esc(App.t("dash.waiting"))}</div>`;
      return;
    }
    root.innerHTML = items.map((event) => `
      <div class="activity-item" data-event-id="${event.id}">
        <div class="activity-icon"><svg><use href="#${App.kindIcon(event.kind)}"></use></svg></div>
        <div class="activity-main">
          <div class="activity-title">${esc(event.title)} <span class="badge ${App.severityClass(event.severity)}">${esc(App.t(`kind.${event.kind}`))}</span></div>
          <div class="activity-text">${esc(App.localizedDescription(event) || "")}</div>
        </div>
        <span class="activity-time">${esc(App.timeAgo(event.created_at))}</span>
      </div>`).join("");
    bindEventCards(root);
  }

  function renderRecent(events) {
    const root = $("recent-events");
    if (!root) return;
    if (!events.length) {
      root.innerHTML = `<div class="empty-state">${esc(App.t("events.none"))}</div>`;
      return;
    }
    root.innerHTML = events.slice(0, 4).map(eventCard).join("");
    bindEventCards(root);
  }

  function render(status) {
    latest = status;
    renderStats(status);
    const events = status.recent_events || [];
    renderAlerts(events);
    renderActivity(events);
    renderRecent(events);
  }

  async function refresh() {
    if (refreshing) return;
    refreshing = true;
    try {
      const status = await App.api("/api/status");
      render(status);
    } catch (error) {
      if (!latest) App.toast(error.message, "error");
    } finally {
      refreshing = false;
    }
  }

  function scheduleRefresh(delay = 600) {
    if (refreshTimer) window.clearTimeout(refreshTimer);
    refreshTimer = window.setTimeout(() => {
      refreshTimer = null;
      refresh();
    }, delay);
  }

  async function withButton(button, work) {
    if (!button) return;
    button.disabled = true;
    try { await work(); } catch (error) { App.toast(error.message, "error"); } finally { button.disabled = false; }
  }

  function bindActions() {
    $("btn-snapshot").addEventListener("click", (event) => withButton(event.currentTarget, async () => {
      const result = await App.api("/api/snapshot", { method: "POST", body: { note: "Manual snapshot from dashboard" } });
      App.toast(App.t("dash.snapshotSaved"), "success");
      if (result.event) App.openEvent(result.event.id, refresh);
      scheduleRefresh(300);
    }));

    $("btn-record").addEventListener("click", (event) => withButton(event.currentTarget, async () => {
      const recording = Boolean(latest && latest.camera && latest.camera.recording);
      const result = await App.api(recording ? "/api/recording/stop" : "/api/recording/start", { method: "POST" });
      App.toast(recording ? App.t("dash.recordingStopped") : App.t("dash.recordingStarted"), "success");
      if (recording && result.url) {
        App.toast(result.url, "info");
      }
      scheduleRefresh(300);
    }));

    $("btn-risk").addEventListener("click", (event) => withButton(event.currentTarget, async () => {
      const result = await App.api("/api/risk_scan", { method: "POST" });
      const found = Array.isArray(result.findings) ? result.findings.length : 0;
      App.toast(found ? App.t("dash.riskDone") : App.t("dash.riskNone"), found ? "warning" : "success");
      if (result.event) App.openEvent(result.event.id, refresh);
      scheduleRefresh(300);
    }));

    $("btn-plate").addEventListener("click", (event) => withButton(event.currentTarget, async () => {
      const result = await App.api("/api/scan/plate", { method: "POST" });
      if (result.plate) {
        App.toast(App.t("dash.plateRead", { plate: result.plate }), "success");
        if (result.event) App.openEvent(result.event.id, refresh);
      } else {
        App.toast(result.message || App.t("dash.plateNone"), "warning");
      }
      scheduleRefresh(300);
    }));

    $("btn-fullscreen").addEventListener("click", () => {
      const wrap = $("video-wrap");
      if (!wrap) return;
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
      else if (wrap.requestFullscreen) wrap.requestFullscreen().catch(() => {});
    });
  }

  document.addEventListener("app:language", () => {
    if (latest) render(latest);
  });
  document.addEventListener("app:sound", () => {
    if (latest) renderThreat(latest.camera ? latest.camera.alarm : null);
  });
  App.onEvent(() => scheduleRefresh(500));

  bindActions();
  refresh();
  window.setInterval(() => {
    if (!document.hidden) refresh();
  }, 5000);
})();
