export default function SourceList({ sources = [] }) {
  if (!sources.length) return null
  return <div className="ashvek-sources"><b>Sources</b>{sources.map(source => <span key={source.resource_id}>• {source.title}</span>)}</div>
}
