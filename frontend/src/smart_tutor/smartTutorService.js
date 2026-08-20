import { post } from '../services/api'

export const smartTutorService = {
  ask: message => post('/smart-tutor/tutor/', message),
  generateFlashcards: ({ topic, count, file }) => {
    const payload = new FormData()
    payload.append('topic', topic)
    payload.append('count', String(count))
    payload.append('file', file)
    return post('/smart-tutor/flashcards/', payload)
  },
  generateMCQs: ({ topic, count, file }) => {
    const payload = new FormData()
    payload.append('topic', topic)
    payload.append('count', String(count))
    payload.append('file', file)
    return post('/smart-tutor/mcqs/', payload)
  },
}
