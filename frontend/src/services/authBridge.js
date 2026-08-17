import { authService } from './authService'

window.addEventListener('rise:auth-expired', () => window.location.assign('/login'))

document.addEventListener('click', event => {
  const button = event.target.closest('.auth-card .button-primary.full')
  if (!button || button.dataset.backendAuth === 'pending') return
  event.preventDefault()
  event.stopPropagation()
  button.dataset.backendAuth = 'pending'
  const fields = document.querySelectorAll('.auth-card input')
  const email = fields[0]?.value
  const password = fields[1]?.value
  authService.login({ email, password }).then(() => window.location.assign('/onboarding')).catch(() => { button.dataset.backendAuth = '' })
}, true)
