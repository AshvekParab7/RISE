import { get } from './api'
import { hydrateBackendData } from '../data/mockData'

const asArray = response => Array.isArray(response) ? response : response?.results || []
const shortCode = subject => subject.code || subject.name.split(/\s+/).map(word => word[0]).join('').slice(0, 2).toUpperCase()
const sourceLabel = source => ({ USER_UPLOAD: 'My notes', GOOGLE_CLASSROOM: 'Google Classroom' }[source] || source)
const priorityLabel = score => score >= 85 ? 'HIGH' : score >= 55 ? 'MEDIUM' : 'LOW'

export async function loadBackendWorkspace() {
  const [semestersResponse, subjectsResponse, topicsResponse, tasksResponse, resourcesResponse] = await Promise.all([
    get('/semesters/'), get('/subjects/'), get('/topics/'), get('/tasks/'), get('/resources/'),
  ])
  const semesters = asArray(semestersResponse)
  const subjects = asArray(subjectsResponse)
  const topics = asArray(topicsResponse)
  const tasks = asArray(tasksResponse)
  const resources = asArray(resourcesResponse)
  const subjectsById = Object.fromEntries(subjects.map(subject => [subject.id, subject]))
  const topicGroups = topics.reduce((groups, topic) => { (groups[topic.subject] ||= []).push(topic); return groups }, {})
  const mappedSubjects = subjects.map(subject => ({
    id: subject.id, name: subject.name, short: shortCode(subject), color: subject.color || '#9733EE',
    mastery: subject.mastery_percentage ?? 0, risk: subject.priority_score ?? 0, priority: priorityLabel(subject.priority_score ?? 0),
    exam: subject.exam_date || 'Not scheduled', next: topicGroups[subject.id]?.[0]?.name || 'First topic',
    units: topicGroups[subject.id]?.slice(0, 5).map(topic => topic.mastery_percentage) || [], code: subject.code,
  }))
  const mappedTasks = tasks.map(task => ({
    id: task.id, title: task.title, subject: subjectsById[task.subject]?.name || 'General', due: task.deadline, estimate: `${task.estimated_minutes} min`,
    priority: task.priority, source: task.source, status: task.status === 'COMPLETED' ? 'completed' : 'open',
  }))
  const mappedResources = resources.map(resource => ({
    id: resource.id, title: resource.title, type: resource.resource_type, meta: `${resource.file_size || 0} bytes`,
    subject: subjectsById[resource.subject]?.name || 'General', source: sourceLabel(resource.source), file: resource.file,
  }))
  hydrateBackendData({ subjects: mappedSubjects, tasks: mappedTasks, resources: mappedResources })
  return { semester: semesters.find(item => item.is_current) || semesters[0], subjects: mappedSubjects, topics, tasks: mappedTasks, resources: mappedResources }
}
