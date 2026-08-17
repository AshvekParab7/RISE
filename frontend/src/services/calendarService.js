import { get, post } from './api'
export const calendarService = { status: () => get('/integrations/google/calendar/'), list: () => get('/integrations/google/calendar/calendars/'), select: calendarIds => post('/integrations/google/calendar/calendars/', { calendar_ids: calendarIds }), sync: calendarIds => post('/integrations/google/calendar/sync/', { calendar_ids: calendarIds }) }
