const RULE_ID = 7301;
const TOKEN_KEY = "riseAccessToken";
const API_BASE_KEY = "riseApiBase";
const PAGE_ORIGIN_KEY = "risePageOrigin";
const STATE_KEY = "riseFocusState";
const POLL_ALARM = "rise-focus-poll";

const storageGet = (keys) => chrome.storage.session.get(keys);
const storageSet = (values) => chrome.storage.session.set(values);

function apiBaseForOrigin(origin) {
  return origin.includes("127.0.0.1")
    ? "http://127.0.0.1:8000/api"
    : "http://localhost:8000/api";
}

function isBreakAuthorized(session) {
  return session?.focus_state === "PAUSED_BREAK"
    && session.break_unlock_expires_at
    && Date.parse(session.break_unlock_expires_at) > Date.now();
}

function shouldBlock(session) {
  if (!session) return false;
  if (session.focus_state === "ACTIVE") return true;
  return session.focus_state === "PAUSED_BREAK" && !isBreakAuthorized(session);
}

async function updateNavigationRule(blocked) {
  await chrome.declarativeNetRequest.updateDynamicRules({
    removeRuleIds: [RULE_ID],
    addRules: blocked ? [{
      id: RULE_ID,
      priority: 1,
      action: {
        type: "redirect",
        redirect: { extensionPath: "/focus-lock.html" },
      },
      condition: {
        regexFilter: "^https?://",
        excludedRequestDomains: ["localhost", "127.0.0.1"],
        resourceTypes: ["main_frame"],
      },
    }] : [],
  });
}

async function clearGuard() {
  await updateNavigationRule(false).catch(() => undefined);
}

async function pollFocusState() {
  const stored = await storageGet([TOKEN_KEY, API_BASE_KEY, STATE_KEY]);
  if (!stored[TOKEN_KEY] || !stored[API_BASE_KEY]) {
    await clearGuard();
    return null;
  }

  try {
    const response = await fetch(`${stored[API_BASE_KEY]}/study-sessions/focus/current/`, {
      headers: { Authorization: `Bearer ${stored[TOKEN_KEY]}` },
    });
    if (response.status === 401) {
      await chrome.storage.session.clear();
      await clearGuard();
      return null;
    }
    if (!response.ok) throw new Error(`Focus state request failed: ${response.status}`);
    const session = await response.json();
    await storageSet({ [STATE_KEY]: session });
    await updateNavigationRule(shouldBlock(session));
    return session;
  } catch {
    const previous = stored[STATE_KEY] || null;
    if (previous) await updateNavigationRule(shouldBlock(previous)).catch(() => undefined);
    return previous;
  }
}

async function requestSmartBreakQuestion() {
  const stored = await storageGet([TOKEN_KEY, API_BASE_KEY, STATE_KEY]);
  const session = await pollFocusState() || stored[STATE_KEY];
  if (!session || session.focus_state !== "ACTIVE") {
    return { error: "Focus is not currently active." };
  }
  const response = await fetch(`${stored[API_BASE_KEY]}/study-sessions/${session.id}/focus/smart-break/question/`, {
    method: "POST",
    headers: { Authorization: `Bearer ${stored[TOKEN_KEY]}` },
  });
  const data = await response.json().catch(() => ({}));
  return response.ok ? data : { error: data.detail || "RISE could not prepare a break question." };
}

async function submitSmartBreakAnswer(answer) {
  const stored = await storageGet([TOKEN_KEY, API_BASE_KEY, STATE_KEY]);
  const session = stored[STATE_KEY];
  if (!session) return { error: "Focus state is unavailable." };
  const response = await fetch(`${stored[API_BASE_KEY]}/study-sessions/${session.id}/focus/smart-break/answer/`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${stored[TOKEN_KEY]}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ answer }),
  });
  const data = await response.json().catch(() => ({}));
  if (response.ok) await pollFocusState();
  return response.ok ? data : { error: data.detail || "RISE could not grade that answer." };
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "RISE_TOKEN") {
    const origin = message.origin || "http://localhost:5173";
    Promise.resolve()
      .then(() => storageSet({
        [TOKEN_KEY]: message.token,
        [API_BASE_KEY]: apiBaseForOrigin(origin),
        [PAGE_ORIGIN_KEY]: origin,
      }))
      .then(pollFocusState)
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ error: error.message }));
    return true;
  }
  if (message?.type === "RISE_REFRESH_STATE") {
    pollFocusState()
      .then((state) => sendResponse({ state }))
      .catch((error) => sendResponse({ error: error.message }));
    return true;
  }
  if (message?.type === "RISE_GET_STATE") {
    Promise.all([pollFocusState(), storageGet([PAGE_ORIGIN_KEY])])
      .then(([state, stored]) => sendResponse({ state, pageOrigin: stored[PAGE_ORIGIN_KEY] }))
      .catch((error) => sendResponse({ error: error.message }));
    return true;
  }
  if (message?.type === "RISE_SMART_BREAK_QUESTION") {
    requestSmartBreakQuestion().then(sendResponse).catch((error) => sendResponse({ error: error.message }));
    return true;
  }
  if (message?.type === "RISE_SMART_BREAK_ANSWER") {
    submitSmartBreakAnswer(message.answer).then(sendResponse).catch((error) => sendResponse({ error: error.message }));
    return true;
  }
  return false;
});

async function startPolling() {
  await chrome.alarms.create(POLL_ALARM, { periodInMinutes: 0.25 });
  await pollFocusState();
}

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === POLL_ALARM) pollFocusState();
});

chrome.runtime.onInstalled.addListener(startPolling);
chrome.runtime.onStartup.addListener(startPolling);
startPolling();