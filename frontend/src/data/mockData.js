const storedUser = typeof localStorage !== 'undefined' ? JSON.parse(localStorage.getItem('rise_user') || 'null') : null
const storedName = storedUser ? [storedUser.first_name, storedUser.last_name].filter(Boolean).join(' ') || storedUser.email?.split('@')[0] : ''
const studentName = storedName || 'User Mehta'
const storedAvatar = storedUser?.avatar_url || (typeof localStorage !== 'undefined' ? localStorage.getItem('rise_profile_photo') : '')
if (typeof document !== 'undefined' && storedAvatar) document.documentElement.style.setProperty('--rise-avatar-url', `url(${JSON.stringify(storedAvatar)})`)
export const mockStudent = { name: studentName, initials: studentName.split(' ').map(part => part[0]).join('').slice(0, 2).toUpperCase(), semester: 'Semester 5 · Computer Engineering', level: 12, xp: 1240, streak: 7 }

export const mockSubjects = [
  { id: 'cn', name: 'Computer Networks', short: 'CN', color: '#9733EE', mastery: 52, risk: 91, priority: 'HIGH', exam: 'Aug 25', next: 'Transport Layer', units: [100, 85, 60, 20, 0] },
  { id: 'dbms', name: 'Database Systems', short: 'DB', color: '#E7984A', mastery: 72, risk: 72, priority: 'MEDIUM', exam: 'Aug 28', next: 'Normalization', units: [100, 90, 76, 54, 40] },
  { id: 'os', name: 'Operating Systems', short: 'OS', color: '#3E5275', mastery: 58, risk: 58, priority: 'MEDIUM', exam: 'Aug 31', next: 'Memory Management', units: [100, 80, 62, 30, 12] },
  { id: 'py', name: 'Python Programming', short: 'PY', color: '#6DAA7A', mastery: 84, risk: 34, priority: 'LOW', exam: 'Sep 04', next: 'Async Patterns', units: [100, 100, 92, 84, 70] },
]

export const mockTasks = [
  { id: 1, title: 'CN Lab Report', subject: 'Computer Networks', due: 'Tomorrow, Aug 19', estimate: '2 hours', priority: 'HIGH', source: 'Google Classroom', status: 'open', accent: '#9733EE' },
  { id: 2, title: 'Normalization worksheet', subject: 'Database Systems', due: 'Aug 21', estimate: '45 min', priority: 'MEDIUM', source: 'Manual', status: 'open', accent: '#E7984A' },
  { id: 3, title: 'Python Mini Project', subject: 'Python Programming', due: 'Aug 28', estimate: '4 hours', priority: 'LOW', source: 'Google Classroom', status: 'open', accent: '#6DAA7A' },
  { id: 4, title: 'OS process scheduling quiz', subject: 'Operating Systems', due: 'Completed Aug 16', estimate: '30 min', priority: 'MEDIUM', source: 'RISE Tutor', status: 'completed', accent: '#3E5275' },
]

export const mockNotes = [
  { id: 1, title: 'CN Unit 1 Notes', type: 'PDF', meta: 'Added Aug 14 · 12 pages', subject: 'Computer Networks', source: 'My notes' },
  { id: 2, title: 'Transport Layer Slides', type: 'PDF', meta: 'Posted by Professor · Aug 14', subject: 'Computer Networks', source: 'Google Classroom' },
  { id: 3, title: 'DBMS Normalization Slides', type: 'PDF', meta: 'Posted by Professor · Aug 15', subject: 'Database Systems', source: 'Google Classroom' },
  { id: 4, title: 'Important Questions', type: 'DOCX', meta: 'Added Aug 11 · 8 pages', subject: 'Computer Networks', source: 'My notes' },
  { id: 5, title: 'Python PYQs', type: 'PDF', meta: 'Added Aug 08 · 22 pages', subject: 'Python Programming', source: 'My notes' },
]

export const mockEvents = [
  { time: '09:00', title: 'College · Computer Networks', type: 'class', meta: 'Room 302' },
  { time: '11:00', title: 'College · Database Systems', type: 'class', meta: 'Lab 2' },
  { time: '16:00', title: 'Computer Networks', type: 'study', meta: 'Transport Layer · 45 min' },
  { time: '17:00', title: 'Break', type: 'break', meta: 'Walk + reset' },
  { time: '17:30', title: 'DBMS Assignment', type: 'task', meta: '45 min' },
  { time: '19:00', title: 'AI Knowledge Check', type: 'test', meta: '10 questions' },
]

export const mockMaterials = [
  { title: 'CN Unit 4 Notes', subject: 'Computer Networks', time: 'Added 2 hours ago' },
  { title: 'DBMS Normalization Slides', subject: 'Database Systems', time: 'Added yesterday' },
]

export const mockAnalytics = { studyTime: '14.2h', focusScore: '82%', completion: '78%', growth: '+18%', distraction: '2h 14m', weekly: [2.1, 3.4, 1.8, 4.2, 3.8, 5.1, 2.7], mastery: [{ name: 'CN', value: 52 }, { name: 'DB', value: 72 }, { name: 'OS', value: 58 }, { name: 'PY', value: 84 }] }

export const mockQuiz = [{ question: 'What is the purpose of TCP congestion control?', options: ['Encrypt packets', 'Prevent network overload', 'Assign IP addresses', 'Compress payloads'], answer: 1 }, { question: 'Which signal indicates a congested network?', options: ['Increasing RTT', 'Higher bandwidth', 'Shorter packets', 'More DNS records'], answer: 0 }]

export function hydrateBackendData({ subjects = [], tasks = [], resources = [] }) {
  if (subjects.length) {
    mockSubjects.splice(0, mockSubjects.length, ...subjects)
  }
  if (tasks.length) {
    mockTasks.splice(0, mockTasks.length, ...tasks)
  }
  if (resources.length) {
    mockNotes.splice(0, mockNotes.length, ...resources)
  }
}
