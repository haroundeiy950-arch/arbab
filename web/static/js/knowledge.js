(() => {
  "use strict";

  const esc = (value) => App.escapeHtml(value);
  let docs = [];
  let current = null;
  let dirty = false;
  let searchResults = [];
  const list = document.getElementById("knowledge-docs");
  const editor = document.getElementById("knowledge-editor");
  const filename = document.getElementById("editor-filename");
  const statusChip = document.getElementById("editor-status");
  const pathNode = document.getElementById("editor-path");
  const titleNode = document.getElementById("editor-title");
  const charsNode = document.getElementById("editor-chars");
  const resultsNode = document.getElementById("k-results");
  const searchInput = document.getElementById("k-search");

  function formatBytes(number) {
    if (!number) return "0 B";
    const units = ["B", "KB", "MB"];
    const index = Math.min(units.length - 1, Math.floor(Math.log(number) / Math.log(1024)));
    return `${(number / Math.pow(1024, index)).toFixed(index ? 1 : 0)} ${units[index]}`;
  }

  function updateChars() {
    if (charsNode) charsNode.textContent = App.t("knowledge.chars", { count: editor.value.length });
  }

  function setDirty(value) {
    dirty = Boolean(value);
    if (!statusChip) return;
    statusChip.textContent = dirty ? App.t("knowledge.unsaved") : App.t("knowledge.saved");
    statusChip.classList.toggle("warn", dirty);
    statusChip.classList.toggle("ok", !dirty);
  }

  function setStats(stats) {
    document.getElementById("k-docs").textContent = docs.length;
    document.getElementById("k-chunks").textContent = (stats && stats.chunks) || 0;
  }

  function renderDocs() {
    if (!docs.length) {
      list.innerHTML = `<div class="empty-inline">${esc(App.t("knowledge.empty"))}</div>`;
      return;
    }
    list.innerHTML = docs.map((doc) => `
      <button type="button" class="doc-item ${current === doc.name ? "active" : ""}" data-doc="${esc(doc.name)}">
        <span class="doc-name">${esc(doc.name)}</span>
        <span class="doc-size">${esc(doc.editable ? formatBytes(doc.size) : "PDF")}</span>
      </button>`).join("");
    list.querySelectorAll(".doc-item").forEach((button) => {
      button.addEventListener("click", () => {
        const doc = docs.find((item) => item.name === button.dataset.doc);
        if (doc) selectDoc(doc);
      });
    });
  }

  async function selectDoc(doc) {
    current = doc.name;
    renderDocs();
    filename.value = doc.name;
    titleNode.textContent = doc.name;
    pathNode.textContent = doc.updated ? `${doc.name} · ${doc.updated}` : doc.name;
    if (!doc.editable) {
      editor.value = "";
      editor.disabled = true;
      pathNode.textContent = App.t("knowledge.pdfHint");
      setDirty(false);
      updateChars();
      return;
    }
    editor.disabled = false;
    pathNode.textContent = App.t("knowledge.selectDoc");
    try {
      const data = await App.api(`/api/knowledge/doc?name=${encodeURIComponent(doc.name)}`);
      editor.value = data.content || "";
      pathNode.textContent = doc.updated ? `${doc.name} · ${doc.updated}` : doc.name;
      setDirty(false);
      updateChars();
    } catch (error) {
      App.toast(error.message || App.t("knowledge.loadFailed"), "error");
    }
  }

  async function loadData(selectName = "") {
    try {
      const [data, settings] = await Promise.all([
        App.api("/api/knowledge"),
        App.api("/api/settings").catch(() => null)
      ]);
      docs = data.docs || [];
      setStats(data.stats || {});
      const provider = settings && settings.agent ? settings.agent : "local-rag";
      document.getElementById("k-provider").textContent = provider;
      renderDocs();
      if (!docs.length) {
        newDocument();
        return;
      }
      const target = docs.find((doc) => doc.name === selectName)
        || docs.find((doc) => doc.name === current)
        || docs.find((doc) => doc.editable)
        || docs[0];
      if (target) await selectDoc(target);
    } catch (error) {
      App.toast(error.message, "error");
    }
  }

  function newDocument() {
    current = null;
    editor.disabled = false;
    editor.value = "";
    filename.value = App.t("knowledge.newName");
    titleNode.textContent = App.t("knowledge.editor");
    pathNode.textContent = App.t("knowledge.newName");
    setDirty(true);
    updateChars();
    renderDocs();
    editor.focus();
  }

  async function saveDocument() {
    const button = document.getElementById("save-document");
    let name = filename.value.trim() || App.t("knowledge.newName");
    if (!/\.(md|txt|pdf)$/i.test(name)) name += ".md";
    button.disabled = true;
    try {
      await App.api("/api/knowledge/save", { method: "POST", body: { name, content: editor.value } });
      current = name;
      setDirty(false);
      App.toast(App.t("knowledge.savedToast"), "success");
      await loadData(name);
    } catch (error) {
      App.toast(error.message || App.t("knowledge.saveFailed"), "error");
    } finally {
      button.disabled = false;
    }
  }

  async function reindex() {
    const button = document.getElementById("reindex-knowledge");
    button.disabled = true;
    try {
      const result = await App.api("/api/knowledge/reindex", { method: "POST" });
      App.toast(App.t("knowledge.reindexed", { count: result.chunks || 0 }), "success");
      await loadData(current || "");
    } catch (error) {
      App.toast(error.message, "error");
    } finally {
      button.disabled = false;
    }
  }

  function renderResults() {
    if (!searchResults.length) {
      resultsNode.innerHTML = `<div class="empty-inline">${esc(App.t("knowledge.searchEmpty"))}</div>`;
      return;
    }
    resultsNode.innerHTML = searchResults.map((result) => `
      <div class="search-hit">
        <div class="search-hit-title">${esc(result.title)} · ${Math.round(Number(result.score || 0) * 100)}%</div>
        <div class="search-hit-text">${esc(result.text)}</div>
      </div>`).join("");
  }

  async function search() {
    const query = searchInput.value.trim();
    if (!query) return;
    const button = document.getElementById("k-search-btn");
    button.disabled = true;
    try {
      const data = await App.api(`/api/knowledge/search?q=${encodeURIComponent(query)}`);
      searchResults = data.results || [];
      renderResults();
    } catch (error) {
      App.toast(error.message, "error");
    } finally {
      button.disabled = false;
    }
  }

  editor.addEventListener("input", () => {
    setDirty(true);
    updateChars();
  });
  filename.addEventListener("input", () => setDirty(true));
  document.getElementById("save-document").addEventListener("click", saveDocument);
  document.getElementById("new-document").addEventListener("click", newDocument);
  document.getElementById("reindex-knowledge").addEventListener("click", reindex);
  document.getElementById("upload-knowledge").addEventListener("click", () => {
    document.getElementById("knowledge-upload").click();
  });
  document.getElementById("knowledge-upload").addEventListener("change", async (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    const button = document.getElementById("upload-knowledge");
    button.disabled = true;
    try {
      await App.api("/api/knowledge/upload", { method: "POST", body: formData });
      App.toast(App.t("knowledge.uploaded"), "success");
      await loadData(file.name);
    } catch (error) {
      App.toast(error.message, "error");
    } finally {
      button.disabled = false;
      event.target.value = "";
    }
  });
  document.getElementById("k-search-btn").addEventListener("click", search);
  searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      search();
    }
  });
  document.addEventListener("app:language", () => {
    renderDocs();
    setDirty(dirty);
    if (current) {
      const doc = docs.find((item) => item.name === current);
      if (doc && !doc.editable) pathNode.textContent = App.t("knowledge.pdfHint");
    }
    if (searchResults.length) renderResults();
  });

  loadData();
})();
