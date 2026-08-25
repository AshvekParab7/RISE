import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  CalendarDays,
  Check,
  ChevronDown,
  CircleAlert,
  Clock3,
  FileText,
  ListChecks,
  RefreshCw,
  Sparkles,
  Target,
  Upload,
  X,
  Zap,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import LegacyPlannerPage from "./CurrentPlannerPage";
import { api, get, hasSession } from "../services/api";
import { classroomService } from "../services/classroomService";
import { adaptivePlannerService } from "./adaptivePlannerService";
import { recognizeExamImage } from "./imageOcr";
import "./timetable.css";

const useToastError = initial => useState(initial);

const asArray = (value) =>
  Array.isArray(value) ? value : value?.results || [];
const dateValue = (value) => (value ? new Date(`${value}T12:00:00`) : null);
const formatDate = (value) => {
  const date = dateValue(value);
  return date
    ? new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
      }).format(date)
    : "Date needed";
};
const formatDateTime = (value) =>
  value
    ? new Intl.DateTimeFormat("en-US", {
        weekday: "short",
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      }).format(new Date(value))
    : "Time needed";
const formatTime = (value) =>
  value
    ? new Intl.DateTimeFormat("en-US", {
        hour: "numeric",
        minute: "2-digit",
      }).format(new Date(value))
    : "";
const statusClass = (value) =>
  String(value || "")
    .toLowerCase()
    .replaceAll("_", "-");
const openResource = (resource) => {
  if (!resource?.file) return;
  const origin = new URL(api.url).origin;
  const url = /^https?:\/\//i.test(resource.file)
    ? resource.file
    : new URL(resource.file, `${origin}/`).toString();
  window.open(url, "_blank", "noopener,noreferrer");
};

function StatusPill({ value }) {
  return (
    <span className={`adaptive-status ${statusClass(value)}`}>
      {String(value || "Pending").replaceAll("_", " ")}
    </span>
  );
}

function MissionCard({ mission }) {
  return (
    <article className="mission-card">
      <div className="mission-card-head">
        <div>
          <span className="mission-subject">{mission.subject}</span>
          <h3>{mission.title}</h3>
        </div>
        <StatusPill value={mission.status} />
      </div>
      <div className="mission-date">
        <CalendarDays size={14} />
        <b>{formatDate(mission.exam_date)}</b>
        <span>
          {mission.days_remaining < 0
            ? "past due"
            : mission.days_remaining === 0
              ? "today"
              : `${mission.days_remaining} days left`}
        </span>
      </div>
      <div className="mission-progress">
        <div>
          <span>Mission progress</span>
          <b>{mission.progress_percentage}%</b>
        </div>
        <div className="progress-track">
          <span style={{ width: `${mission.progress_percentage}%` }} />
        </div>
      </div>
      <div className="mission-meta">
        <span>
          <Target size={13} /> {mission.mastered_topics}/
          {mission.total_topics || 0} topics ready
        </span>
        <span>
          <CircleAlert size={13} /> {mission.difficulty_label}
        </span>
      </div>
      {mission.weak_topics?.length > 0 && (
        <div className="mission-weak">
          <small>Focus next</small>
          <b>{mission.weak_topics.map((topic) => topic.name).join(" · ")}</b>
        </div>
      )}
    </article>
  );
}

function ResourceLinks({ resources }) {
  if (!resources?.length)
    return <small className="adaptive-muted">No linked notes yet</small>;
  return (
    <div className="resource-links">
      {resources.slice(0, 3).map((resource) => (
        <button
          className="resource-link"
          key={resource.id}
          onClick={() => openResource(resource)}
          disabled={!resource.file}
        >
          <FileText size={13} />
          <span>{resource.title}</span>
          <ArrowUpRight size={12} />
        </button>
      ))}
    </div>
  );
}

function ExamReview({ upload, subjects, busy, onClose, onChange, onConfirm }) {
  return (
    <div className="adaptive-modal-backdrop">
      <section
        className="panel adaptive-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="exam-review-title"
      >
        <div className="section-head">
          <div>
            <p className="eyebrow">EXAM IMPORT</p>
            <h2 id="exam-review-title">Review your exam dates</h2>
            <p className="muted">
              {upload.original_filename || "Uploaded schedule"} · check every
              row before saving.
            </p>
          </div>
          <button
            className="icon-button"
            onClick={onClose}
            aria-label="Close exam review"
          >
            <X size={17} />
          </button>
        </div>
        {upload.processing_error && (
          <p className="adaptive-notice">
            <CircleAlert size={15} />
            {upload.processing_error}
          </p>
        )}
        <div className="exam-review-list">
          {upload.rows?.map((row) => (
            <div className="exam-review-row" key={row.id}>
              <label>
                Subject
                <select
                  value={row.subject || ""}
                  onChange={(event) =>
                    onChange(row.id, "subject", event.target.value)
                  }
                >
                  <option value="">Choose subject</option>
                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Exam title
                <input
                  value={row.title || ""}
                  onChange={(event) =>
                    onChange(row.id, "title", event.target.value)
                  }
                />
              </label>
              <label>
                Date
                <input
                  type="date"
                  value={row.exam_date || ""}
                  onChange={(event) =>
                    onChange(row.id, "exam_date", event.target.value)
                  }
                />
              </label>
              <label>
                Starts
                <input
                  type="time"
                  value={row.start_time || ""}
                  onChange={(event) =>
                    onChange(row.id, "start_time", event.target.value)
                  }
                />
              </label>
              <label>
                Ends
                <input
                  type="time"
                  value={row.end_time || ""}
                  onChange={(event) =>
                    onChange(row.id, "end_time", event.target.value)
                  }
                />
              </label>
              <label>
                Venue
                <input
                  value={row.venue || ""}
                  onChange={(event) =>
                    onChange(row.id, "venue", event.target.value)
                  }
                  placeholder="Optional"
                />
              </label>
              <span className="confidence-label">
                {row.confidence
                  ? `${row.confidence}% extraction confidence`
                  : "Manual row"}
              </span>
            </div>
          ))}
        </div>
        <div className="button-row adaptive-modal-actions">
          <button className="button" onClick={onClose}>
            Cancel
          </button>
          <button
            className="button button-primary"
            onClick={onConfirm}
            disabled={busy || !upload.rows?.length}
          >
            {busy ? "Saving exams..." : "Confirm exam dates"}
            <Check size={15} />
          </button>
        </div>
      </section>
    </div>
  );
}

function AdaptiveOverview({
  overview,
  action,
  preview,
  loading,
  busy,
  onNextAction,
  onGenerate,
  onCommit,
  onOpenClassroom,
}) {
  if (loading)
    return (
      <div className="panel loading-state">
        Loading your adaptive study signals...
      </div>
    );
  if (!overview) return null;
  const actionData = action?.action || overview.next_action?.action;
  return (
    <>
      <div className="adaptive-summary">
        <div>
          <span>EXAM MISSIONS</span>
          <b>{overview.exam_missions.length}</b>
          <small>Dates on your runway</small>
        </div>
        <div>
          <span>WEAK TOPICS</span>
          <b>{overview.weak_topics.length}</b>
          <small>Highest-impact focus areas</small>
        </div>
        <div>
          <span>DEADLINE RESCUE</span>
          <b>{overview.deadline_rescue.length}</b>
          <small>Classroom tasks needing care</small>
        </div>
        <div>
          <span>STUDY LIBRARY</span>
          <b>{overview.resource_count}</b>
          <small>Notes and resources ready</small>
        </div>
      </div>
      <div className="adaptive-grid">
        <section className="panel adaptive-section adaptive-missions">
          <div className="section-head">
            <div>
              <p className="eyebrow">EXAM MISSION</p>
              <h2>Protect the runway</h2>
            </div>
            <span className="adaptive-section-count">
              {overview.exam_missions.length} active
            </span>
          </div>
          {overview.exam_missions.length ? (
            <div className="mission-grid">
              {overview.exam_missions.map((mission) => (
                <MissionCard key={mission.id} mission={mission} />
              ))}
            </div>
          ) : (
            <div className="adaptive-empty">
              <CalendarDays size={20} />
              <p>Add or import an exam to build a mission.</p>
            </div>
          )}
        </section>
        <section className="panel adaptive-section adaptive-next">
          <div className="section-head">
            <div>
              <p className="eyebrow">RIGHT NOW</p>
              <h2>What should I do now?</h2>
            </div>
            <button
              className="icon-button"
              onClick={onNextAction}
              aria-label="Refresh next action"
            >
              <RefreshCw size={15} />
            </button>
          </div>
          {actionData ? (
            <>
              <div className="next-action-title">
                <Zap size={19} />
                <div>
                  <b>{actionData.topic || actionData.subject}</b>
                  <span>{actionData.duration_minutes} minute focus block</span>
                </div>
              </div>
              <p className="adaptive-reason">
                {action?.reason || overview.next_action?.reason}
              </p>
              <div className="button-row">
                <button
                  className="button button-primary"
                  onClick={() => onNextAction(true)}
                >
                  Start focus
                </button>
                <button className="button" onClick={onGenerate}>
                  Plan around it
                </button>
              </div>
            </>
          ) : (
            <div className="adaptive-empty">
              <Zap size={20} />
              <p>Add a topic or exam to get a next action.</p>
            </div>
          )}
        </section>
        <section className="panel adaptive-section adaptive-weak">
          <div className="section-head">
            <div>
              <p className="eyebrow">ADAPTIVE SIGNALS</p>
              <h2>Weak topics to move first</h2>
            </div>
            <span className="adaptive-section-count">Ranked</span>
          </div>
          {overview.weak_topics.length ? (
            <div className="weak-topic-list">
              {overview.weak_topics.map((topic) => (
                <article
                  className="weak-topic-row"
                  key={topic.topic_id || topic.subject_id}
                >
                  <div className="weak-topic-score">
                    <b>{topic.priority_score}</b>
                    <small>impact</small>
                  </div>
                  <div className="weak-topic-main">
                    <div>
                      <b>{topic.topic || topic.subject}</b>
                      <span>
                        {topic.subject} · {topic.difficulty_label}
                      </span>
                    </div>
                    <div className="topic-progress">
                      <span style={{ width: `${topic.mastery_percentage}%` }} />
                    </div>
                    <small>
                      {topic.mastery_percentage}% mastery ·{" "}
                      {topic.reasons?.[0]?.label || "Needs deliberate practice"}
                    </small>
                    <ResourceLinks resources={topic.resources} />
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="adaptive-empty">
              <Target size={20} />
              <p>Complete a subject or topic to reveal adaptive signals.</p>
            </div>
          )}
        </section>
        <section className="panel adaptive-section adaptive-rescue">
          <div className="section-head">
            <div>
              <p className="eyebrow">DEADLINE RESCUE</p>
              <h2>Assignments from Classroom</h2>
            </div>
            <button className="button button-light" onClick={onOpenClassroom}>
              <RefreshCw size={14} />
              Sync
            </button>
          </div>
          {overview.deadline_rescue.length ? (
            <div className="rescue-list">
              {overview.deadline_rescue.map((task) => (
                <article className="rescue-row" key={task.id}>
                  <div className="rescue-icon">
                    <ListChecks size={16} />
                  </div>
                  <div className="rescue-details">
                    <b>{task.title}</b>
                    <span>
                      {task.subject || "Unsorted"} · {task.estimated_minutes}{" "}
                      min
                    </span>
                  </div>
                  <div
                    className={`rescue-due ${task.days_remaining <= 1 ? "urgent" : ""}`}
                  >
                    <b>
                      {task.days_remaining < 0
                        ? "Overdue"
                        : task.days_remaining === 0
                          ? "Today"
                          : formatDateTime(task.deadline)}
                    </b>
                    <small>{task.priority}</small>
                  </div>
                  {task.link && (
                    <a
                      href={task.link}
                      target="_blank"
                      rel="noreferrer"
                      aria-label={`Open ${task.title} in Google Classroom`}
                    >
                      <ArrowUpRight size={15} />
                    </a>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <div className="adaptive-empty">
              <ListChecks size={20} />
              <p>No open Classroom assignments need rescue.</p>
            </div>
          )}
        </section>
        <section className="panel adaptive-section adaptive-library">
          <div className="section-head">
            <div>
              <p className="eyebrow">CONNECTED SOURCES</p>
              <h2>Timetable inputs</h2>
            </div>
            <span className="adaptive-section-count">
              {overview.timetable.length} events
            </span>
          </div>
          <div className="source-event-list">
            {overview.timetable.slice(0, 10).map((event) => (
              <div
                className={`source-event ${statusClass(event.source)}`}
                key={`${event.source}-${event.id}-${event.start_at}`}
              >
                <div className="source-event-time">
                  <b>{formatTime(event.start_at)}</b>
                  <small>{formatDate(event.start_at?.slice(0, 10))}</small>
                </div>
                <div>
                  <b>{event.title}</b>
                  <span>
                    {event.source === "COLLEGE"
                      ? `${event.subject} · ${event.room || "College class"}`
                      : event.source.replaceAll("_", " ")}
                  </span>
                </div>
              </div>
            ))}
            {!overview.timetable.length && (
              <div className="adaptive-empty">
                <Clock3 size={20} />
                <p>Your connected timetable is clear.</p>
              </div>
            )}
          </div>
        </section>
      </div>
      {preview && (
        <section className="panel adaptive-plan-preview">
          <div className="section-head">
            <div>
              <p className="eyebrow">PLAN PREVIEW</p>
              <h2>
                {preview.scheduled_minutes} minutes placed around your
                commitments
              </h2>
              <p className="muted">
                Review these blocks before they are added to your timetable.
              </p>
            </div>
            <button
              className="icon-button"
              onClick={() => onCommit(null)}
              aria-label="Close plan preview"
            >
              <X size={17} />
            </button>
          </div>
          <div className="preview-blocks">
            {preview.blocks.map((block, index) => (
              <div className="preview-block" key={`${block.start_at}-${index}`}>
                <span>{formatDateTime(block.start_at)}</span>
                <b>{block.title}</b>
                <small>
                  {block.duration_minutes} min · {block.reason}
                </small>
                {block.resource_titles?.length > 0 && (
                  <em>Use {block.resource_titles.join(", ")}</em>
                )}
              </div>
            ))}
          </div>
          {preview.blocks.length ? (
            <div className="button-row">
              <button
                className="button button-primary"
                onClick={() => onCommit(preview.blocks)}
                disabled={busy}
              >
                {busy ? "Adding blocks..." : "Add confirmed blocks"}
                <Check size={15} />
              </button>
            </div>
          ) : (
            <p className="adaptive-notice">
              <CircleAlert size={15} />
              No open study windows were found for this range.
            </p>
          )}
        </section>
      )}
    </>
  );
}

export default function PlannerPage() {
  const navigate = useNavigate();
  const [overview, setOverview] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [action, setAction] = useState(null);
  const [upload, setUpload] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useToastError("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [overviewResponse, subjectResponse] = await Promise.all([
        adaptivePlannerService.overview({ days: 7 }),
        get("/subjects/"),
      ]);
      setOverview(overviewResponse);
      setSubjects(
        asArray(subjectResponse).length
          ? asArray(subjectResponse)
          : overviewResponse.subjects || [],
      );
    } catch (reason) {
      setError(reason.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!hasSession()) {
      setLoading(false);
      return;
    }
    load();
  }, []);

  const nextAction = async (startFocus) => {
    if (!hasSession()) {
      setError("Sign in to use your personal study planner.");
      return;
    }
    try {
      const response = await adaptivePlannerService.nextAction();
      setAction(response);
      if (startFocus && response.action) navigate("/focus");
    } catch (reason) {
      setError(reason.message);
    }
  };

  const generate = async () => {
    if (!hasSession()) {
      setError("Sign in to use your personal study planner.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      setPreview(
        await adaptivePlannerService.preview({
          days: 7,
          daily_minutes: 90,
          day_start: "08:00",
          day_end: "22:00",
        }),
      );
    } catch (reason) {
      setError(reason.message);
    } finally {
      setBusy(false);
    }
  };

  const commit = async (blocks) => {
    if (!blocks) return setPreview(null);
    if (!hasSession()) {
      setError("Sign in to use your personal study planner.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await adaptivePlannerService.commit(blocks);
      setPreview(null);
      await load();
    } catch (reason) {
      setError(reason.message);
    } finally {
      setBusy(false);
    }
  };

  const uploadExam = async (event) => {
    if (!hasSession()) {
      setError("Sign in to use your personal study planner.");
      return;
    }
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setUploading(true);
    setError("");
    const body = new FormData();
    body.append("file", file);
    const isImage =
      file.type.startsWith("image/") || /\.(png|jpe?g|webp)$/i.test(file.name);
    try {
      if (isImage) {
        try {
          const ocrText = await recognizeExamImage(file);
          if (ocrText.trim()) body.append("ocr_text", ocrText);
        } catch {}
      }
      setUpload(await adaptivePlannerService.uploadExamSchedule(body));
    } catch (reason) {
      setError(reason.message);
    } finally {
      setUploading(false);
    }
  };

  const updateRow = (rowId, key, value) =>
    setUpload((current) => ({
      ...current,
      rows: current.rows.map((row) =>
        row.id === rowId ? { ...row, [key]: value } : row,
      ),
    }));

  const confirmUpload = async () => {
    if (!hasSession()) {
      setError("Sign in to use your personal study planner.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const rows = upload.rows.map((row) => ({
        id: row.id,
        subject: row.subject,
        title: row.title,
        exam_date: row.exam_date,
        start_time: row.start_time,
        end_time: row.end_time,
        venue: row.venue || "",
      }));
      await adaptivePlannerService.confirmExamSchedule(upload.id, rows);
      setUpload(null);
      await load();
    } catch (reason) {
      setError(reason.message);
    } finally {
      setBusy(false);
    }
  };

  const syncClassroom = async () => {
    if (!hasSession()) {
      setError("Sign in to use your personal study planner.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await classroomService.sync();
      await load();
    } catch (reason) {
      setError(reason.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="planner-page-shell">
      <div className="planner-adaptive-overview">
        <div className="page-header adaptive-page-header">
          <div>
            <p className="eyebrow">ADAPTIVE STUDY PLANNER</p>
            <h1>Build a week that learns.</h1>
          </div>
          <details className="planner-actions-menu">
            <summary className="button button-primary planner-actions-trigger">
              <Sparkles size={15} />
              Planner actions
              <ChevronDown size={14} />
            </summary>
            <div className="planner-actions-popover">
              <button className="button" onClick={() => nextAction(false)}>
                <Zap size={16} />
                What should I do now?
              </button>
              <button className="button" onClick={generate} disabled={busy}>
                <Sparkles size={16} />
                Generate adaptive plan
              </button>
              <label
                className={`button button-primary ${uploading ? "disabled" : ""}`}
              >
                <Upload size={16} />
                {uploading ? "Reading schedule..." : "Upload exam schedule"}
                <input
                  hidden
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg,.webp"
                  onChange={uploadExam}
                  disabled={uploading}
                />
              </label>
            </div>
          </details>
        </div>
        {error && <p className="api-error">{error}</p>}
        {(overview || loading) && (
            <details className="planner-adaptive-details" open>
            <summary>
              <span>
                <small>ADAPTIVE OVERVIEW</small>
                <strong>Signals, missions, and deadlines</strong>
              </span>
              <span className="planner-adaptive-details-action">
                View overview
              </span>
            </summary>
            <div className="planner-adaptive-details-body">
              <AdaptiveOverview
                overview={overview}
                action={action}
                preview={preview}
                loading={loading}
                busy={busy}
                onNextAction={nextAction}
                onGenerate={generate}
                onCommit={commit}
                onOpenClassroom={syncClassroom}
              />
            </div>
          </details>
        )}
      </div>
      <section className="planner-timetable-section">
        <LegacyPlannerPage />
      </section>
      {upload && (
        <ExamReview
          upload={upload}
          subjects={subjects}
          busy={busy}
          onClose={() => setUpload(null)}
          onChange={updateRow}
          onConfirm={confirmUpload}
        />
      )}
    </div>
  );
}
