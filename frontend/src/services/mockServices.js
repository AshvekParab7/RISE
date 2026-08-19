import { mockTasks, mockSubjects } from '../data/mockData'

const wait = (value, ms = 220) => new Promise(resolve => setTimeout(() => resolve(value), ms))

export const authService = { login: credentials => wait({ user: credentials?.email ? 'User Mehta' : 'User Mehta', authenticated: true }), logout: () => wait({ authenticated: false }) }
export const subjectService = { list: () => wait(mockSubjects), create: subject => wait({ ...subject, id: `subject-${Date.now()}` }) }
export const taskService = { list: () => wait(mockTasks), complete: id => wait({ id, status: 'completed' }), create: task => wait({ ...task, id: Date.now() }) }
export const plannerService = { generate: () => wait({ generated: true, message: 'Your plan has been optimized around your highest-risk topics.' }, 900) }
export const classroomService = { connect: () => wait({ connected: true, courses: 5, assignments: 12, materials: 34 }), sync: () => wait({ syncedAt: 'just now' }, 700) }
export const analyticsService = { getOverview: () => wait({ ready: true }) }
export const aiService = { ask: prompt => wait({ role: 'assistant', content: `Based on your RISE workspace, I would start with ${prompt.toLowerCase().includes('weak') ? 'Computer Networks: Transport Layer' : 'the next high-priority study block'}. I can turn that into a focused session whenever you are ready.` }) }
