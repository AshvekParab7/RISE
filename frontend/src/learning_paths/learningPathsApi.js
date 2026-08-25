import { get, post, remove } from '../services/api'

export const learningPathsApi = {
  create: (url, retry = false) => post('/learning/youtube/', { url, retry }),
  searchYouTube: query => get(`/learning/youtube/search/?q=${encodeURIComponent(query)}`),
  list: () => get('/learning/'),
  detail: id => get(`/learning/${id}/`),
  remove: id => remove(`/learning/${id}/`),
  status: id => get(`/learning/${id}/status/`),
  startLevel: (pathId, levelId) => post(`/learning/${pathId}/levels/${levelId}/start/`, {}),
  checkpoint: (pathId, levelId, answer) => post(`/learning/${pathId}/checkpoint/`, { level_id: levelId, answer }),
  finalChallenge: id => get(`/learning/${id}/final-challenge/`),
  submitFinalChallenge: (id, answers) => post(`/learning/${id}/final-challenge/`, { answers }),
  notes: id => get(`/learning/${id}/notes/`),
  resume: id => post(`/learning/${id}/resume/`, {}),
}
