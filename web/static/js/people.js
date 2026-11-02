(() => {
  "use strict";

  const esc = (value) => App.escapeHtml(value);
  let people = [];
  let loading = false;
  const grid = document.getElementById("people-grid");
  const countNode = document.getElementById("people-count");
  const search = document.getElementById("people-search");

  function card(person) {
    return `
      <article class="person-card" data-person-id="${person.id}">
        <div class="person-photo">
          ${person.photo_url ? `<img src="${esc(person.photo_url)}" alt="${esc(person.name)}" loading="lazy">` : `<div class="no-photo"><svg><use href="#i-people"></use></svg></div>`}
          <span class="person-status badge success">${esc(App.t("people.consented"))}</span>
        </div>
        <div class="person-body">
          <div class="person-name">${esc(person.name)}</div>
          <div class="person-role">${esc(person.role || person.company || "")}</div>
          <div class="person-meta">
            ${person.company ? `<span>${esc(person.company)}</span>` : ""}
            <span>${esc(App.formatTime(person.created_at))}</span>
          </div>
          ${person.notes ? `<div class="person-notes">${esc(person.notes)}</div>` : ""}
          <div class="person-actions">
            <button type="button" class="btn small btn-ghost person-delete">${esc(App.t("common.delete"))}</button>
          </div>
        </div>
      </article>`;
  }

  function render() {
    const query = search ? search.value.trim().toLowerCase() : "";
    const filtered = people.filter((person) => {
      if (!query) return true;
      return [person.name, person.role, person.company, person.notes]
        .some((value) => String(value || "").toLowerCase().includes(query));
    });
    if (countNode) countNode.textContent = App.t("people.count", { count: people.length });
    if (!filtered.length) {
      grid.innerHTML = `<div class="empty-state">${esc(people.length ? App.t("common.none") : App.t("people.empty"))}</div>`;
      return;
    }
    grid.innerHTML = filtered.map(card).join("");
    grid.querySelectorAll(".person-delete").forEach((button) => {
      button.addEventListener("click", () => {
        const article = button.closest("[data-person-id]");
        const person = people.find((item) => String(item.id) === String(article.dataset.personId));
        if (!person) return;
        if (!window.confirm(App.t("people.deleteConfirm", { name: person.name }))) return;
        button.disabled = true;
        App.api(`/api/people/${person.id}`, { method: "DELETE" })
          .then(() => {
            App.toast(App.t("common.deleted"), "success");
            load();
          })
          .catch((error) => {
            App.toast(error.message, "error");
            button.disabled = false;
          });
      });
    });
  }

  async function load() {
    if (loading) return;
    loading = true;
    try {
      const data = await App.api("/api/people");
      people = data.people || [];
      render();
    } catch (error) {
      App.toast(error.message, "error");
      grid.innerHTML = `<div class="empty-state">${esc(App.t("common.error"))}</div>`;
    } finally {
      loading = false;
    }
  }

  function openForm() {
    const template = document.getElementById("person-modal-template");
    if (!template) return;
    const form = template.content.firstElementChild.cloneNode(true);
    const modal = App.modal({ title: App.t("people.add"), subtitle: App.t("people.noticeTitle"), content: form });
    const submit = form.querySelector("#person-submit");
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const consent = form.querySelector('input[name="consent"]');
      if (!consent || !consent.checked) {
        App.toast(App.t("people.consentRequired"), "warning");
        return;
      }
      let errorBox = form.querySelector(".form-error");
      if (errorBox) errorBox.remove();
      submit.disabled = true;
      try {
        await App.api("/api/people", { method: "POST", body: new FormData(form) });
        modal.close();
        App.toast(App.t("people.registered"), "success");
        await load();
      } catch (error) {
        errorBox = document.createElement("div");
        errorBox.className = "form-error";
        errorBox.textContent = error.message;
        form.prepend(errorBox);
        submit.disabled = false;
      }
    });
  }

  document.getElementById("add-person").addEventListener("click", openForm);
  if (search) search.addEventListener("input", render);
  document.addEventListener("app:language", render);
  load();
})();
