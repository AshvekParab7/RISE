import { get, post } from "../services/api";

const query = (params) => {
  const values = Object.entries(params || {}).filter(
    ([, value]) => value !== undefined && value !== null && value !== "",
  );
  return values.length ? `?${new URLSearchParams(values)}` : "";
};

export const adaptivePlannerService = {
  overview: (params) => get(`/adaptive-planner/overview/${query(params)}`),
  nextAction: () => get("/adaptive-planner/next-action/"),
  preview: (payload) => post("/adaptive-planner/plan/preview/", payload),
  commit: (blocks) => post("/adaptive-planner/plan/commit/", { blocks }),
  uploadExamSchedule: (formData) =>
    post("/adaptive-planner/exam-schedule-uploads/", formData),
  getExamUpload: (id) => get(`/adaptive-planner/exam-schedule-uploads/${id}/`),
  confirmExamSchedule: (id, rows) =>
    post(`/adaptive-planner/exam-schedule-uploads/${id}/confirm/`, { rows }),
};
