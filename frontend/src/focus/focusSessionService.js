import { get, post } from "../services/api";

export const focusSessionService = {
  current: () => get("/study-sessions/focus/current/"),
  start: (value) => post("/study-sessions/focus/start/", value),
  state: (id, action, endReason) => post(`/study-sessions/${id}/focus/state/`, {
    action,
    ...(endReason ? { end_reason: endReason } : {}),
  }),
  complete: (id, metadata) => post(`/study-sessions/${id}/focus/complete/`, metadata),
  studyGuide: (id) => post(`/study-sessions/${id}/focus/study-guide/`, {}),
  smartBreakQuestion: (id) => post(`/study-sessions/${id}/focus/smart-break/question/`, {}),
  smartBreakAnswer: (id, answer) => post(`/study-sessions/${id}/focus/smart-break/answer/`, { answer }),
};