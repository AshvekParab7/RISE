import { get, post, patch, remove } from './api'
export const semesterService = { list: () => get('/semesters/'), create: value => post('/semesters/', value), update: (id, value) => patch(`/semesters/${id}/`, value), remove: id => remove(`/semesters/${id}/`) }
