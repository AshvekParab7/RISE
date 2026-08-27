import { Link, useLocation } from 'react-router-dom'

export default function TutorTabs() {
  const location = useLocation()
  const youtube = location.pathname.startsWith('/learn/youtube')
  return <nav className="tutor-tabs" aria-label="Tutor tools"><Link className={!youtube ? 'active' : ''} to="/tutor">RISE Tutor</Link><Link className={youtube ? 'active' : ''} to="/learn/youtube">Learn from YouTube</Link></nav>
}
