import { get, post, remove } from './api'

export const resourceService = { list: () => get('/resources/'), upload: formData => post('/resources/', formData), remove: id => remove(`/resources/${id}/`) }
