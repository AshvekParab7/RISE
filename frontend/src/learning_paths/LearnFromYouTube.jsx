import { useEffect, useRef, useState } from 'react'
import { BookOpen, Check, ChevronRight, CirclePlay, LockKeyhole, RotateCcw, Search, Sparkles, Trophy, Zap } from 'lucide-react'
import { learningPathsApi } from './learningPathsApi'
import LearningMap from './LearningMap'
import TutorTabs from './TutorTabs'
import './learnFromYouTube.css'

const asPercent = (completed, total) => total ? Math.round(completed / total * 100) : 0

function LearnFromYouTubeContent() {
  const [url, setUrl] = useState('')
  const [paths, setPaths] = useState([])
  const [path, setPath] = useState(null)
  const [level, setLevel] = useState(null)
  const [step, setStep] = useState(0)
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState(null)
  const [finalChallenge, setFinalChallenge] = useState(null)
  const [finalAnswers, setFinalAnswers] = useState({})
  const [mapTransition, setMapTransition] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [selectedVideo, setSelectedVideo] = useState(null)
  const [searchBusy, setSearchBusy] = useState(false)
  const [processingStep, setProcessingStep] = useState(0)
  const [finishingPathId, setFinishingPathId] = useState(null)
  const processingPathId = useRef(null)

  const loadPaths = async () => { try { setPaths(await learningPathsApi.list()) } catch (reason) { setError(reason.message) } }
  useEffect(() => { loadPaths() }, [])
  useEffect(() => {
    const rows = document.querySelectorAll('.yt-continue > button')
    rows.forEach((row, index) => {
      if (row.querySelector('.yt-row-delete')) return
      const control = document.createElement('span')
      control.className = 'yt-row-delete'
      control.setAttribute('role', 'button')
      control.setAttribute('tabindex', '0')
      control.textContent = 'Remove'
      const remove = event => { event.preventDefault(); event.stopPropagation(); deleteSavedPath(paths[index].id) }
      control.addEventListener('click', remove)
      control.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') remove(event) })
      row.appendChild(control)
    })
  }, [paths])
  useEffect(() => {
    if (!path || path.status !== 'PROCESSING') return undefined
    processingPathId.current = path.id
    setProcessingStep(0)
    const stageTimer = setInterval(() => setProcessingStep(current => Math.min(current + 1, 4)), 3200)
    const timer = setInterval(async () => { try { const refreshed = await learningPathsApi.detail(path.id); setPath(refreshed); if (refreshed.status !== 'PROCESSING') clearInterval(timer) } catch (reason) { setError(reason.message) } }, 2000)
    return () => { clearInterval(stageTimer); clearInterval(timer) }
  }, [path?.id, path?.status])
  useEffect(() => {
    if (!path || path.status !== 'READY' || processingPathId.current !== path.id) return undefined
    processingPathId.current = null
    setFinishingPathId(path.id)
    const timer = setTimeout(() => setFinishingPathId(null), 900)
    return () => clearTimeout(timer)
  }, [path])
  useEffect(() => { const showMap = event => { setLevel(null); setMapTransition(event.detail || null) }; window.addEventListener('rise:learning-map', showMap); return () => window.removeEventListener('rise:learning-map', showMap) }, [])

  const searchYouTube = async event => { event.preventDefault(); if (searchQuery.trim().length < 2) return; setSearchBusy(true); setError(''); try { setSearchResults((await learningPathsApi.searchYouTube(searchQuery.trim())).results || []) } catch (reason) { setError(reason.message); setSearchResults([]) } finally { setSearchBusy(false) } }
  const createPath = async (event, targetUrl = url) => { event.preventDefault(); setBusy(true); setError(''); try { const created = await learningPathsApi.create(targetUrl); setPath(created); setLevel(null); await loadPaths() } catch (reason) { setError(reason.message) } finally { setBusy(false) } }
  const useSelectedVideo = () => { if (!selectedVideo) return; setUrl(selectedVideo.url); createPath({ preventDefault: () => {} }, selectedVideo.url) }
  const resume = async id => { setBusy(true); setError(''); try { const loaded = await learningPathsApi.resume(id); setPath(loaded); setLevel(null); setStep(0); if (loaded.status !== 'COMPLETED' && loaded.levels.length && loaded.levels.every(item => item.status === 'COMPLETED')) setFinalChallenge(await learningPathsApi.finalChallenge(id)) } catch (reason) { setError(reason.message) } finally { setBusy(false) } }
  const openLevel = async selected => { if (selected.status === 'LOCKED') return; setBusy(true); setError(''); try { const started = await learningPathsApi.startLevel(path.id, selected.id); setLevel(started); setStep(0); setFeedback(null); setAnswer('') } catch (reason) { setError(reason.message) } finally { setBusy(false) } }
  const submitCheckpoint = async () => { if (!answer.trim()) return; setBusy(true); setError(''); try { const response = await learningPathsApi.checkpoint(path.id, level.id, answer); setPath(response.path); setLevel(response.level); setFeedback(response.attempt); setAnswer(''); if (response.attempt.correct) { setStep(3); window.setTimeout(() => window.dispatchEvent(new CustomEvent('rise:learning-map', { detail: { completedOrder: level.order } })), 1400) } } catch (reason) { setError(reason.message) } finally { setBusy(false) } }
  const submitFinal = async () => { setBusy(true); setError(''); try { const response = await learningPathsApi.submitFinalChallenge(path.id, finalAnswers); setPath(response.path); setFinalChallenge(null) } catch (reason) { setError(reason.message) } finally { setBusy(false) } }
  const openFinalChallenge = async () => { setBusy(true); setError(''); try { setFinalChallenge(await learningPathsApi.finalChallenge(path.id)) } catch (reason) { setError(reason.message) } finally { setBusy(false) } }
  const deletePath = async () => { if (!window.confirm(`Delete saved learning path "${path.title || 'this lecture'}"? This removes its levels, notes, attempts, and progress.`)) return; setBusy(true); setError(''); try { await learningPathsApi.remove(path.id); reset(); await loadPaths() } catch (reason) { setError(reason.message) } finally { setBusy(false) } }
  const deleteSavedPath = async id => { const item = paths.find(pathItem => pathItem.id === id); if (!item || !window.confirm(`Delete saved learning path "${item.title || 'this lecture'}"? This removes its progress and notes.`)) return; setError(''); try { await learningPathsApi.remove(id); setPaths(current => current.filter(pathItem => pathItem.id !== id)) } catch (reason) { setError(reason.message) } }
  const retry = async () => { setBusy(true); setError(''); try { setPath(await learningPathsApi.create(path.youtube_url, true)) } catch (reason) { setError(reason.message) } finally { setBusy(false) } }
  const reset = () => { setPath(null); setLevel(null); setFinalChallenge(null); setFinalAnswers({}); setUrl(''); setError('') }
  const sourceUrl = level && (() => { const source = new URL(path.youtube_url); source.searchParams.set('t', Math.floor(level.start_seconds)); return source.toString() })()

  if (!path) return <div className="yt-learn-page"><header className="yt-hero"><div><p className="eyebrow">RISE LEARNING PATHS</p><h1>Learn from YouTube</h1><p>Turn a captioned lecture into a step-by-step learning journey.</p></div><CirclePlay size={42}/></header>{error && <p className="api-error">{error}</p>}<div className="yt-home-grid"><section className="panel yt-url-card"><div className="yt-url-icon"><CirclePlay size={28}/></div><h2>Find a lecture to learn from</h2><p className="muted">Search YouTube or paste a link. RISE uses available captions to build your path.</p><form className="yt-search-form" onSubmit={searchYouTube}><label htmlFor="youtube-search">Search YouTube</label><div className="yt-input-row"><Search size={17}/><input id="youtube-search" value={searchQuery} onChange={event => setSearchQuery(event.target.value)} placeholder='Search for a topic, e.g. "Python for beginners"'/><button className="button button-primary" disabled={searchBusy || searchQuery.trim().length < 2}>{searchBusy ? 'Searching...' : 'Search'}</button></div></form>{searchResults.length > 0 && <div className="yt-results" aria-label="YouTube search results">{searchResults.map(video => <button className={`yt-result ${selectedVideo?.video_id === video.video_id ? 'selected' : ''}`} onClick={() => setSelectedVideo(video)} key={video.video_id}><img src={video.thumbnail} alt=""/><span><b>{video.title}</b><small>{video.channel} · {video.duration}</small><em>{video.description}</em></span></button>)}</div>}{selectedVideo && <div className="yt-preview"><div className="yt-player"><iframe src={`https://www.youtube-nocookie.com/embed/${selectedVideo.video_id}`} title={selectedVideo.title} allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen/></div><div className="yt-preview-meta"><div><b>{selectedVideo.title}</b><small>{selectedVideo.channel} · {selectedVideo.duration}</small></div><button className="button button-primary" onClick={useSelectedVideo} disabled={busy}><Sparkles size={15}/>RISE</button></div></div>}<div className="yt-or"><span>OR</span></div><form onSubmit={createPath}><label htmlFor="youtube-url">Paste YouTube URL</label><input id="youtube-url" type="url" value={url} onChange={event => setUrl(event.target.value)} placeholder="https://www.youtube.com/watch?v=..." required/><button className="button button-primary" disabled={busy}>{busy ? 'Building learning path...' : 'Start learning'}<ChevronRight size={16}/></button></form></section><aside className="panel yt-continue"><h3>Continue learning</h3>{paths.length ? paths.map(item => <button onClick={() => resume(item.id)} key={item.id}><span><BookOpen size={16}/></span><div><b>{item.title || 'Processing lecture'}</b><small>{item.completed_levels}/{item.total_levels} levels · {item.xp} XP</small><i><em style={{width:`${item.total_levels ? asPercent(item.completed_levels, item.total_levels) : item.processing_progress}%`}}/></i></div><ChevronRight size={16}/></button>) : <p className="muted">Your YouTube learning paths will stay here.</p>}</aside></div></div>
  if (path.status === 'PROCESSING' || finishingPathId === path.id) return <ProcessingView step={processingStep} finishing={finishingPathId === path.id}/>
  if (path.status === 'FAILED') return <div className="yt-processing failed"><CirclePlay size={34}/><p className="eyebrow">COULD NOT CREATE PATH</p><h1>Transcript processing failed</h1><p>{path.failure_reason}</p><div className="button-row"><button className="button button-primary" onClick={retry} disabled={busy}><RotateCcw size={15}/>Retry</button><button className="button" onClick={reset}>Use another video</button></div></div>
  if (finalChallenge) return <FinalChallenge path={path} challenge={finalChallenge} answers={finalAnswers} setAnswers={setFinalAnswers} submit={submitFinal} busy={busy}/>
  const completed = path.levels.filter(item => item.status === 'COMPLETED').length
  if (path.status === 'COMPLETED') return <div className="yt-complete panel"><Trophy size={46}/><p className="eyebrow">COURSE COMPLETE</p><h1>{path.title}</h1><div><strong>{completed}/{path.levels.length}<small>Levels</small></strong><strong>{path.mastery_percentage}%<small>Mastery</small></strong><strong>{path.xp}<small>XP</small></strong></div><button className="button button-primary" onClick={reset}>Back to learning paths</button></div>
  if (!level) return <div className="learning-map-shell"><LearningMap path={path} transition={mapTransition} onTransitionEnd={() => setMapTransition(null)} onSelect={openLevel} onFinalChallenge={openFinalChallenge} onBack={reset}/><button className="button learning-map-delete" onClick={deletePath} disabled={busy}>Delete saved learning path</button></div>

  return <div className="yt-course"><header className="yt-course-head"><button className="text-button" onClick={reset}>← Learning paths</button><div><p className="eyebrow">LEARN FROM YOUTUBE</p><h1>{path.title}</h1></div><div className="yt-xp"><Zap size={16}/><strong>{path.xp}</strong><span>XP</span></div></header><div className="yt-course-progress"><span style={{width:`${asPercent(completed, path.levels.length)}%`}}/></div><div className="yt-course-grid"><aside className="panel yt-map"><p className="eyebrow">LEARNING MAP</p>{path.levels.map(item => <button className={`${item.status.toLowerCase()} ${level?.id === item.id ? 'current' : ''}`} onClick={() => openLevel(item)} key={item.id}><span>{item.status === 'COMPLETED' ? <Check size={17}/> : item.status === 'LOCKED' ? <LockKeyhole size={15}/> : item.order}</span><div><b>Level {item.order} · {item.title}</b><small>{item.status === 'LOCKED' ? `Complete Level ${item.order - 1} checkpoint` : item.status}</small></div></button>)}<div className="yt-final"><Trophy size={19}/><b>Final Challenge</b><small>{completed === path.levels.length ? 'Unlocked' : 'Complete every level'}</small></div></aside><main className="yt-lesson-area">{level ? <Lesson level={level} step={step} setStep={setStep} answer={answer} setAnswer={setAnswer} submit={submitCheckpoint} feedback={feedback} busy={busy} sourceUrl={sourceUrl}/> : <div className="panel yt-empty"><Sparkles size={26}/><h2>Choose Level 1 to begin</h2><p>RISE will teach one transcript-derived concept at a time.</p></div>}</main><aside className="panel yt-study-notes"><p className="eyebrow">RISE NOTES</p>{path.cumulative_notes ? <pre>{path.cumulative_notes}</pre> : <p className="muted">Complete a level to add concise lesson notes here.</p>}</aside></div></div>
}

function ProcessingView({ step, finishing }) {
  const stages = ['Video selected', 'Understanding the lecture...', 'Breaking it into learning levels...', 'Creating your personalized RISE path...', 'Preparing your first lesson...']
  return <div className="yt-processing"><div className="yt-processing-ring"><CirclePlay size={28}/></div><p className="eyebrow">BUILDING YOUR PATH</p><div className="yt-processing-stages" aria-live="polite"><strong>✓ {stages[0]}</strong>{stages.slice(1).map((stage, index) => <span className={index + 1 <= step ? 'active' : ''} key={stage}>→ {stage}</span>)}</div><h1>{finishing ? 'Your learning path is ready' : stages[Math.max(1, step)]}</h1><div className={`yt-progress ${finishing ? 'complete' : 'indeterminate'}`}><span/></div>{finishing && <strong>100%</strong>}<p>{finishing ? 'Opening your first learning map...' : 'RISE is shaping the lecture into a clear, focused learning journey.'}</p></div>
}

function Lesson({ level, step, setStep, answer, setAnswer, submit, feedback, busy, sourceUrl }) {
  const lessonSteps = level.lesson_steps || []
  const current = lessonSteps[Math.min(step, lessonSteps.length - 1)] || { heading: level.title, explanation: level.description, example: level.notes, analogy: '' }
  if (step < 2) return <section className="yt-lesson panel"><div className="yt-level-head"><span>LEVEL {level.order}</span><small>STEP {step + 1} OF 4</small></div><div className="yt-lesson-progress"><span className={step >= 0 ? 'done' : ''}>Learn</span><span className={step >= 1 ? 'done' : ''}>Understand</span><span>Try</span><span>Complete</span></div><h2>{current.heading}</h2><p className="yt-teaching-copy">{current.explanation}</p><div className="yt-example"><b>Example</b><p>{current.example}</p></div>{current.analogy && <div className="yt-analogy"><b>Think of it as...</b><p>{current.analogy}</p></div>}<a className="yt-source-link" href={sourceUrl} target="_blank" rel="noreferrer"><CirclePlay size={15}/> Watch source at {Math.floor(level.start_seconds/60)}:{String(Math.floor(level.start_seconds % 60)).padStart(2, '0')}</a><button className="button button-primary" onClick={() => setStep(step + 1)}>Got it <ChevronRight size={15}/></button></section>
  if (step === 2) return <section className="yt-lesson panel"><div className="yt-level-head"><span>LEVEL {level.order}</span><small>STEP 3 OF 4 · TRY</small></div><h2>Check your understanding</h2><p className="muted">Answer from the lesson, then RISE will explain why.</p><div className="yt-checkpoint"><h3>{level.checkpoint.question}</h3>{level.checkpoint.options?.length ? level.checkpoint.options.map(option => <button className={answer === option ? 'selected' : ''} onClick={() => setAnswer(option)} key={option}>{option}</button>) : <textarea rows={4} value={answer} onChange={event => setAnswer(event.target.value)} placeholder="Explain your answer..."/>}<button className="button button-primary" onClick={submit} disabled={busy || !answer.trim()}>Check answer</button>{feedback && <div className={feedback.correct ? 'yt-feedback correct' : 'yt-feedback incorrect'}><strong>{feedback.correct ? '+25 XP · Level complete' : 'Not yet · Try again'}</strong><p>{feedback.feedback}</p>{!feedback.correct && <a href={sourceUrl} target="_blank" rel="noreferrer">Revisit the source section</a>}</div>}</div></section>
  return <section className="yt-lesson yt-level-complete panel"><Trophy size={42}/><p className="eyebrow">LEVEL COMPLETE</p><h2>{level.title}</h2><strong>⭐⭐⭐</strong><p className="yt-xp-reward">+25 XP</p><p>You learned this section from the lecture transcript.</p><button className="button button-primary" onClick={() => window.dispatchEvent(new CustomEvent('rise:learning-map', { detail: { completedOrder: level.order } }))}>Continue to learning map <ChevronRight size={15}/></button></section>
}

function FinalChallenge({ path, challenge, answers, setAnswers, submit, busy }) {
  return <div className="yt-final-challenge"><header><Trophy size={35}/><p className="eyebrow">FINAL CHALLENGE</p><h1>{path.title}</h1><p>Answer from the complete learning path. Your mastery score is based on this assessment.</p></header>{challenge.questions.map((question, index) => <section className="panel yt-final-question" key={question.id}><span>{index + 1}</span><div><small>{question.level_title}</small><h3>{question.question}</h3>{question.options?.length ? question.options.map(option => <button className={answers[question.id] === option ? 'selected' : ''} onClick={() => setAnswers(current => ({...current, [question.id]: option}))} key={option}>{option}</button>) : <textarea rows={3} value={answers[question.id] || ''} onChange={event => setAnswers(current => ({...current, [question.id]: event.target.value}))} placeholder="Your answer..."/>}</div></section>)}<button className="button button-primary" onClick={submit} disabled={busy || Object.keys(answers).length !== challenge.questions.length}>{busy ? 'Evaluating...' : 'Complete final challenge'}</button></div>
}

export default function LearnFromYouTube() { return <><TutorTabs/><LearnFromYouTubeContent/></> }
