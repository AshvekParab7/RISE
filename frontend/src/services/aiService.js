import { post } from './api'

export const aiService = {
  tutor: message => post('/ai/tutor/', message),
  planner: message => post('/ai/planner/', message),
  generateTest: payload => post('/ai/tests/generate/', payload),
}
