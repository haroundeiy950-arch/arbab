(() => {
  "use strict";

  const esc = (value) => App.escapeHtml(value);
  let models = {};
  let agentProvider = "local-rag";

  function fields() {
    return Array.from(document.querySelectorAll("[data-setting]"));
  }

  function fill(settings) {
    fields().forEach((field) => {
      const key = field.dataset.setting;
      const value = settings[key];
      if (field.type === "checkbox") {
        field.checked = String(value) === "1" || value === true;
      } else if (value !== undefined && value !== null) {
        field.value = value;
      }
    });
  }

  function renderModels() {
    const root = document.getElementById("model-status");
    if (!root) return;
    const entries = [
      ["objects", "settings.modelObjects"],
      ["pose", "settings.modelPose"],
      ["faces", "settings.modelFaces"],
      ["plates", "settings.modelPlates"],
      ["custom_threat_model", "settings.modelThreats"]
    ];
    root.innerHTML = entries.map(([key, label]) => `
      <div class="model-row">
        <span>${esc(App.t(label))}</span>
        <strong class="${models[key] ? "ok" : "bad"}">${esc(models[key] ? App.t("settings.operational") : App.t("settings.missing"))}</strong>
      </div>`).join("");
  }

  async function load(notify = false) {
    const button = document.getElementById("reload-settings");
    button.disabled = true;
    try {
      const data = await App.api("/api/settings");
      fill(data.settings || {});
      models = data.models || {};
      agentProvider = data.agent || "local-rag";
      const provider = document.getElementById("provider-readonly");
      if (provider) provider.value = agentProvider;
      renderModels();
      if (notify) App.toast(App.t("settings.reloaded"), "success");
    } catch (error) {
      App.toast(error.message, "error");
    } finally {
      button.disabled = false;
    }
  }

  function payload() {
    const data = {};
    fields().forEach((field) => {
      data[field.dataset.setting] = field.type === "checkbox" ? field.checked : field.value;
    });
    return data;
  }

  async function save() {
    const button = document.getElementById("save-settings");
    button.disabled = true;
    try {
      const data = await App.api("/api/settings", { method: "PUT", body: payload() });
      App.toast(App.t("settings.saved"), "success");
      if (data.updated && Object.prototype.hasOwnProperty.call(data.updated, "camera_source")) {
        window.setTimeout(() => load(false), 1200);
      }
    } catch (error) {
      App.toast(error.message || App.t("settings.saveFailed"), "error");
    } finally {
      button.disabled = false;
    }
  }

  async function changePassword(event) {
    event.preventDefault();
    const form = document.getElementById("password-form");
    const current = document.getElementById("current-password");
    const next = document.getElementById("new-password");
    const confirm = document.getElementById("confirm-password");
    if (next.value.length < 10) {
      App.toast(App.t("settings.passwordShort"), "warning");
      return;
    }
    if (next.value !== confirm.value) {
      App.toast(App.t("settings.passwordMismatch"), "warning");
      return;
    }
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      await App.api("/api/settings/password", {
        method: "POST",
        body: { current: current.value, new: next.value }
      });
      form.reset();
      App.toast(App.t("settings.passwordChanged"), "success");
    } catch (error) {
      App.toast(error.message, "error");
    } finally {
      button.disabled = false;
    }
  }

  async function cleanup() {
    const button = document.getElementById("cleanup-events");
    button.disabled = true;
    try {
      const result = await App.api("/api/maintenance/cleanup", { method: "POST" });
      App.toast(App.t("settings.cleanupDone", { count: result.removed || 0 }), "success");
    } catch (error) {
      App.toast(error.message || App.t("settings.cleanupFailed"), "error");
    } finally {
      button.disabled = false;
    }
  }

  document.getElementById("save-settings").addEventListener("click", save);
  document.getElementById("reload-settings").addEventListener("click", () => load(true));
  document.getElementById("password-form").addEventListener("submit", changePassword);
  document.getElementById("cleanup-events").addEventListener("click", cleanup);
  document.addEventListener("app:language", () => {
    renderModels();
    const provider = document.getElementById("provider-readonly");
    if (provider) provider.value = agentProvider;
  });

  load();
})();
