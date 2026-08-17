import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Check, ChevronRight, Clock3, Trophy } from 'lucide-react'
import { mockQuiz } from './data/mockData'

const questions = [...mockQuiz, { question: 'Which protocol guarantees ordered delivery?', options: ['UDP', 'TCP', 'IP', 'ARP'], answer: 1 }, { question: 'What does a three-way handshake establish?', options: ['A TCP connection', 'A DNS record', 'A subnet', 'A firewall rule'], answer: 0 }, { question: 'Which metric commonly rises as congestion increases?', options: ['Round-trip time', 'Screen brightness', 'Disk capacity', 'Frame size'], answer: 0 }, { question: 'Which layer handles end-to-end transport?', options: ['Application', 'Transport', 'Network', 'Physical'], answer: 1 }, { question: 'What does HTTP primarily transfer?', options: ['Web resources', 'MAC addresses', 'Radio signals', 'Disk sectors'], answer: 0 }, { question: 'Which mechanism regulates sender speed?', options: ['Flow control', 'DNS lookup', 'Packet framing', 'Port scanning'], answer: 0 }, { question: 'What identifies an application endpoint?', options: ['Port number', 'Subnet mask', 'Frame checksum', 'Cable type'], answer: 0 }, { question: 'Which protocol is connectionless?', options: ['TCP', 'UDP', 'TLS', 'HTTP'], answer: 1 }]

export default function TestRunner() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [current, setCurrent] = useState(0)
  const [answers, setAnswers] = useState({})
  const [seconds, setSeconds] = useState(15 * 60)
  const [submitted, setSubmitted] = useState(false)
  useEffect(() => { if (submitted || seconds === 0) return undefined; const timer = setInterval(() => setSeconds(value => value - 1), 1000); return () => clearInterval(timer) }, [seconds, submitted])
  const question = questions[current]
  const select = option => setAnswers(value => ({ ...value, [current]: option }))
  const submit = () => setSubmitted(true)
  const score = questions.reduce((total, item, index) => total + (answers[index] === item.answer ? 1 : 0), 0)
  const mins = String(Math.floor(seconds / 60)).padStart(2, '0')
  const secs = String(seconds % 60).padStart(2, '0')
  if (submitted) return <div className="test-runner"><button className="back-link" onClick={() => navigate('/tests')}><ArrowLeft size={15}/> Back to tests</button><div className="knowledge-result panel"><div className="result-mark"><Trophy size={25}/></div><p className="eyebrow">TEST COMPLETE · {id || 'TRANSPORT-LAYER'}</p><h1>{score} / {questions.length}</h1><h2>Knowledge Score <strong>{Math.round(score / questions.length * 100)}%</strong></h2><div className="score-line"><span>Mastery<br/><strong>52% → 60%</strong></span><span>Knowledge growth<br/><strong>+8%</strong></span></div><div className="result-columns"><div><b>Strong areas</b><span><Check size={14}/> TCP</span><span><Check size={14}/> HTTP</span></div><div><b>Weak areas</b><span>Congestion Control</span><span>Flow Control</span></div></div><button className="button button-primary" onClick={() => navigate('/planner')}>Update My RISE Plan <ChevronRight size={16}/></button></div></div>
  return <div className="test-runner"><button className="back-link" onClick={() => navigate('/tests')}><ArrowLeft size={15}/> Exit test</button><div className="test-runner-head"><div><p className="eyebrow">COMPUTER NETWORKS · TRANSPORT LAYER</p><h1>Transport Layer Test</h1></div><span className="test-timer"><Clock3 size={15}/> {mins}:{secs}</span></div><div className="test-progress"><span style={{ width: `${(current + 1) / questions.length * 100}%` }} /></div><div className="runner-question panel"><div className="quiz-top"><span>QUESTION {current + 1} / {questions.length}</span><span>Medium</span></div><h2>{question.question}</h2><div className="options">{question.options.map((option, index) => <button className={answers[current] === index ? 'selected' : ''} onClick={() => select(index)} key={option}><span>{String.fromCharCode(65 + index)}</span>{option}</button>)}</div><div className="runner-actions"><button className="button" disabled={current === 0} onClick={() => setCurrent(value => value - 1)}>Previous</button>{current === questions.length - 1 ? <button className="button button-primary" onClick={submit}>Submit test <ChevronRight size={16}/></button> : <button className="button button-primary" onClick={() => setCurrent(value => value + 1)}>Next <ChevronRight size={16}/></button>}</div></div></div>
}
