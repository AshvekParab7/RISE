import { authService } from './authService'
import { googleService } from './googleService'

window.addEventListener('rise:auth-expired', () => window.location.assign('/login'))

document.addEventListener('click', event => {
  const googleButton = event.target.closest('.auth-card .google-button')
  if (googleButton) {
    event.preventDefault()
    event.stopPropagation()
    googleService.connect().catch(() => { googleButton.dataset.backendAuth = '' })
    return
  }
  const button = event.target.closest('.auth-card .full')
  if (!button || button.dataset.backendAuth === 'pending') return
  event.preventDefault()
  event.stopPropagation()
  button.dataset.backendAuth = 'pending'
  const fields = document.querySelectorAll('.auth-card input')
  const email = fields[0]?.value
  const password = fields[1]?.value
  authService.login({ email, password }).then(() => window.location.assign('/onboarding')).catch(() => { button.dataset.backendAuth = '' })
}, true)
