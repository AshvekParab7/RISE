import { get, post } from "./api";

export const aiService = {
  tutor: (message) => post("/ai/tutor/", message),
  planner: (message) => post("/ai/planner/", message),
  listPlannerConversations: () => get("/ai/planner/conversations/"),
  getPlannerConversation: (id) => get(`/ai/planner/conversations/${id}/`),
  appendPlannerMessage: (id, message) =>
    post(`/ai/planner/conversations/${id}/messages/`, message),
  generateTest: (payload) => post("/ai/tests/generate/", payload),
};
