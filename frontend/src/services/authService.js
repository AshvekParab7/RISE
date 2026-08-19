import { get, post } from './api'

export const authService = {
  register: credentials => post('/auth/register/', credentials),
  login: async credentials => { const session = await post('/auth/login/', credentials); localStorage.setItem('rise_access_token', session.access); localStorage.setItem('rise_refresh_token', session.refresh); localStorage.setItem('rise_user', JSON.stringify(session.user)); return session },
  firebaseLogin: async idToken => { const session = await post('/auth/firebase/', { id_token: idToken }); localStorage.setItem('rise_access_token', session.access); localStorage.setItem('rise_refresh_token', session.refresh); localStorage.setItem('rise_user', JSON.stringify(session.user)); return session },
  logout: async () => { const refresh = localStorage.getItem('rise_refresh_token'); const result = await post('/auth/logout/', { refresh }); localStorage.removeItem('rise_access_token'); localStorage.removeItem('rise_refresh_token'); localStorage.removeItem('rise_user'); localStorage.removeItem('rise_profile_photo'); return result },
  currentUser: () => get('/auth/me/'),
}
