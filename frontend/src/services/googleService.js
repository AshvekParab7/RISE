import { get, remove } from './api'

export const googleService = {
  getConnection: () => get('/integrations/google/'),
  connect: async integration => { const response = await get(`/integrations/google/start/${integration ? `?integration=${integration}` : ''}`); window.location.assign(response.authorization_url) },
  disconnect: () => remove('/integrations/google/'),
}
