import { get, patch, post, remove } from './api'

export const plannerService = {
  list: day => get(`/planner-events/${day ? `?day=${encodeURIComponent(day)}` : ''}`),
  create: payload => post('/planner-events/', payload),
  update: (id, payload) => patch(`/planner-events/${id}/`, payload),
  remove: id => remove(`/planner-events/${id}/`),
}
