import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from 'firebase/auth'
import { initializeApp } from 'firebase/app'
import { authService } from './authService'

const config = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
}

const configured = Object.values(config).every(Boolean)
const firebaseApp = configured ? initializeApp(config) : null
const firebaseAuth = firebaseApp ? getAuth(firebaseApp) : null
const googleProvider = configured ? new GoogleAuthProvider() : null

export const firebaseAuthService = {
  login: async () => {
    if (!firebaseAuth || !googleProvider) throw new Error('Google Sign-In is not configured.')
    let result
    try {
      result = await signInWithPopup(firebaseAuth, googleProvider)
    } catch (error) {
      if (error?.code === 'auth/operation-not-allowed') throw new Error('Google Sign-In is disabled in Firebase Authentication. Enable the Google provider in Firebase Console.')
      throw new Error('Google Sign-In could not be completed.')
    }
    const idToken = await result.user.getIdToken()
    const session = await authService.firebaseLogin(idToken)
    if (result.user.photoURL) localStorage.setItem('rise_profile_photo', result.user.photoURL)
    return session
  },
  logout: async () => { if (firebaseAuth) await signOut(firebaseAuth); localStorage.removeItem('rise_profile_photo') },
}
