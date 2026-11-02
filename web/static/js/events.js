(() => {
  "use strict";

  const esc = (value) => App.escapeHtml(value);
  const limit = 24;
  let offset = 0;
  let hasMore = false;
  let events = [];
  let loading = false;
  let liveTimer = null;

  const filterKind = document.getElementById("filter-kind");
  const filterSeverity = document.getElementById("filter-severity");
  const filterSearch = document.getElementById("filter-search");
  const grid = document.getElementById("events-grid");
  const countNode = document.getElementById("events-count");
  const loadMore = document.getElementById("load-more");

  function card(event) {
    return `
      <article class="event-card" data-event-id="${event.id}" tabindex="0">
        <div class="event-thumb-box">
          ${event.snapshot_url ? `<img src="${esc(event.snapshot_url)}" alt="" loading="lazy">` : `<div class="event-thumb-fallback"><svg><use href="#${App.kindIcon(event.kind)}"></use></svg></div>`}
          <div class="event-thumb-top">
            <span class="badge ${App.severityClass(event.severity)}">${esc(App.t(`severity.${event.severity}`))}</span>
            <span class="badge">${esc(App.t(`kind.${event.kind}`) === `kind.${event.kind}` ? event.kind : App.t(`kind.${event.kind}`))}</span>
          </div>
        </div>
        <div class="event-body">
          <div class="event-title">${esc(event.title)}</div>
          ${event.person_name ? `<div class="event-person">${esc(event.person_name)}</div>` : ""}
          <div class="event-foot">
            <span>${esc(App.formatTime(event.created_at))}</span>
            <span>${event.acknowledged ? esc(App.t("common.acknowledged")) : `#${event.id}`}</span>
          </div>
        </div>
      </article>`;
  }

  function bindCards() {
    grid.querySelectorAll("[data-event-id]").forEach((node) => {
      const open = () => App.openEvent(Number(node.dataset.eventId), () => load(true));
      node.addEventListener("click", open);
      node.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          open();
        }
      });
    });
  }

  function render() {
    if (!events.length) {
      grid.innerHTML = `<div class="empty-state">${esc(App.t("events.none"))}</div>`;
    } else {
      grid.innerHTML = events.map(card).join("");
    }
    bindCards();
    if (countNode) {
      countNode.textContent = events.length
        ? App.t(hasMore ? "events.countMore" : "events.count", { count: events.length })
        : "";
    }
    if (loadMore) loadMore.hidden = !hasMore;
  }

  async function load(reset = false) {
    if (loading) return;
    loading = true;
    if (reset) offset = 0;
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (filterKind && filterKind.value) params.set("kind", filterKind.value);
    if (filterSeverity && filterSeverity.value) params.set("severity", filterSeverity.value);
    if (filterSearch && filterSearch.value.trim()) params.set("search", filterSearch.value.trim());
    if (!reset) {
      grid.querySelectorAll("[data-event-id]").forEach((node) => node.style.pointerEvents = "none");
    }
    try {
      const data = await App.api(`/api/events?${params.toString()}`);
      const incoming = data.events || [];
      events = reset ? incoming : events.concat(incoming);
      hasMore = Boolean(data.has_more);
      offset = events.length;
      render();
    } catch (error) {
      if (reset || !events.length) {
        grid.innerHTML = `<div class="empty-state">${esc(App.t("events.loadFailed"))}</div>`;
      }
      App.toast(error.message || App.t("events.loadFailed"), "error");
    } finally {
      loading = false;
      if (loadMore) loadMore.disabled = false;
    }
  }

  function scheduleLiveRefresh() {
    if (liveTimer) window.clearTimeout(liveTimer);
    liveTimer = window.setTimeout(() => {
      liveTimer = null;
      if (!document.hidden) load(true);
    }, 900);
  }

  document.getElementById("apply-filters").addEventListener("click", () => load(true));
  document.getElementById("refresh-events").addEventListener("click", () => load(true));
  if (loadMore) {
    loadMore.addEventListener("click", () => {
      loadMore.disabled = true;
      load(false);
    });
  }
  if (filterSearch) {
    filterSearch.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        load(true);
      }
    });
  }
  [filterKind, filterSeverity].forEach((select) => {
    if (select) select.addEventListener("change", () => load(true));
  });
  document.addEventListener("app:language", render);
  App.onEvent(scheduleLiveRefresh);

  load(true);
})();
