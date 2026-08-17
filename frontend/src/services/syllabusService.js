import { get, post, patch, remove } from './api'
export const syllabusService = { list: () => get('/syllabus/'), upload: formData => post('/syllabus/', formData), update: (id, value) => patch(`/syllabus/${id}/`, value), remove: id => remove(`/syllabus/${id}/`) }
