import { post } from './api'

export const aiService = {
  planner: payload => post('/ai/planner/', payload),
  generateTest: payload => post('/ai/tests/generate/', payload),
}
