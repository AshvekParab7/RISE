import { get, remove } from './api'

export const googleService = {
  getConnection: () => get('/integrations/google/'),
  connect: async () => { const response = await get('/integrations/google/start/'); window.location.assign(response.authorization_url); return response },
  disconnect: () => remove('/integrations/google/'),
}
