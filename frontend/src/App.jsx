import { BrowserRouter } from 'react-router-dom'
import ProductApp from './RISEProduct'
import TestRunner from './TestRunner'
import { AuthProvider } from './context/AuthContext'
import { BackendGate } from './context/BackendGate'

export default function AppEntry() {
	const oauth = new URLSearchParams(window.location.hash.slice(1))
	if (oauth.get('rise_access') && oauth.get('rise_refresh')) {
		localStorage.setItem('rise_access_token', oauth.get('rise_access'))
		localStorage.setItem('rise_refresh_token', oauth.get('rise_refresh'))
		localStorage.removeItem('rise_guest_mode')
		window.history.replaceState({}, '', window.location.pathname)
	}
	const app = window.location.pathname.startsWith('/tests/') ? <BrowserRouter><TestRunner /></BrowserRouter> : <ProductApp />
	return <AuthProvider><BackendGate>{app}</BackendGate></AuthProvider>
}
