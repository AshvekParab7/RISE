import { get, patch, post, remove } from './api'

export const studySessionService = {
	list: () => get('/study-sessions/'),
	create: value => post('/study-sessions/', value),
	update: (id, value) => patch(`/study-sessions/${id}/`, value),
	remove: id => remove(`/study-sessions/${id}/`),
}
