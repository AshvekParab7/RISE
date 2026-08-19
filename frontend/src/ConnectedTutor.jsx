import { useState } from 'react'
import { Send, Sparkles, Upload } from 'lucide-react'
import PdfViewer from './PdfViewer'
import { aiService } from './services/aiService'

const MAX_PDF_SIZE = 20 * 1024 * 1024

export default function ConnectedTutor() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [file, setFile] = useState(null)
  const [activeCitation, setActiveCitation] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const chooseFile = event => {
    const selected = event.target.files?.[0]
    if (!selected) return
    if (selected.type !== 'application/pdf' || !selected.name.toLowerCase().endsWith('.pdf')) { setError('Choose a PDF file.'); return }
    if (selected.size > MAX_PDF_SIZE) { setError('PDF must be 20 MB or smaller.'); return }
    setFile(selected)
    setActiveCitation(null)
    setMessages([{ role: 'assistant', content: `I have opened ${selected.name}. Ask me anything from this study material.` }])
    setError('')
  }

  const ask = async prompt => {
    const text = prompt || input.trim()
    if (!file || !text || busy) return
    setInput('')
    setBusy(true)
    setError('')
    setMessages(items => [...items, { role: 'user', content: text }])
    const payload = new FormData()
    payload.append('message', text)
    payload.append('file', file)
    try {
      const response = await aiService.tutor(payload)
      setMessages(items => [...items, { role: 'assistant', content: response.answer, sources: response.sources || [] }])
    } catch (reason) {
      setError(reason.message)
      setMessages(items => [...items, { role: 'assistant', content: 'I could not read that part of the PDF right now. Please try again.' }])
    } finally { setBusy(false) }
  }

  if (!file) return <div className="tutor-upload-page"><div className="tutor-upload-card"><div className="tutor-upload-icon"><Upload size={28}/></div><p className="eyebrow">PDF-FIRST TUTOR</p><h1>Start with your study material.</h1><p>Upload a text-based PDF to open RISE Tutor. Every answer will be grounded only in that document.</p>{error && <p className="api-error">{error}</p>}<label className="button button-primary tutor-upload-button"><Upload size={16}/>Upload PDF<input hidden type="file" accept="application/pdf,.pdf" onChange={chooseFile}/></label><small>PDF only, up to 20 MB</small></div></div>

  return <div className="tutor-page"><div className="tutor-workspace"><PdfViewer file={file} citation={activeCitation}/><section className="chat panel"><div className="chat-head"><div className="tutor-avatar"><Sparkles size={18}/></div><div><b>RISE Tutor</b><small>Grounded only in {file.name}</small></div><label className="button tutor-replace"><Upload size={15}/>Replace PDF<input hidden type="file" accept="application/pdf,.pdf" onChange={chooseFile}/></label><span className="online">PDF ready</span></div><div className="messages">{messages.map((message, index) => <div className={`message ${message.role}`} key={index}><div className="message-bubble">{message.content}{message.sources?.length > 0 && <div className="citation-list">{message.sources.map((source, sourceIndex) => <button onClick={() => setActiveCitation(source)} className={activeCitation?.chunk_id === source.chunk_id ? 'active' : ''} title={source.quote} key={source.chunk_id}><sup>{sourceIndex + 1}</sup> Page {source.page}: “{source.quote}”</button>)}</div>}</div></div>)}{busy && <div className="message assistant"><div className="message-bubble typing">Reading the PDF...</div></div>}</div><div className="quick-actions">{['Summarize this PDF', 'Explain the key concepts', 'Create revision questions', 'What should I study first?'].map(action => <button key={action} onClick={() => ask(action)}>{action}</button>)}</div>{error && <p className="api-error tutor-error">{error}</p>}<div className="chat-input"><input aria-label="Ask about the PDF" value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => event.key === 'Enter' && ask()} placeholder="Ask a question about this PDF..."/><button onClick={() => ask()} disabled={busy || !input.trim()} aria-label="Send message"><Send size={17}/></button></div></section></div></div>
}
