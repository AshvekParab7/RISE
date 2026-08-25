import { useEffect, useMemo, useRef, useState } from 'react'
import { Check, LockKeyhole, Sparkles, Trophy, Zap } from 'lucide-react'
import './learningMap.css'
import './notesScroll.css'

const starsFor = count => count ? '★'.repeat(count) + '☆'.repeat(3 - count) : '☆☆☆'
const pointFor = (index, total) => ({ x: 50 + Math.sin(index * 1.73 + total * .18) * 24, y: 100 + index * 145 })
const curvePath = points => points.reduce((path, point, index) => {
  if (!index) return `M ${point.x} ${point.y}`
  const previous = points[index - 1]
  const middleY = (previous.y + point.y) / 2
  return `${path} C ${previous.x} ${middleY}, ${point.x} ${middleY}, ${point.x} ${point.y}`
}, '')
const segmentPath = (from, to) => `M ${from.x} ${from.y} C ${from.x} ${(from.y + to.y) / 2}, ${to.x} ${(from.y + to.y) / 2}, ${to.x} ${to.y}`

export default function LearningMap({ path, transition, onTransitionEnd, onSelect, onFinalChallenge, onBack }) {
  const [hovered, setHovered] = useState(null)
  const [travelling, setTravelling] = useState(false)
  const [unlocked, setUnlocked] = useState(false)
  const mapRef = useRef(null)
  const nodesRef = useRef({})
  const completed = path.levels.filter(level => level.status === 'COMPLETED').length
  const stars = path.levels.reduce((total, level) => total + (level.best_stars || 0), 0)
  const current = path.levels.find(level => level.order === path.current_level_order) || path.levels.find(level => level.status !== 'COMPLETED') || path.levels[0]
  const points = useMemo(() => path.levels.map((_level, index) => pointFor(index, path.levels.length)), [path.levels.length])
  const fullPath = useMemo(() => curvePath(points), [points])
  const mapHeight = Math.max(440, points.length * 145 + 145)
  const transitionStartOrder = Number(transition?.completedOrder || 0)
  const transitionEndOrder = transitionStartOrder + 1
  const transitionFrom = transitionStartOrder > 0 ? points[transitionStartOrder - 1] : null
  const transitionTo = transitionEndOrder <= points.length ? points[transitionEndOrder - 1] : null
  const visibleCompleted = travelling && transition?.completedOrder ? Math.max(0, completed - 1) : completed
  const completionRatio = path.levels.length ? visibleCompleted / path.levels.length : 0
  const completedPath = useMemo(() => curvePath(points.slice(0, Math.max(1, visibleCompleted))), [points, visibleCompleted])

  useEffect(() => {
    if (!transition || !transitionFrom || !transitionTo) return undefined
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (reduced) { setUnlocked(true); onTransitionEnd?.(); return undefined }
      setTravelling(true); setUnlocked(false)
      mapRef.current?.querySelector('.map-travel-particle animateMotion')?.setAttribute('dur', '4s')
      const unlockTimer = setTimeout(() => { setTravelling(false); setUnlocked(true); nodesRef.current[transitionEndOrder]?.scrollIntoView({ behavior: 'smooth', block: 'center' }) }, 4100)
      const endTimer = setTimeout(() => { setUnlocked(false); onTransitionEnd?.() }, 6000)
    return () => { clearTimeout(unlockTimer); clearTimeout(endTimer) }
  }, [transition?.completedOrder])

  useEffect(() => { if (transition || !current || !nodesRef.current[current.order]) return; nodesRef.current[current.order].scrollIntoView({ behavior: 'smooth', block: 'center' }) }, [transition, current?.order])
  useEffect(() => { const travelled = mapRef.current?.querySelector('.map-trail-completed'); if (travelled) { travelled.setAttribute('d', completedPath); travelled.style.clipPath = 'none' } }, [completedPath])
  useEffect(() => {
    const svg = mapRef.current?.querySelector('.map-path-lines')
    if (!svg) return undefined
    svg.querySelector('.map-idle-particle')?.remove()
    if (travelling || !current || current.order >= path.levels.length) return undefined
    const from = points[current.order - 1]
    const to = points[current.order]
    if (!from || !to) return undefined
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle')
    circle.setAttribute('class', 'map-idle-particle'); circle.setAttribute('r', '1.5')
    const motion = document.createElementNS('http://www.w3.org/2000/svg', 'animateMotion')
    motion.setAttribute('dur', '3.5s'); motion.setAttribute('repeatCount', 'indefinite'); motion.setAttribute('path', segmentPath(from, to))
    circle.appendChild(motion); svg.appendChild(circle)
    return () => circle.remove()
  }, [travelling, current?.order, path.levels.length, points])
  useEffect(() => {
    const node = mapRef.current?.querySelector('.map-final-node')
    if (!node) return undefined
    node.setAttribute('role', 'button')
    node.setAttribute('tabindex', completed === path.levels.length ? '0' : '-1')
    const activate = () => { if (completed === path.levels.length) onFinalChallenge?.() }
    const keyboard = event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); activate() } }
    node.addEventListener('click', activate); node.addEventListener('keydown', keyboard)
    return () => { node.removeEventListener('click', activate); node.removeEventListener('keydown', keyboard) }
  }, [completed, path.levels.length, onFinalChallenge])
  useEffect(() => {
    const stats = document.querySelector('.learning-map-stats')
    if (!stats || stats.querySelector('.notes-button')) return undefined
    const notes = path.study_notes?.length ? path.study_notes : path.levels.map(level => ({ order: level.order, title: level.title, key_concepts: level.key_concepts, notes: level.notes, lesson_steps: level.lesson_steps }))
    const button = document.createElement('button')
    button.className = 'notes-button'; button.type = 'button'; button.textContent = '📖 View Notes'
    const modal = document.createElement('div'); modal.className = 'notes-overlay'; modal.hidden = true
    modal.innerHTML = `<section class="notes-panel" role="dialog" aria-modal="true" aria-label="Study notes"><header><div><p class="eyebrow">RISE STUDY NOTES</p><h2>Notes from this video</h2></div><button class="notes-close" type="button" aria-label="Close notes">×</button></header><div class="notes-body"><aside class="notes-toc"><input class="notes-search" type="search" placeholder="Search notes" aria-label="Search notes"/> <div class="notes-levels"></div></aside><article class="notes-content"></article></div></section>`
    const levels = modal.querySelector('.notes-levels'); const content = modal.querySelector('.notes-content'); const search = modal.querySelector('.notes-search')
    const safe = value => String(value || '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]))
    const render = selected => { const note = notes.find(item => item.order === selected) || notes[0]; if (!note) return; levels.innerHTML = notes.filter(item => `${item.title} ${item.notes} ${(item.key_concepts || []).join(' ')}`.toLowerCase().includes(search.value.toLowerCase())).map(item => `<button class="notes-level ${item.order === note.order ? 'active' : ''}" data-order="${item.order}">LEVEL ${item.order}<strong>${safe(item.title)}</strong></button>`).join(''); content.innerHTML = `<p class="eyebrow">LEVEL ${note.order}</p><h3>${safe(note.title)}</h3>${note.key_concepts?.length ? `<h4>Key concepts</h4><div class="notes-tags">${note.key_concepts.map(concept => `<span>${safe(concept)}</span>`).join('')}</div>` : ''}<h4>Study notes</h4><div class="notes-copy">${safe(note.notes).replace(/\n/g, '<br/>')}</div>${(note.lesson_steps || []).map(step => `<section><h4>${safe(step.heading)}</h4><p>${safe(step.explanation)}</p>${step.example ? `<div class="notes-code"><code>${safe(step.example)}</code><button class="copy-note" data-code="${safe(step.example)}" type="button">Copy</button></div>` : ''}</section>`).join('')}`; levels.querySelectorAll('.notes-level').forEach(item => item.addEventListener('click', () => render(Number(item.dataset.order)))); content.querySelectorAll('.copy-note').forEach(item => item.addEventListener('click', () => navigator.clipboard?.writeText(item.dataset.code))) }
    const close = () => { modal.hidden = true }; button.addEventListener('click', () => { modal.hidden = false; render(notes[0]?.order) }); modal.querySelector('.notes-close').addEventListener('click', close); modal.addEventListener('click', event => { if (event.target === modal) close() }); search.addEventListener('input', () => render(notes[0]?.order)); stats.prepend(button); document.querySelector('.learning-map-screen')?.append(modal)
    return () => { button.remove(); modal.remove() }
  }, [path.id])
  useEffect(() => {
    const preventBackgroundScroll = event => {
      const modal = document.querySelector('.notes-overlay')
      if (!modal || modal.hidden || modal.contains(event.target)) return
      event.preventDefault()
    }
    document.addEventListener('wheel', preventBackgroundScroll, { passive: false })
    document.addEventListener('touchmove', preventBackgroundScroll, { passive: false })
    return () => { document.removeEventListener('wheel', preventBackgroundScroll); document.removeEventListener('touchmove', preventBackgroundScroll) }
  }, [])

  return <div className="learning-map-screen"><header className="learning-map-header"><button className="text-button" onClick={onBack}>← Learning paths</button><div><p className="eyebrow">LEARNING JOURNEY</p><h1>{path.title}</h1><p className="muted">Your next lesson is earned from a real checkpoint.</p></div><div className="learning-map-stats"><span>LEVEL {Math.min(completed + 1, path.levels.length)} / {path.levels.length}</span><b>{Math.round(completionRatio * 100)}%</b><i><em style={{width:`${completionRatio * 100}%`}}/></i><small>★ {stars} stars · <Zap size={12}/> {path.xp} XP</small></div></header><div className="learning-map-world" ref={mapRef}><div className="map-cloud cloud-one"/><div className="map-cloud cloud-two"/><div className="map-orbit orbit-one"/><svg className={`map-path-lines ${travelling ? 'travelling' : ''}`} viewBox={`0 0 100 ${mapHeight}`} preserveAspectRatio="none"><path className="map-trail-future" d={fullPath}/><path className="map-trail-completed" d={fullPath} style={{clipPath:`inset(0 0 ${Math.max(0, 100 - completionRatio * 100)}% 0)`}}/>{travelling && transitionFrom && transitionTo && <><path className="map-trail-travel" d={segmentPath(transitionFrom, transitionTo)}/><circle className="map-travel-particle" r="1.8"><animateMotion dur="1.5s" path={segmentPath(transitionFrom, transitionTo)} fill="freeze"/></circle></>}</svg><div className="map-nodes" style={{minHeight:mapHeight}}>{path.levels.map((level, index) => { const position = points[index]; const isLocked = level.status === 'LOCKED'; const isCurrent = current?.id === level.id && !isLocked; const isCompleted = level.status === 'COMPLETED'; const isUnlocking = unlocked && transition?.completedOrder + 1 === level.order; return <button id={`learning-map-level-${level.order}`} ref={node => { if (node) nodesRef.current[level.order] = node }} className={`map-node ${level.status.toLowerCase()} ${isCurrent ? 'current' : ''} ${isUnlocking ? 'unlocking' : ''}`} style={{left:`${position.x}%`,top:position.y}} onClick={() => !isLocked && onSelect(level)} onMouseEnter={() => setHovered(level.id)} onMouseLeave={() => setHovered(null)} onFocus={() => setHovered(level.id)} onBlur={() => setHovered(null)} key={level.id} aria-label={`${level.title}, ${level.status}`}><span className="map-node-circle">{isCompleted ? <Check size={24}/> : isLocked ? <LockKeyhole size={19}/> : level.order}</span><strong>{level.title}</strong><small>{isCompleted ? starsFor(level.best_stars) : isCurrent ? 'CONTINUE LEARNING' : isLocked ? `Complete Level ${level.order - 1}` : 'START LEVEL'}</small>{isCurrent && <b className="map-current-badge"><Sparkles size={12}/> CURRENT</b>}{isUnlocking && <b className="map-unlocked-badge">🔓 UNLOCKED</b>}{hovered === level.id && <span className="map-node-popover"><b>Level {level.order}</b><strong>{level.title}</strong><small>{level.estimated_minutes} min · best {level.best_score || 0}% · {level.best_stars || 0}/3 stars</small>{isLocked ? `Complete Level ${level.order - 1} to unlock` : isCompleted ? 'Review lesson' : 'Open lesson'}</span>}</button> })}<div className="map-final-node" style={{top:mapHeight - 72,left:'50%'}}><Trophy size={22}/><b>FINAL CHALLENGE</b><small>{completed === path.levels.length ? 'READY' : 'Complete every level'}</small></div></div></div><footer className="learning-map-footer"><span>🎯 Next: <b>{current?.title || 'Final challenge'}</b></span><span><Zap size={14}/> XP is earned from real progress</span></footer></div>
}
