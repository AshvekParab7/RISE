import { post } from './api'

export const aiService = {
  tutor: message => post('/ai/tutor/', message),
  planner: payload => post('/ai/planner/', payload),
  generateTest: payload => post('/ai/tests/generate/', payload),
}
