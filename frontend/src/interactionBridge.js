import { workspaceSeed } from './data/workspace'

const resultsFor = query => {
  const value = query.trim().toLowerCase()
  if (!value) return []
  const results = [
    ...workspaceSeed.subjects.map(item => ({ label: item.name, detail: 'Subject', path: `/subjects/${item.id}` })),
    ...workspaceSeed.notes.map(item => ({ label: item.title, detail: `${item.subject} · ${item.source}`, path: '/notes' })),
    ...workspaceSeed.tasks.map(item => ({ label: item.title, detail: `${item.subject} · ${item.source}`, path: '/tasks' })),
    ...workspaceSeed.topics.map(item => ({ label: item.name, detail: 'Syllabus topic', path: `/subjects/${item.subjectId}` })),
  ]
  return results.filter(item => `${item.label} ${item.detail}`.toLowerCase().includes(value)).slice(0, 8)
}

const showSearch = () => {
  if (document.querySelector('.search-overlay')) return
  const overlay = document.createElement('div')
  overlay.className = 'search-overlay'
  overlay.innerHTML = '<div class="search-dialog" role="dialog" aria-label="Search RISE"><div class="search-dialog-input"><span>⌕</span><input autofocus placeholder="Search subjects, notes, tasks, and topics..." /></div><div class="search-results"></div><button class="search-close">Close</button></div>'
  document.body.appendChild(overlay)
  const input = overlay.querySelector('input')
  const results = overlay.querySelector('.search-results')
  const render = () => { const matches = resultsFor(input.value); results.innerHTML = matches.length ? matches.map(item => `<button data-path="${item.path}"><b>${item.label}</b><small>${item.detail}</small></button>`).join('') : '<p>Start typing to search your academic world.</p>' }
  input.addEventListener('input', render)
  overlay.addEventListener('click', event => { const result = event.target.closest('[data-path]'); if (result) window.location.assign(result.dataset.path); if (event.target === overlay || event.target.closest('.search-close')) overlay.remove() })
  render(); input.focus()
}

document.addEventListener('click', event => {
  const search = event.target.closest('.search')
  if (search) showSearch()
  const action = event.target.closest('.note-row .button')
  if (action) {
    const title = action.closest('.note-row')?.querySelector('b')?.textContent || 'this resource'
    if (action.textContent.trim() === 'AI') window.location.assign('/tutor')
  }
}, true)
