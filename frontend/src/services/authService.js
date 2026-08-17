import { get, post } from './api'

export const authService = {
  register: credentials => post('/auth/register/', credentials),
  login: async credentials => { const session = await post('/auth/login/', credentials); localStorage.setItem('rise_access_token', session.access); localStorage.setItem('rise_refresh_token', session.refresh); return session },
  logout: async () => { const refresh = localStorage.getItem('rise_refresh_token'); const result = await post('/auth/logout/', { refresh }); localStorage.removeItem('rise_access_token'); localStorage.removeItem('rise_refresh_token'); return result },
  currentUser: () => get('/auth/me/'),
}
