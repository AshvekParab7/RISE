import { get, post, patch, remove } from './api'
export const topicService = { list: () => get('/topics/'), create: value => post('/topics/', value), update: (id, value) => patch(`/topics/${id}/`, value), remove: id => remove(`/topics/${id}/`) }
