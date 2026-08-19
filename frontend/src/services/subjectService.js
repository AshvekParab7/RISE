import { get, patch, post, remove } from './api'

export const subjectService = { list: () => get('/subjects/'), create: subject => post('/subjects/', subject), update: (id, subject) => patch(`/subjects/${id}/`, subject), remove: id => remove(`/subjects/${id}/`) }
