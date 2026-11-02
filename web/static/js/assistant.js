(() => {
  "use strict";

  const esc = (value) => App.escapeHtml(value);
  const log = document.getElementById("chat-log");
  const form = document.getElementById("ask-form");
  const input = document.getElementById("ask-input");
  const submit = document.getElementById("ask-submit");
  const speakAnswers = document.getElementById("speak-answers");
  const capture = document.getElementById("capture-question");
  const providerChip = document.getElementById("provider-chip");
  let busy = false;
  let welcome = log.querySelector(".chat-welcome");

  function scrollDown() {
    log.scrollTop = log.scrollHeight;
  }

  function removeWelcome() {
    if (welcome) {
      welcome.remove();
      welcome = null;
    }
  }

  function appendMessage(role, text, options = {}) {
    const message = document.createElement("div");
    message.className = `chat-message ${role}`;
    const avatar = document.createElement("div");
    avatar.className = "msg-avatar";
    avatar.textContent = role === "user" ? App.t("assistant.you") : App.t("assistant.agent");
    const wrapper = document.createElement("div");
    const bubble = document.createElement("div");
    bubble.className = "msg-bubble";
    bubble.textContent = text;
    wrapper.appendChild(bubble);

    const meta = document.createElement("div");
    meta.className = "msg-meta";
    const time = document.createElement("span");
    time.textContent = App.formatTime(new Date().toISOString(), false);
    meta.appendChild(time);
    if (options.provider) {
      const provider = document.createElement("span");
      provider.textContent = options.provider;
      meta.appendChild(provider);
    }
    wrapper.appendChild(meta);

    if (options.sources && options.sources.length) {
      const sources = document.createElement("div");
      sources.className = "msg-sources";
      options.sources.forEach((source) => {
        const chip = document.createElement("span");
        chip.className = "msg-source";
        chip.textContent = source.title || source.source || String(source);
        sources.appendChild(chip);
      });
      wrapper.appendChild(sources);
    }

    if (options.snapshotUrl) {
      const link = document.createElement("a");
      link.href = options.snapshotUrl;
      link.target = "_blank";
      link.rel = "noopener";
      const image = document.createElement("img");
      image.className = "msg-thumb";
      image.src = options.snapshotUrl;
      image.alt = App.t("assistant.snapshot");
      link.appendChild(image);
      wrapper.appendChild(link);
    }

    message.appendChild(avatar);
    message.appendChild(wrapper);
    log.appendChild(message);
    scrollDown();
    return message;
  }

  function appendTyping() {
    removeWelcome();
    const node = document.createElement("div");
    node.className = "chat-message assistant";
    node.id = "typing-message";
    node.innerHTML = `<div class="msg-avatar">${esc(App.t("assistant.agent"))}</div><div class="msg-bubble typing"><span></span><span></span><span></span></div>`;
    node.title = App.t("assistant.thinking");
    log.appendChild(node);
    scrollDown();
    return node;
  }

  async function ask(question) {
    const value = String(question || "").trim();
    if (!value || busy) return;
    busy = true;
    removeWelcome();
    appendMessage("user", value);
    input.value = "";
    submit.disabled = true;
    const typing = appendTyping();
    try {
      const response = await App.api("/api/ask", {
        method: "POST",
        body: {
          question: value,
          language: App.lang,
          capture: capture ? capture.checked : true
        }
      });
      typing.remove();
      appendMessage("assistant", response.answer || "", {
        provider: response.provider,
        sources: response.sources || [],
        snapshotUrl: response.snapshot_url ? App.safeUrl(response.snapshot_url) : ""
      });
      if (speakAnswers && speakAnswers.checked) {
        App.speak(response.answer || "", App.lang, true);
      }
    } catch (error) {
      typing.remove();
      App.toast(error.message || App.t("assistant.answerError"), "error");
    } finally {
      busy = false;
      submit.disabled = false;
      input.focus();
    }
  }

  function setRisk(level, answer) {
    const orb = document.getElementById("risk-orb");
    const label = document.getElementById("risk-level");
    const body = document.getElementById("assess-body");
    const normalized = ["low", "medium", "high"].includes(String(level)) ? String(level) : "low";
    orb.className = `risk-orb ${normalized}`;
    label.textContent = App.t(`risk.${normalized}`) === `risk.${normalized}` ? normalized.toUpperCase() : App.t(`risk.${normalized}`);
    body.textContent = answer || "";
    scrollDown();
  }

  async function assess() {
    const button = document.getElementById("assess-btn");
    button.disabled = true;
    const body = document.getElementById("assess-body");
    const previous = body.textContent;
    body.textContent = App.t("common.loading");
    try {
      const result = await App.api("/api/assess", { method: "POST", body: { language: App.lang } });
      setRisk(result.risk_level, result.answer || result.summary || "");
      App.toast(App.t("assistant.assessDone"), "success");
    } catch (error) {
      body.textContent = previous;
      App.toast(error.message || App.t("assistant.assessError"), "error");
    } finally {
      button.disabled = false;
    }
  }

  async function loadProvider() {
    try {
      const data = await App.api("/api/settings");
      if (providerChip && data.agent) providerChip.textContent = data.agent;
    } catch (error) {}
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    ask(input.value);
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      ask(input.value);
    }
  });
  document.querySelectorAll("#quick-prompts [data-q]").forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.dataset.q || "";
      ask(input.value);
    });
  });
  document.getElementById("assess-btn").addEventListener("click", assess);
  document.addEventListener("app:language", () => {
    const label = document.getElementById("risk-level");
    const orb = document.getElementById("risk-orb");
    const level = ["low", "medium", "high"].find((name) => orb.classList.contains(name));
    if (level && label) label.textContent = App.t(`risk.${level}`);
  });

  loadProvider();
})();
