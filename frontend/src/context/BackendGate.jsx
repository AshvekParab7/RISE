import { useEffect, useState } from 'react'
import { loadBackendWorkspace } from '../services/backendBridge'

export function BackendGate({ children }) {
  const [ready, setReady] = useState(false)
  useEffect(() => { if (!localStorage.getItem('rise_access_token')) { setReady(true); return undefined } loadBackendWorkspace().catch(() => null).finally(() => setReady(true)); return undefined }, [])
  return ready ? children : <div className="backend-loading"><div className="loading-orb">R</div><p>Loading your RISE workspace...</p></div>
}
