import { get, post } from './api'
import { authorizeClassroomToken, requestClassroomAccessToken } from './googleClassroomGis'

export const classroomService = {
  status: async () => {
    const response = await get('/integrations/google/classroom/')
    return response
  },
  sync: async () => {
    try { return await post('/integrations/google/classroom/sync/', {}) } catch (error) {
      if (![400, 403].includes(error.status)) throw error
      const missingScopes = error.data?.missing_scopes || []
      const accessToken = await requestClassroomAccessToken(missingScopes.length ? missingScopes : undefined)
      await authorizeClassroomToken(accessToken)
      return post('/integrations/google/classroom/sync/', {})
    }
  },
}
