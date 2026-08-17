import { get, post } from './api'

export const classroomService = {
  status: () => get('/integrations/google/classroom/'),
  sync: () => post('/integrations/google/classroom/sync/', {}),
}
