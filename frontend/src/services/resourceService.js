import { api, get, post, remove } from './api'

const preview = async id => {
	const token = localStorage.getItem('rise_access_token')
	const response = await fetch(`${api.url}/resources/${id}/preview/`, {
		headers: token ? { Authorization: `Bearer ${token}` } : {},
	})
	if (!response.ok) throw new Error('This resource could not be fetched.')
	return response.blob()
}

export const resourceService = { list: () => get('/resources/'), upload: formData => post('/resources/', formData), remove: id => remove(`/resources/${id}/`), preview }
