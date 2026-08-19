import { useEffect, useMemo, useState } from 'react'
import { CalendarDays, Check, MessageCircle, Moon, Pencil, Plus, Send, Sparkles, Sun, Trash2, X } from 'lucide-react'
import { aiService } from './services/aiService'
import { get } from './services/api'
import { plannerService } from './services/plannerService'
import './planner.css'

const colors = ['#6D5EF5', '#E7984A', '#3E8F8B', '#D65B72', '#4D7BC4']
const asArray = value => Array.isArray(value) ? value : value?.results || []
const dateKey = value => new Date(value).toISOString().slice(0, 10)
const localDateTime = value => {
  const date = value ? new Date(value) : new Date(Date.now() + 3600000)
  const offset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}
const dayLabel = value => new Intl.DateTimeFormat('en-US', { weekday: 'short', month: 'short', day: 'numeric' }).format(new Date(`${value}T12:00:00`))
const daysFrom = (start, count) => Array.from({ length: count }, (_, index) => { const date = new Date(`${start}T12:00:00`); date.setDate(date.getDate() + index); return date.toISOString().slice(0, 10) })
const toIso = value => /(?:Z|[+-]\d{2}:?\d{2})$/.test(value) ? value : new Date(value).toISOString()
const resolvePlanDay = (label, days, fallback) => { const normalized = String(label || '').toLowerCase(); if (normalized.includes('tomorrow')) return days[1] || fallback; return days.find(value => normalized.includes(new Date(`${value}T12:00:00`).toLocaleDateString('en-US', { weekday: 'short' }).toLowerCase())) || fallback }

function EventForm({ event, subjects, onCancel, onSave, saving }) {
  const [form, setForm] = useState(event || { title: '', subtopics: '', start_at: localDateTime(), duration_minutes: 45, color: colors[0], event_type: 'STUDY', subject: subjects[0]?.id || '' })
  const update = (key, value) => setForm(current => ({ ...current, [key]: value }))
  return <div className="panel event-popup"><div className="section-head"><div><p className="eyebrow">{event ? 'EDIT EVENT' : 'NEW EVENT'}</p><h2>{event ? 'Tune this study block' : 'Add a study event'}</h2></div><button className="icon-button" onClick={onCancel} aria-label="Close event editor"><X size={17}/></button></div><div className="form-grid"><label>Title<input value={form.title} onChange={event => update('title', event.target.value)} placeholder="e.g. Revise TCP congestion control" autoFocus/></label><label>Subject<select value={form.subject || ''} onChange={event => update('subject', event.target.value)}><option value="">No subject</option>{subjects.map(subject => <option key={subject.id} value={subject.id}>{subject.name}</option>)}</select></label><label>Start time<input type="datetime-local" value={localDateTime(form.start_at)} onChange={event => update('start_at', event.target.value)}/></label><label>Duration (minutes)<input type="number" min="1" value={form.duration_minutes} onChange={event => update('duration_minutes', Number(event.target.value))}/></label></div><label className="event-form-wide">Subtopics<textarea value={form.subtopics} onChange={event => update('subtopics', event.target.value)} placeholder="What will you cover?" rows="3"/></label><fieldset className="event-color-field"><legend>Event color</legend><div className="event-color-options">{colors.map(color => <button type="button" key={color} className={`event-color-choice ${form.color === color ? 'selected' : ''}`} style={{ background: color }} onClick={() => update('color', color)} aria-label={`Use ${color} event color`}/>)}</div></fieldset><div className="button-row"><button className="button" onClick={onCancel}>Cancel</button><button className="button button-primary" onClick={() => onSave({ ...form, subject: form.subject || null, duration_minutes: Number(form.duration_minutes) })} disabled={saving}>{saving ? 'Saving...' : 'Save event'}</button></div></div>
}

function EventCard({ event, onEdit, onDelete }) {
  return <div className="planner-event" style={{ borderLeftColor: event.color }}><button className="event-delete" onClick={() => onDelete(event)} aria-label={`Delete ${event.title}`}><Trash2 size={13}/></button><b>{event.title}</b><small>{event.subtopics || 'Study block'} · {event.duration_minutes} min</small><span>{new Date(event.start_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span><button className="icon-button" onClick={() => onEdit(event)} aria-label={`Edit ${event.title}`}><Pencil size={14}/></button></div>
}

function PlannerChat({ events, onCreate }) {
  const [messages, setMessages] = useState([{ role: 'assistant', content: 'Tell me what you want to study and when you are available. I will ask only for the details needed to make a realistic block.' }])
  const [input, setInput] = useState('')
  const [pending, setPending] = useState(null)
  const [loading, setLoading] = useState(false)
  const send = async text => {
    const message = (text || input).trim()
    if (!message || loading) return
    setInput('')
    const next = [...messages, { role: 'user', content: message }]
    setMessages(next)
    setLoading(true)
    try {
      const response = await aiService.planner({ message, history: next, calendar: events.map(event => ({ title: event.title, start: event.start_at, duration: event.duration_minutes, source: 'RISE' })) })
      setMessages(items => [...items, { role: 'assistant', content: response.reply || 'I need one more detail before I can plan that.' }])
      setPending(response.ready ? response : null)
    } catch (reason) {
      setMessages(items => [...items, { role: 'assistant', content: reason.message }])
    } finally { setLoading(false) }
  }
  const confirm = async () => { if (!pending) return; await onCreate(pending.plan); setMessages(items => [...items, { role: 'assistant', content: 'Added the confirmed study blocks to your RISE planner.' }]); setPending(null) }
  return <section className="panel planner-chat"><div className="planner-chat-head"><MessageCircle size={17}/><div><b>RISE Planner</b><small>Planning conversations stay in your account.</small></div></div><div className="planner-chat-messages">{messages.map((message, index) => <div className={`planner-chat-message ${message.role}`} key={`${message.role}-${index}`}>{message.content}</div>)}{pending && <div className="planner-chat-options"><button onClick={confirm}><Check size={13}/> Add proposed plan</button><button onClick={() => setPending(null)}>Let me change it</button></div>}{loading && <div className="planner-chat-message">RISE is thinking...</div>}</div><div className="planner-chat-input"><input value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => event.key === 'Enter' && send()} placeholder="Ask about your study plan" aria-label="Ask RISE Planner"/><button onClick={() => send()} aria-label="Send planner message"><Send size={15}/></button></div></section>
}

export default function PlannerPage() {
  const [plannerSubjects, setPlannerSubjects] = useState([])
  const [events, setEvents] = useState([])
  const [view, setView] = useState('day')
  const [selectedDay, setSelectedDay] = useState(dateKey(new Date()))
  const [editor, setEditor] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('rise_theme') === 'dark')
  const weekDays = useMemo(() => daysFrom(selectedDay, 7), [selectedDay])
  const load = () => plannerService.list().then(data => setEvents(asArray(data))).catch(reason => setError(reason.message)).finally(() => setLoading(false))
  useEffect(() => { load() }, [])
  useEffect(() => { get('/subjects/').then(data => setPlannerSubjects(asArray(data))).catch(reason => setError(reason.message)) }, [])
  useEffect(() => { document.documentElement.dataset.theme = darkMode ? 'dark' : 'light'; localStorage.setItem('rise_theme', darkMode ? 'dark' : 'light') }, [darkMode])
  const save = async payload => { setSaving(true); setError(''); try { const normalizedPayload = { ...payload, start_at: toIso(payload.start_at) }; const response = editor?.id ? await plannerService.update(editor.id, normalizedPayload) : await plannerService.create(normalizedPayload); setEvents(items => editor?.id ? items.map(item => item.id === editor.id ? response : item) : [...items, response]); setEditor(null) } catch (reason) { setError(reason.message) } finally { setSaving(false) } }
  const remove = async event => { if (!window.confirm(`Delete ${event.title}?`)) return; try { await plannerService.remove(event.id); setEvents(items => items.filter(item => item.id !== event.id)) } catch (reason) { setError(reason.message) } }
  const createPlan = async plan => { for (const item of plan) { const day = resolvePlanDay(item.day, weekDays, selectedDay); await plannerService.create({ title: item.title, subtopics: item.subtopic || '', start_at: toIso(`${day}T${item.time}`), duration_minutes: item.duration || 45, color: colors[0], event_type: 'STUDY' }) } await load() }
  const shown = events.filter(event => view === 'week' ? weekDays.includes(dateKey(event.start_at)) : dateKey(event.start_at) === selectedDay).sort((a, b) => new Date(a.start_at) - new Date(b.start_at))
  return <><div className="page-header"><div><p className="eyebrow">YOUR WEEK, INTELLIGENTLY ARRANGED</p><h1>Study planner</h1><p className="muted lead">Persisted RISE study blocks, separate from imported Google Calendar events.</p></div><div className="button-row"><button className="button" onClick={() => setDarkMode(value => !value)}>{darkMode ? <Sun size={16}/> : <Moon size={16}/>} {darkMode ? 'Light mode' : 'Dark mode'}</button><button className="button" onClick={() => setView(view === 'day' ? 'week' : 'day')}><CalendarDays size={16}/>{view === 'day' ? 'Week view' : 'Day view'}</button><button className="button button-primary" onClick={() => setEditor({})}><Plus size={16}/>Add event</button></div></div>{error && <p className="api-error">{error}</p>}{editor && <EventForm event={editor.id ? editor : null} subjects={plannerSubjects} onCancel={() => setEditor(null)} onSave={save} saving={saving}/>}<div className="planner-toolbar"><div className="planner-tabs"><button className={view === 'day' ? 'active' : ''} onClick={() => setView('day')}>Day<small>{dayLabel(selectedDay)}</small></button><button className={view === 'week' ? 'active' : ''} onClick={() => setView('week')}>Week<small>{dayLabel(weekDays[0])}</small></button></div><input className="planner-day-selector" type="date" value={selectedDay} onChange={event => setSelectedDay(event.target.value)} /></div><div className="planner-with-chat"><main className="planner-main">{loading ? <div className="panel loading-state">Loading planner events...</div> : view === 'day' ? <div className="panel planner-day-view"><div className="day-column planner-day-column"><b>{dayLabel(selectedDay)}</b><div className="day-line"/>{shown.length ? shown.map(event => <EventCard key={event.id} event={event} onEdit={setEditor} onDelete={remove}/>) : <div className="empty-state"><Sparkles size={22}/><h3>No study blocks yet</h3><p>Add an event or ask RISE Planner to propose one.</p></div>}</div></div> : <div className="panel week-grid planner-week-seven">{weekDays.map(day => <div className="day-column" key={day}><b>{dayLabel(day)}</b><div className="day-line"/>{events.filter(event => dateKey(event.start_at) === day).map(event => <EventCard key={event.id} event={event} onEdit={setEditor} onDelete={remove}/>)}</div>)}</div>}</main><PlannerChat events={events} onCreate={createPlan}/></div></>
}
