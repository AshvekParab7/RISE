import { get, post } from '../../services/api'

export const studyCoachApi = {
  listSessions: () => get('/ashvek/study-coach/sessions/'),
  getSession: id => get(`/ashvek/study-coach/sessions/${id}/`),
  createSession: payload => post('/ashvek/study-coach/sessions/', payload),
  teach: payload => post('/ashvek/study-coach/teach/', payload),
  answer: payload => post('/ashvek/study-coach/answer/', payload),
  practice: payload => post('/ashvek/study-coach/practice/', payload),
  revision: payload => post('/ashvek/study-coach/revision/', payload),
  complete: id => post(`/ashvek/study-coach/sessions/${id}/complete/`, {}),
  report: id => get(`/ashvek/study-coach/session/${id}/report/`),
}
