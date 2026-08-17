import { get, post, patch, remove } from './api'
export const timetableService = { list: () => get('/college-timetable/'), create: value => post('/college-timetable/', value), update: (id, value) => patch(`/college-timetable/${id}/`, value), remove: id => remove(`/college-timetable/${id}/`) }
