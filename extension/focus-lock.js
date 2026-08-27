const stateCopy = document.querySelector("#state-copy");
const sessionMeta = document.querySelector("#session-meta");
const questionArea = document.querySelector("#question-area");
const actions = document.querySelector("#actions");
const notice = document.querySelector("#notice");

let currentState = null;
let pageOrigin = "http://localhost:5173";
let question = null;
let breakEndsAt = null;

function message(payload) {
  return new Promise((resolve) => chrome.runtime.sendMessage(payload, resolve));
}

function clear(element) {
  while (element.firstChild) element.removeChild(element.firstChild);
}

function button(label, handler, primary = false) {
  const element = document.createElement("button");
  element.type = "button";
  element.textContent = label;
  element.className = primary ? "button primary" : "button";
  element.addEventListener("click", handler);
  return element;
}

function formatSeconds(seconds) {
  const mins = String(Math.floor(seconds / 60)).padStart(2, "0");
  const secs = String(seconds % 60).padStart(2, "0");
  return `${mins}:${secs}`;
}

function renderState(state) {
  currentState = state;
  clear(actions);
  clear(questionArea);
  notice.textContent = "";
  sessionMeta.hidden = !state;
  if (!state) {
    stateCopy.textContent = "Sign in to RISE and start a Focus session to activate the guard.";
    actions.append(button("Open RISE Focus", () => window.location.assign(`${pageOrigin}/focus`), true));
    return;
  }

  sessionMeta.textContent = `${state.focus_state} · ${formatSeconds(state.remaining_seconds || 0)} remaining`;
  if (state.focus_state === "PAUSED_BREAK" && state.break_unlock_expires_at) {
    breakEndsAt = Date.parse(state.break_unlock_expires_at);
    stateCopy.textContent = `Break authorized. Return to RISE when you are ready.`;
    renderBreakActions();
    return;
  }
  if (state.focus_state !== "ACTIVE") {
    stateCopy.textContent = "This Focus session is no longer blocking navigation.";
    actions.append(button("Open RISE Focus", () => window.location.assign(`${pageOrigin}/focus`), true));
    return;
  }
  stateCopy.textContent = "Navigation is held until RISE confirms a break or the session ends.";
  actions.append(button("Request Smart Break", requestQuestion, true));
  actions.append(button("Refresh state", refreshState));
}

function renderBreakActions() {
  clear(actions);
  const remaining = Math.max(0, Math.ceil((breakEndsAt - Date.now()) / 1000));
  stateCopy.textContent = `Break authorized for ${formatSeconds(remaining)}.`;
  actions.append(button("Return to RISE Focus", () => window.location.assign(`${pageOrigin}/focus`), true));
}

function renderQuestion() {
  clear(questionArea);
  questionArea.hidden = false;
  const heading = document.createElement("h2");
  heading.textContent = "Answer to unlock a break";
  questionArea.append(heading);
  const prompt = document.createElement("p");
  prompt.textContent = question.question;
  questionArea.append(prompt);
  const form = document.createElement("form");
  question.options.forEach((option, index) => {
    const label = document.createElement("label");
    label.className = "option";
    const input = document.createElement("input");
    input.type = "radio";
    input.name = "answer";
    input.value = option;
    input.required = index === 0;
    const text = document.createElement("span");
    text.textContent = option;
    label.append(input, text);
    form.append(label);
  });
  const submit = document.createElement("button");
  submit.type = "submit";
  submit.className = "button primary";
  submit.textContent = "Submit answer";
  form.append(submit);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    submit.disabled = true;
    const answer = form.elements.answer.value;
    const response = await message({ type: "RISE_SMART_BREAK_ANSWER", answer });
    if (response?.error) {
      notice.textContent = response.error;
      submit.disabled = false;
      return;
    }
    if (response.correct) {
      breakEndsAt = Date.now() + (response.break_seconds || 600) * 1000;
      question = null;
      questionArea.hidden = true;
      notice.textContent = "Correct. The server has authorized your break.";
      await refreshState();
    } else {
      question = null;
      notice.textContent = "Not quite. The session stays locked; request a fresh question.";
      await refreshState();
    }
  });
  questionArea.append(form);
}

async function requestQuestion() {
  notice.textContent = "Preparing a note-grounded question...";
  const response = await message({ type: "RISE_SMART_BREAK_QUESTION" });
  if (response?.error) {
    notice.textContent = response.error;
    return;
  }
  question = response.question;
  renderQuestion();
}

async function refreshState() {
  const response = await message({ type: "RISE_GET_STATE" });
  if (response?.error) {
    notice.textContent = response.error;
    return;
  }
  pageOrigin = response.pageOrigin || pageOrigin;
  renderState(response.state);
}

setInterval(() => {
  if (currentState?.focus_state === "PAUSED_BREAK" && breakEndsAt) {
    if (Date.now() >= breakEndsAt) refreshState();
    else renderBreakActions();
  }
}, 1000);

refreshState();