import { get } from './api'

export const intelligenceService = {
  priorities: params => get(`/intelligence/priorities/${params ? `?${new URLSearchParams(params)}` : ''}`),
  nextAction: () => get('/intelligence/next-action/'),
  dailyPlan: availableMinutes => get(`/intelligence/daily-plan/?available_minutes=${availableMinutes || 90}`),
}
