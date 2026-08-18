import { post } from './api'

export const aiService = {
  tutor: message => post('/ai/tutor/', message),
  generateTest: payload => post('/ai/tests/generate/', payload),
}
