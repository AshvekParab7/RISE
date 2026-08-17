import { useEffect, useState } from 'react'
import { authService } from '../services/authService'
import { AuthContext } from './auth'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const refreshUser = async () => { try { const current = await authService.currentUser(); setUser(current); return current } catch { setUser(null); return null } }
  useEffect(() => { const restore = async () => { if (localStorage.getItem('rise_access_token')) await refreshUser(); setIsLoading(false) }; restore(); const expire = () => setUser(null); window.addEventListener('rise:auth-expired', expire); return () => window.removeEventListener('rise:auth-expired', expire) }, [])
  const login = async credentials => { setError(null); try { const session = await authService.login(credentials); setUser(session.user); return session } catch (reason) { setError(reason.message); throw reason } }
  const logout = async () => { try { await authService.logout() } finally { setUser(null) } }
  return <AuthContext.Provider value={{ user, isAuthenticated: Boolean(user), isLoading, error, login, logout, refreshUser }}>{children}</AuthContext.Provider>
}
