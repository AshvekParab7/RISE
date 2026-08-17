import { api, get, remove } from './api'

export const googleService = {
  getConnection: () => get('/integrations/google/'),
  connect: () => window.location.assign(`${api.url}/integrations/google/start/?redirect=1`),
  disconnect: () => remove('/integrations/google/'),
}
