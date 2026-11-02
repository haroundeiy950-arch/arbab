(() => {
  "use strict";

  const esc = (value) => App.escapeHtml(value);
  let vehicles = [];
  let lastScan = null;
  let loading = false;
  const tbody = document.getElementById("vehicles-body");
  const countNode = document.getElementById("vehicles-count");
  const scanCard = document.getElementById("scan-result");

  function render() {
    if (countNode) countNode.textContent = App.t("vehicles.count", { count: vehicles.length });
    if (!vehicles.length) {
      tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state">${esc(App.t("vehicles.empty"))}</div></td></tr>`;
      return;
    }
    tbody.innerHTML = vehicles.map((vehicle) => `
      <tr data-vehicle-id="${vehicle.id}">
        <td class="plate-cell">${esc(vehicle.plate)}</td>
        <td>${esc(vehicle.make || "—")}</td>
        <td>${esc(vehicle.model || "—")}</td>
        <td>${esc(vehicle.color || "—")}</td>
        <td>${esc(vehicle.owner || "—")}</td>
        <td>${esc(vehicle.notes || "—")}</td>
        <td>
          <div class="head-right">
            <button type="button" class="btn small btn-ghost vehicle-edit">${esc(App.t("common.edit"))}</button>
            <button type="button" class="btn small btn-ghost vehicle-delete">${esc(App.t("common.delete"))}</button>
          </div>
        </td>
      </tr>`).join("");
    tbody.querySelectorAll(".vehicle-edit").forEach((button) => {
      button.addEventListener("click", () => {
        const row = button.closest("[data-vehicle-id]");
        const vehicle = vehicles.find((item) => String(item.id) === String(row.dataset.vehicleId));
        if (vehicle) openForm(vehicle);
      });
    });
    tbody.querySelectorAll(".vehicle-delete").forEach((button) => {
      button.addEventListener("click", () => {
        const row = button.closest("[data-vehicle-id]");
        const vehicle = vehicles.find((item) => String(item.id) === String(row.dataset.vehicleId));
        if (!vehicle) return;
        if (!window.confirm(App.t("vehicles.deleteConfirm", { plate: vehicle.plate }))) return;
        button.disabled = true;
        App.api(`/api/vehicles/${vehicle.id}`, { method: "DELETE" })
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
      const data = await App.api("/api/vehicles");
      vehicles = data.vehicles || [];
      render();
    } catch (error) {
      App.toast(error.message, "error");
      tbody.innerHTML = `<tr><td colspan="7"><div class="empty-state">${esc(App.t("common.error"))}</div></td></tr>`;
    } finally {
      loading = false;
    }
  }

  function openForm(vehicle) {
    const template = document.getElementById("vehicle-modal-template");
    if (!template) return;
    const form = template.content.firstElementChild.cloneNode(true);
    form.querySelector('[name="plate"]').value = vehicle ? vehicle.plate : "";
    form.querySelector('[name="make"]').value = vehicle ? vehicle.make : "";
    form.querySelector('[name="model"]').value = vehicle ? vehicle.model : "";
    form.querySelector('[name="color"]').value = vehicle ? vehicle.color : "";
    form.querySelector('[name="owner"]').value = vehicle ? vehicle.owner : "";
    form.querySelector('[name="notes"]').value = vehicle ? vehicle.notes : "";
    const modal = App.modal({
      title: vehicle ? App.t("vehicles.editTitle") : App.t("vehicles.addTitle"),
      subtitle: App.t("vehicles.limitTitle"),
      content: form
    });
    const submit = form.querySelector('button[type="submit"]');
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const errorBox = form.querySelector(".form-error");
      if (errorBox) errorBox.remove();
      submit.disabled = true;
      try {
        await App.api("/api/vehicles", {
          method: "POST",
          body: Object.fromEntries(new FormData(form).entries())
        });
        modal.close();
        App.toast(App.t("vehicles.saved"), "success");
        await load();
      } catch (error) {
        const box = document.createElement("div");
        box.className = "form-error";
        box.textContent = error.message;
        form.prepend(box);
        submit.disabled = false;
      }
    });
  }

  function showScan(result) {
    lastScan = result;
    if (!result || !result.plate) {
      if (scanCard) scanCard.hidden = true;
      App.toast((result && result.message) || App.t("vehicles.scanNone"), "warning");
      return;
    }
    document.getElementById("scan-plate-value").textContent = result.plate;
    document.getElementById("scan-make").textContent = result.make || "—";
    document.getElementById("scan-model").textContent = result.model || "—";
    document.getElementById("scan-owner").textContent = result.owner || "—";
    document.getElementById("scan-confidence").textContent = result.confidence !== undefined
      ? `${Math.round(Number(result.confidence) * 100)}%`
      : "—";
    const badge = document.getElementById("scan-registered");
    badge.textContent = result.registered ? App.t("vehicles.registered") : App.t("vehicles.notRegistered");
    badge.className = `badge ${result.registered ? "success" : "warning"}`;
    const link = document.getElementById("scan-evidence");
    const url = result.event && result.event.snapshot_url ? App.safeUrl(result.event.snapshot_url) : "";
    link.hidden = !url;
    if (url) link.href = url;
    scanCard.hidden = false;
    App.toast(App.t("vehicles.scanDone", { plate: result.plate }), "success");
  }

  async function scan(button) {
    button.disabled = true;
    try {
      const result = await App.api("/api/scan/plate", { method: "POST" });
      showScan(result);
    } catch (error) {
      App.toast(error.message || App.t("vehicles.scanFailed"), "error");
    } finally {
      button.disabled = false;
    }
  }

  document.getElementById("add-vehicle").addEventListener("click", () => openForm(null));
  document.getElementById("scan-plate").addEventListener("click", (event) => scan(event.currentTarget));
  document.getElementById("scan-close").addEventListener("click", () => {
    scanCard.hidden = true;
    lastScan = null;
  });
  document.addEventListener("app:language", () => {
    render();
    if (lastScan && !scanCard.hidden) {
      const badge = document.getElementById("scan-registered");
      badge.textContent = lastScan.registered ? App.t("vehicles.registered") : App.t("vehicles.notRegistered");
    }
  });
  load();
})();
