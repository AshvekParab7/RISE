import { mockAnalytics, mockEvents, mockMaterials, mockNotes, mockQuiz, mockStudent, mockSubjects, mockTasks } from './mockData'

export const workspaceSeed = {
  student: mockStudent,
  subjects: mockSubjects,
  topics: mockSubjects.flatMap(subject => subject.units.map((mastery, index) => ({ id: `${subject.id}-unit-${index + 1}`, subjectId: subject.id, name: `Unit ${index + 1}`, mastery }))),
  syllabus: { subjects: 5, units: 27, topics: 143, status: 'analyzed' },
  notes: mockNotes,
  classroomMaterials: mockMaterials,
  tasks: mockTasks,
  exams: mockSubjects.map(subject => ({ subjectId: subject.id, subject: subject.name, date: subject.exam })),
  collegeTimetable: mockEvents.filter(event => event.type === 'class'),
  calendarEvents: mockEvents,
  studyPlan: mockEvents,
  focusSessions: [],
  quizResults: [],
  mastery: Object.fromEntries(mockSubjects.map(subject => [subject.id, subject.mastery])),
  priorities: Object.fromEntries(mockSubjects.map(subject => [subject.id, subject.risk])),
  notifications: [],
  integrations: { classroom: false, calendar: false },
  gamification: { level: mockStudent.level, xp: mockStudent.xp, streak: mockStudent.streak },
  analytics: mockAnalytics,
  quiz: mockQuiz,
}
