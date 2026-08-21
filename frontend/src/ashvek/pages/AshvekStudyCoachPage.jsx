import { useEffect, useState } from 'react'
import { BookOpen, Brain, Check, ChevronRight, FileText, Flame, RotateCcw, Sparkles, Upload } from 'lucide-react'
import { get } from '../../services/api'
import { resourceService } from '../../services/resourceService'
import { studyCoachApi } from '../services/studyCoachApi'
import QuestionCard from '../components/QuestionCard'
import SessionReport from '../components/SessionReport'
import SourceList from '../components/SourceList'
import StepIndicator from '../components/StepIndicator'
import TutorTabs from '../../learning_paths/TutorTabs'
import '../styles.css'

const asArray = value => Array.isArray(value) ? value : value?.results || []

export default function AshvekStudyCoachPage() {
  const [subjects, setSubjects] = useState([])
  const [topics, setTopics] = useState([])
  const [resources, setResources] = useState([])
  const [sessions, setSessions] = useState([])
  const [subjectId, setSubjectId] = useState('')
  const [topicId, setTopicId] = useState('')
  const [topic, setTopic] = useState('')
  const [resourceIds, setResourceIds] = useState([])
  const [mode, setMode] = useState('TEACH')
  const [session, setSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [evaluation, setEvaluation] = useState(null)
  const [lesson, setLesson] = useState(null)
  const [practiceQuestions, setPracticeQuestions] = useState([])
  const [practiceAnswers, setPracticeAnswers] = useState({})
  const [revision, setRevision] = useState(null)
  const [busy, setBusy] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  const loadWorkspace = async () => {
    try {
      const [subjectResponse, topicResponse, resourceResponse, sessionResponse] = await Promise.all([get('/subjects/'), get('/topics/'), get('/resources/'), studyCoachApi.listSessions()])
      setSubjects(asArray(subjectResponse)); setTopics(asArray(topicResponse)); setResources(asArray(resourceResponse).filter(item => item.processing_status === 'READY')); setSessions(asArray(sessionResponse))
    } catch (reason) { setError(reason.message) }
  }
  useEffect(() => { loadWorkspace() }, [])

  const resetSessionView = loaded => {
    if (!loaded) { setSession(null); setMessages([]); setQuestion(null); setLesson(null); setEvaluation(null); setRevision(null); setPracticeQuestions([]); setPracticeAnswers({}); return }
    setSession(loaded); setMessages(loaded.messages || []); setQuestion(loaded.current_question || null); setLesson(loaded.current_step === 0 ? { explanation: 'Building your first lesson...', example: 'RISE is preparing a short explanation and your first question.', sources: [] } : null); setEvaluation(null); setRevision(null); setPracticeQuestions([]); setPracticeAnswers({}); setMode(loaded.mode || 'TEACH')
  }
  const chooseTopic = value => { setTopicId(value); setTopic(topics.find(item => String(item.id) === String(value))?.name || '') }
  const toggleResource = id => setResourceIds(current => current.includes(id) ? current.filter(item => item !== id) : [...current, id])

  const startSession = async event => {
    event?.preventDefault(); setBusy(true); setError('')
    try {
      const created = await studyCoachApi.createSession({ topic: topic.trim(), subject_id: subjectId || null, topic_id: topicId || null, resource_ids: resourceIds, mode })
      resetSessionView(created)
      if (mode === 'TEACH') await teach(created.id)
      if (mode === 'PRACTICE') await startPractice(created)
      if (mode === 'REVISION') await revise(created.id)
      setSessions(current => [created, ...current])
    } catch (reason) { setError(reason.message) } finally { setBusy(false) }
  }
  const teach = async sessionId => {
    setBusy(true); setError('')
    try { const response = await studyCoachApi.teach({ session_id: sessionId, prompt: topic }); setSession(response.session); setLesson(response.lesson); setQuestion(response.lesson.question); setMessages(response.session.messages || []); setMode('TEACH') } catch (reason) { setError(reason.message) } finally { setBusy(false) }
  }
  const submitAnswer = async (helpRequested = false) => {
    if (!session) return
    helpRequested = helpRequested || !answer.trim()
    setBusy(true); setError('')
    try { const response = await studyCoachApi.answer({ session_id: session.id, answer, help_requested: helpRequested }); setSession(response.session); setEvaluation(response.evaluation); setQuestion(response.next_question); setLesson(response.reteach || lesson); setMessages(response.session.messages || []); setAnswer('') } catch (reason) { setError(reason.message) } finally { setBusy(false) }
  }
  const startPractice = async sessionOverride => {
    const target = sessionOverride || session
    if (!target) return
    setBusy(true); setError('')
    try { const response = await studyCoachApi.practice({ session_id: target.id, question_count: 5, difficulty: 'ADAPTIVE' }); setSession(response.session); setPracticeQuestions(response.questions); setPracticeAnswers({}); setMode('PRACTICE') } catch (reason) { setError(reason.message) } finally { setBusy(false) }
  }
  const submitPractice = async () => {
    setBusy(true); setError('')
    try { const response = await studyCoachApi.practice({ session_id: session.id, answers: practiceAnswers }); setSession(response.session); setRevision(null); setPracticeQuestions([]) } catch (reason) { setError(reason.message) } finally { setBusy(false) }
  }
  const revise = async sessionId => {
    setBusy(true); setError('')
    try { const response = await studyCoachApi.revision({ session_id: sessionId }); setSession(response.session); setRevision(response.revision); setMessages(response.session.messages || []); setMode('REVISION') } catch (reason) { setError(reason.message) } finally { setBusy(false) }
  }
  const complete = async () => { if (!session) return; if (session.weaknesses?.length && !window.confirm(`You still have ${session.weaknesses.length} concept${session.weaknesses.length === 1 ? '' : 's'} that need practice. Press OK to finish anyway, or Cancel to continue learning.`)) return; setBusy(true); try { setSession(await studyCoachApi.complete(session.id)); setMode('REPORT') } catch (reason) { setError(reason.message) } finally { setBusy(false) } }
  const continueSession = async id => { setBusy(true); try { resetSessionView(await studyCoachApi.getSession(id)) } catch (reason) { setError(reason.message) } finally { setBusy(false) } }
  const uploadNotes = async event => {
    const file = event.target.files?.[0]
    if (!file || !subjectId) { setError('Choose a subject before uploading a note.'); return }
    setUploading(true); setError('')
    try { const form = new FormData(); form.append('subject', subjectId); form.append('title', file.name); form.append('file', file); form.append('resource_type', 'NOTE'); await resourceService.upload(form); const refreshed = await get('/resources/'); setResources(asArray(refreshed).filter(item => item.processing_status === 'READY')) } catch (reason) { setError(reason.message) } finally { setUploading(false); event.target.value = '' }
  }

  const visibleTopics = topics.filter(item => !subjectId || String(item.subject) === String(subjectId))
  const selectedSubject = subjects.find(item => String(item.id) === String(subjectId))

  return <div className="ashvek-page"><TutorTabs/>
    <div className="ashvek-header"><div><p className="eyebrow">ADAPTIVE STUDY COACH</p><h1>Learn by doing, not scrolling.</h1><p className="muted lead">RISE explains, checks your thinking, finds the gap, and chooses the next step.</p></div><div className="ashvek-points"><Flame size={17}/><span>Today</span><strong>{session?.points || 0}</strong><small>learning points</small></div></div>
    {error && <p className="api-error">{error}</p>}
    {!session && <div className="ashvek-start-grid"><form className="panel ashvek-launcher" onSubmit={startSession}><div className="ashvek-launch-icon"><Brain size={24}/></div><h2>What do you want to learn?</h2><p className="muted">Start a guided lesson, build a revision card, or jump straight into practice.</p><input value={topic} onChange={event => setTopic(event.target.value)} placeholder="Teach me K-Means..." required maxLength={200}/><div className="ashvek-form-row"><label>Subject<select value={subjectId} onChange={event => { setSubjectId(event.target.value); setTopicId('') }}><option value="">Any subject</option>{subjects.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label>Topic<select value={topicId} onChange={event => chooseTopic(event.target.value)}><option value="">Use my topic</option>{visibleTopics.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label></div><div className="ashvek-mode-tabs">{[['TEACH', 'Teach Me', 'Step-by-step tutor'], ['PRACTICE', 'Practice', 'Generated questions'], ['REVISION', 'Quick Revision', 'Compact recall']].map(item => <button type="button" className={mode === item[0] ? 'active' : ''} onClick={() => setMode(item[0])} key={item[0]}><strong>{item[1]}</strong><small>{item[2]}</small></button>)}</div><div className="ashvek-resource-picker"><div className="ashvek-picker-head"><span><FileText size={15}/> Ground it in my resources</span><label className="button"><Upload size={14}/> {uploading ? 'Uploading...' : 'Upload note'}<input hidden type="file" accept=".pdf,.doc,.docx,.ppt,.pptx,.png,.jpg,.jpeg,.webp" onChange={uploadNotes}/></label></div>{resources.length ? resources.map(resource => <label className="ashvek-resource" key={resource.id}><input type="checkbox" checked={resourceIds.includes(resource.id)} onChange={() => toggleResource(resource.id)}/><span><b>{resource.title}</b><small>{resource.file_size} bytes · {resource.source === 'GOOGLE_CLASSROOM' ? 'Google Classroom' : 'My notes'}</small></span></label>) : <small className="muted">Processed resources will appear here.</small>}</div><button className="button button-primary ashvek-start" disabled={busy}>{busy ? 'Preparing...' : mode === 'TEACH' ? 'Start guided lesson' : mode === 'PRACTICE' ? 'Start practice' : 'Build quick revision' }<ChevronRight size={17}/></button></form><aside className="ashvek-continue panel"><div className="ashvek-aside-title"><h3>Continue learning</h3><RotateCcw size={17}/></div>{sessions.length ? sessions.slice(0, 5).map(item => <button className="ashvek-session-row" onClick={() => continueSession(item.id)} key={item.id}><span><BookOpen size={16}/></span><div><b>{item.topic_label}</b><small>{item.status === 'COMPLETED' ? 'Completed' : `${item.points} points`} · {item.mode}</small></div><ChevronRight size={16}/></button>) : <p className="muted">Your active lessons will stay here so you can return later.</p>}</aside></div>}
    {session && <div className="ashvek-session-layout"><main><div className="ashvek-session-top"><button className="text-button" onClick={() => resetSessionView(null)}>← New session</button><div><p className="eyebrow">{selectedSubject?.name || session.subject_name || 'PERSONAL STUDY'}</p><h2>{session.topic_label}</h2></div><div className="ashvek-session-actions"><span><Sparkles size={15}/> {session.points} pts</span><button className="button" onClick={complete} disabled={busy}>Finish session</button></div></div><StepIndicator step={session.current_step || 1} status={session.status}/>{mode === 'REPORT' || session.status === 'COMPLETED' ? <SessionReport report={session.report} points={session.points} onPractice={startPractice} onContinue={() => setMode('TEACH')}/> : mode === 'PRACTICE' && practiceQuestions.length ? <section className="ashvek-practice"><div className="ashvek-section-heading"><div><p className="eyebrow">PRACTICE</p><h2>Show what you can do</h2></div><span>Adaptive · {practiceQuestions.length} questions</span></div>{practiceQuestions.map((item, index) => <div className="ashvek-practice-question panel" key={item.id}><span>{index + 1}</span><h3>{item.question}</h3>{item.options.map(option => <label key={option}><input type="radio" name={item.id} checked={practiceAnswers[item.id] === option} onChange={() => setPracticeAnswers(current => ({ ...current, [item.id]: option }))}/>{option}</label>)}</div>)}<button className="button button-primary" onClick={submitPractice} disabled={busy || Object.keys(practiceAnswers).length !== practiceQuestions.length}>Complete practice <Check size={16}/></button></section> : mode === 'REVISION' && revision ? <section className="ashvek-revision panel"><p className="eyebrow">QUICK REVISION</p><h2>Keep the important bits close</h2>{Object.entries(revision).filter(([, value]) => Array.isArray(value) && value.length).map(([key, value]) => <div key={key}><b>{key.replaceAll('_', ' ')}</b>{value.map((item, index) => <p key={index}>{typeof item === 'string' ? item : item.definition || JSON.stringify(item)}</p>)}</div>)}<SourceList sources={session.messages?.at(-1)?.sources}/></section> : <><section className="ashvek-lesson panel"><div className="ashvek-lesson-title"><span>STEP {Math.min(session.current_step || 1, 9)}</span><small>Guided explanation</small></div>{lesson ? <><h2>{lesson.explanation}</h2><div className="ashvek-example"><b>Simple example</b><p>{lesson.example}</p></div><SourceList sources={lesson.sources}/></> : <div className="ashvek-message-list">{messages.slice(-4).map((message, index) => <div className={`ashvek-message ${message.role}`} key={index}>{typeof message.content === 'string' ? message.content : JSON.stringify(message.content)}</div>)}</div>}</section><QuestionCard question={question} answer={answer} setAnswer={setAnswer} onSubmit={submitAnswer} busy={busy} feedback={evaluation}/></>}</main><aside className="ashvek-side-panel"><div className="panel ashvek-progress-card"><p className="eyebrow">YOUR MAP</p>{Object.entries(session.concepts || {}).length ? Object.entries(session.concepts).map(([name, value]) => <div className="ashvek-concept" key={name}><span>{name}</span><b className={value.toLowerCase()}>{value}</b></div>) : <p className="muted">Your understanding map will fill in as you answer.</p>}</div><div className="panel ashvek-weakness-card"><p className="eyebrow">DETECTED GAPS</p>{session.weaknesses?.length ? session.weaknesses.map(item => <p key={item}>⚠ {item}</p>) : <p className="muted">No weak concepts detected yet.</p>}</div>{evaluation && <button className="button button-primary ashvek-side-action" onClick={startPractice}><Sparkles size={16}/> Practice this area</button>}</aside></div>}
  </div>
}
