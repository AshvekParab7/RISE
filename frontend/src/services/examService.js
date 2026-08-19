import { get, post, patch, remove } from './api'
export const examService = { list: () => get('/exams/'), create: value => post('/exams/', value), update: (id, value) => patch(`/exams/${id}/`, value), remove: id => remove(`/exams/${id}/`) }
