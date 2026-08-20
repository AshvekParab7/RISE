import { useState } from 'react'
import { Send, Sparkles, Upload } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { createPortal } from 'react-dom'
import PdfViewer from './PdfViewer'
import { smartTutorService } from './smartTutorService'
import './markdown.css'
import './flashcards.css'
import './flashcard-size.css'
import './mcqs.css'
import './clay-tutor.css'
import './tutor-layout.css'

const MAX_PDF_SIZE = 20 * 1024 * 1024

const getFlashcardRequest = text => {
  if (!/\bflashcards?\b/i.test(text)) return null
  const count = Math.min(Number(text.match(/\b(\d+)\s+flashcards?\b/i)?.[1] || 3), 20)
  const topic = text.replace(/\b(generate|create|make|give)\b/i, '').replace(/\b\d+\s+flashcards?\b/i, '').replace(/\bflashcards?\b/i, '').replace(/^\s*(on|about|for)\s+/i, '').trim()
  return topic ? { topic, count } : null
}

const getMCQRequest = text => {
  if (!/\bmcqs?\b|multiple[- ]choice/i.test(text)) return null
  const count = Math.min(Number(text.match(/\b(\d+)\s+(?:mcqs?|multiple[- ]choice)/i)?.[1] || 4), 20)
  const topic = text.replace(/\b(generate|create|make|give)\b/i, '').replace(/\b\d+\s+(?:mcqs?|multiple[- ]choice questions?)\b/i, '').replace(/\bmcqs?\b|\bmultiple[- ]choice questions?\b/i, '').replace(/^\s*(on|about|for)\s+/i, '').trim()
  return topic ? { topic, count } : null
}

function FlashcardModal({ cards, topic, onClose }) {
  return createPortal(<div className="flashcard-modal-backdrop" role="presentation" onClick={onClose}><section className="flashcard-modal" role="dialog" aria-modal="true" aria-labelledby="flashcard-title" onClick={event => event.stopPropagation()}><div className="flashcard-modal-head"><div><p className="eyebrow">SMART TUTOR</p><h2 id="flashcard-title">Flashcards on {topic}</h2><small>Click a card to flip it and reveal the answer.</small></div><button className="flashcard-close" onClick={onClose} aria-label="Close flashcards">×</button></div><div className="flashcard-grid">{cards.map((card, index) => <Flashcard key={`${card.question}-${index}`} card={card} index={index}/>)}</div></section></div>, document.body)
}

function Flashcard({ card, index }) {
  const [flipped, setFlipped] = useState(false)
  return <button className={`flashcard ${flipped ? 'is-flipped' : ''}`} onClick={() => setFlipped(value => !value)} aria-label={`${flipped ? 'Show question' : 'Reveal answer'} for flashcard ${index + 1}`}><span className="flashcard-inner"><span className="flashcard-face flashcard-front"><small>QUESTION {index + 1}</small><strong>{card.question}</strong><em>Click to reveal answer</em></span><span className="flashcard-face flashcard-back"><small>ANSWER</small><strong><ReactMarkdown remarkPlugins={[remarkGfm]}>{card.answer}</ReactMarkdown></strong><em>Click to see question</em></span></span></button>
}

function MCQModal({ questions, topic, onClose }) {
  const [answers, setAnswers] = useState({})
  return createPortal(<div className="mcq-modal-backdrop" role="presentation" onClick={onClose}><section className="mcq-modal" role="dialog" aria-modal="true" aria-labelledby="mcq-title" onClick={event => event.stopPropagation()}><div className="flashcard-modal-head"><div><p className="eyebrow">SMART TUTOR</p><h2 id="mcq-title">MCQs on {topic}</h2><small>Select an option to check your answer.</small></div><button className="flashcard-close" onClick={onClose} aria-label="Close MCQs">×</button></div><div className="mcq-list">{questions.map((question, index) => { const selected = answers[index]; const answered = selected !== undefined; return <article className="mcq-item" key={`${question.question}-${index}`}><small>QUESTION {index + 1}</small><h3>{question.question}</h3><div className="mcq-options">{question.options.map(option => <button className={answered ? option === question.correct_answer ? 'mcq-option correct' : option === selected ? 'mcq-option incorrect' : 'mcq-option' : 'mcq-option'} onClick={() => !answered && setAnswers(value => ({ ...value, [index]: option }))} disabled={answered} key={option}>{option}{answered && option === question.correct_answer && <b> ✓</b>}{answered && option === selected && option !== question.correct_answer && <b> ✕</b>}</button>)}</div>{answered && <p className={`mcq-feedback ${selected === question.correct_answer ? 'correct' : 'incorrect'}`}>{selected === question.correct_answer ? 'Correct!' : 'Not quite.'} {question.explanation}</p>}</article> })}</div></section></div>, document.body)
}

function TutorMessage({ message, onCitation }) {
  const [showFlashcards, setShowFlashcards] = useState(false)
  const [showMCQs, setShowMCQs] = useState(false)
  return <div className={`message ${message.role}`}><div className="message-bubble"><ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>{message.flashcards?.length > 0 && <><button className="launch-flashcards" onClick={() => setShowFlashcards(true)}>Launch Flashcards</button>{showFlashcards && <FlashcardModal cards={message.flashcards} topic={message.topic} onClose={() => setShowFlashcards(false)}/>}</>}{message.mcqs?.length > 0 && <><button className="launch-flashcards launch-mcqs" onClick={() => setShowMCQs(true)}>Launch MCQs</button>{showMCQs && <MCQModal questions={message.mcqs} topic={message.topic} onClose={() => setShowMCQs(false)}/>}</>}{message.sources?.length > 0 && <div className="citation-list">{message.sources.map((source, sourceIndex) => <button onClick={() => onCitation(source)} title={source.quote} key={source.chunk_id}><sup>{sourceIndex + 1}</sup> Page {source.page}: “{source.quote}”</button>)}</div>}</div></div>
}

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
    if (!text || busy) return
    setInput('')
    setBusy(true)
    setError('')
    setMessages(items => [...items, { role: 'user', content: text }])
    const mcqRequest = getMCQRequest(text)
    if (mcqRequest) {
      try {
        const response = await smartTutorService.generateMCQs({ ...mcqRequest, file })
        setMessages(items => [...items, { role: 'assistant', content: `I created **${response.mcqs.length} MCQs** on **${response.topic}**.`, mcqs: response.mcqs, topic: response.topic }])
      } catch (reason) {
        setError(reason.message)
      } finally { setBusy(false) }
      return
    }
    const flashcardRequest = getFlashcardRequest(text)
    if (flashcardRequest) {
      try {
        const response = await smartTutorService.generateFlashcards({ ...flashcardRequest, file })
        setMessages(items => [...items, { role: 'assistant', content: `I created **${response.flashcards.length} flashcards** on **${response.topic}**.`, flashcards: response.flashcards, topic: response.topic }])
      } catch (reason) {
        setError(reason.message)
      } finally { setBusy(false) }
      return
    }
    if (!file) { setBusy(false); setError('Upload a PDF before asking a question.'); return }
    const payload = new FormData()
    payload.append('message', text)
    payload.append('file', file)
    try {
      const response = await smartTutorService.ask(payload)
      setMessages(items => [...items, { role: 'assistant', content: response.answer, sources: response.sources || [] }])
    } catch (reason) {
      setError(reason.message)
      setMessages(items => [...items, { role: 'assistant', content: 'I could not read that part of the PDF right now. Please try again.' }])
    } finally { setBusy(false) }
  }

  if (!file) return <div className="tutor-upload-page"><div className="tutor-upload-card"><div className="tutor-upload-icon"><Upload size={28}/></div><p className="eyebrow">PDF-FIRST TUTOR</p><h1>Start with your study material.</h1><p>Upload a text-based PDF to open RISE Tutor. Every answer will be grounded only in that document.</p>{error && <p className="api-error">{error}</p>}<label className="button button-primary tutor-upload-button"><Upload size={16}/>Upload PDF<input hidden type="file" accept="application/pdf,.pdf" onChange={chooseFile}/></label><small>PDF only, up to 20 MB</small></div></div>

  return <div className="tutor-page"><div className="tutor-workspace"><PdfViewer file={file} citation={activeCitation}/><section className="chat panel"><div className="chat-head"><div className="tutor-avatar"><Sparkles size={18}/></div><div><b>RISE Tutor</b><small>Grounded only in {file.name}</small></div><label className="button tutor-replace"><Upload size={15}/>Replace PDF<input hidden type="file" accept="application/pdf,.pdf" onChange={chooseFile}/></label><span className="online">PDF ready</span></div><div className="messages">{messages.map((message, index) => <TutorMessage key={index} message={message} onCitation={setActiveCitation}/>)}{busy && <div className="message assistant"><div className="message-bubble typing">Reading the PDF...</div></div>}</div><div className="quick-actions">{['Summarize this PDF', 'Explain the key concepts', 'Create revision questions', 'What should I study first?'].map(action => <button key={action} onClick={() => ask(action)}>{action}</button>)}</div>{error && <p className="api-error tutor-error">{error}</p>}<div className="chat-input"><input aria-label="Ask about the PDF" value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => event.key === 'Enter' && ask()} placeholder="Ask a question about this PDF..."/><button onClick={() => ask()} disabled={busy || !input.trim()} aria-label="Send message"><Send size={17}/></button></div></section></div></div>
}
