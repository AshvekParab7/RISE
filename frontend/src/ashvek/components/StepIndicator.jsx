export default function StepIndicator({ step, status = 'ACTIVE' }) {
  const steps = ['Concept', 'Example', 'Check understanding', 'Practice', 'Mastery']
  return <div className="ashvek-stepper" aria-label="Tutor progress">{steps.map((label, index) => <div className={`ashvek-step ${index + 1 <= step ? 'active' : ''}`} key={label}><span>{index + 1}</span><small>{label}</small></div>)}<em>{status === 'COMPLETED' ? 'Complete' : `Step ${Math.min(step, steps.length)} of ${steps.length}`}</em></div>
}
