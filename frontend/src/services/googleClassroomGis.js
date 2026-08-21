import { post } from './api'

const GIS_URL = 'https://accounts.google.com/gsi/client'
const CLASSROOM_SCOPES = [
  'https://www.googleapis.com/auth/classroom.courses.readonly',
  'https://www.googleapis.com/auth/classroom.courseworkmaterials.readonly',
  'https://www.googleapis.com/auth/drive.readonly',
]
let scriptPromise

function loadGis() {
  if (window.google?.accounts?.oauth2) return Promise.resolve()
  if (scriptPromise) return scriptPromise
  scriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = GIS_URL
    script.async = true
    script.onload = resolve
    script.onerror = () => reject(new Error('Google Classroom authorization could not be loaded.'))
    document.head.appendChild(script)
  })
  return scriptPromise
}

export async function requestClassroomAccessToken(scopes = CLASSROOM_SCOPES) {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
  if (!clientId) throw new Error('Google Classroom authorization is not configured.')
  await loadGis()
  return new Promise((resolve, reject) => {
    const client = window.google.accounts.oauth2.initTokenClient({
      client_id: clientId,
      scope: scopes.join(' '),
      include_granted_scopes: true,
      callback: response => response.error ? reject(new Error('Google Classroom authorization was denied.')) : resolve(response.access_token),
      error_callback: () => reject(new Error('Google Classroom authorization could not be completed.')),
    })
    client.requestAccessToken({ prompt: 'consent select_account', scope: scopes.join(' ') })
  })
}

export const authorizeClassroomToken = accessToken => post('/integrations/google/classroom/authorize/', { access_token: accessToken })
