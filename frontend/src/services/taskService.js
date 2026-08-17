import { get, patch, post, remove } from './api'

export const taskService = { list: () => get('/tasks/'), create: task => post('/tasks/', task), update: (id, task) => patch(`/tasks/${id}/`, task), complete: id => patch(`/tasks/${id}/`, { status: 'COMPLETED' }), remove: id => remove(`/tasks/${id}/`) }
