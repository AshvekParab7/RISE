import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Check,
  ChevronRight,
  CircleCheck,
  Download,
  FileText,
  Filter,
  Pencil,
  Play,
  Plus,
  RefreshCw,
  Trash2,
  Upload,
  X,
} from "lucide-react";
import { useWorkspace } from "./context/WorkspaceContext";
import { subjectService } from "./services/subjectService";
import { semesterService } from "./services/semesterService";
import { taskService } from "./services/taskService";
import { resourceService } from "./services/resourceService";
import { syllabusService } from "./services/syllabusService";
import { studySessionService } from "./services/studySessionService";
import { api, get, hasSession } from "./services/api";
import PdfViewer from "./PdfViewer";
import "./resourceViewer.css";

const Button = ({
  children,
  primary = false,
  onClick,
  icon: Icon,
  disabled = false,
}) => (
  <button
    disabled={disabled}
    onClick={(event) => {
      if (onClick) return onClick(event);
      if (children !== "Open") return;
      const title = event.currentTarget
        .closest(".note-row")
        ?.querySelector("b")?.textContent;
      if (!title) return;
      get("/resources/")
        .then((value) => asArray(value).find((item) => item.title === title))
        .then(openResource)
        .catch(() => null);
    }}
    className={`button ${primary ? "button-primary" : ""}`}
  >
    {Icon && <Icon size={16} />} {children}
  </button>
);
const Header = ({ eyebrow, title, description, action }) => (
  <div className="page-header">
    <div>
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      <p className="muted lead">{description}</p>
    </div>
    {action}
  </div>
);
const ErrorMessage = ({ message }) =>
  message ? <p className="api-error">{message}</p> : null;
const asArray = (value) =>
  Array.isArray(value) ? value : value?.results || [];
const createSemesterForm = () => {
  const year = new Date().getFullYear();
  return {
    name: `Semester 5`,
    year,
    semester_number: 5,
    is_current: true,
    start_date: `${year}-07-01`,
    end_date: `${year}-12-31`,
  };
};
const mapTask = (task, subjects) => ({
  ...task,
  due: task.deadline,
  estimate: `${task.estimated_minutes} min`,
  status: task.status === "COMPLETED" ? "completed" : "open",
  subjectId: task.subject,
  subject:
    subjects.find((item) => item.id === task.subject)?.name || task.subject,
  classroomUrl: task.classroom_url,
  submissionStatus: task.submission_status,
});
const taskIsToday = (task) => {
  const deadline = new Date(task.deadline || task.due);
  const today = new Date();
  return deadline.toDateString() === today.toDateString();
};
const taskIsUpcoming = (task) => {
  const deadline = new Date(task.deadline || task.due);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return deadline >= today && !taskIsToday(task);
};
const openResource = (note) => {
  const url = resourceUrl(note);
  if (!url) return;
  window.location.assign(url);
};
const resourceUrl = (note) => {
  const resourceLink = note.file || note.description;
  if (!resourceLink) return "";
  const origin = new URL(api.url).origin;
  return /^https?:\/\//i.test(resourceLink)
    ? resourceLink
    : new URL(resourceLink, `${origin}/`).toString();
};
const isGoogleResource = (note) => /(?:drive\.google\.com|docs\.google\.com|classroom\.google\.com)/i.test(resourceUrl(note));
const downloadResource = async (note) => {
  if (!note.file && isGoogleResource(note) && note.id) {
    try {
      const blob = await resourceService.download(note.id);
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = note.title || "resource";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);
      return;
    } catch {
      // Fall through to the original Classroom link when Drive access is unavailable.
    }
  }
  const url = resourceUrl(note);
  if (!url) return;
  const link = document.createElement("a");
  link.href = url;
  link.download = note.title || "resource";
  document.body.appendChild(link);
  link.click();
  link.remove();
};
const resourceMeta = (item) => {
  if (item.file_size) return `${item.file_size} bytes`;
  if (item.file) return "Ready to open";
  if (item.source === "GOOGLE_CLASSROOM" && item.description) return "Open online";
  return "File unavailable";
};

function ResourceViewer({ resource, onClose }) {
  const [previewFile, setPreviewFile] = useState(null);
  const [previewHtml, setPreviewHtml] = useState("");
  const [previewError, setPreviewError] = useState("");
  const url = resourceUrl(resource);
  const googleUrl = isGoogleResource(resource);
  const isPdf = /\.pdf(?:$|[?#])/i.test(url) || /\.pdf$/i.test(resource.title || "");
  const closeViewer = () => onClose();

  useEffect(() => {
    if (!url || (!googleUrl && !isPdf)) return undefined;
    let cancelled = false;
    setPreviewFile(null);
    setPreviewHtml("");
    setPreviewError("");
    const fileRequest = googleUrl && resource.id
      ? resourceService.preview(resource.id)
      : fetch(url).then((response) => {
        if (!response.ok) throw new Error("Resource request failed.");
        return response.blob();
      });
    fileRequest
      .then((blob) => {
        if (cancelled) return;
        if (blob.type.includes("html")) {
          blob.text().then((html) => !cancelled && setPreviewHtml(html));
        } else if (blob.type === "application/pdf" || isPdf) {
          setPreviewFile(new File([blob], resource.title || "resource.pdf", { type: "application/pdf" }));
        } else {
          setPreviewError("This file type cannot be previewed inside RISE.");
        }
      })
      .catch(() => !cancelled && setPreviewError("This resource could not be fetched for preview."));
    return () => { cancelled = true; };
  }, [googleUrl, isPdf, resource.id, resource.title, url]);

  useEffect(() => {
    const handleKeyDown = (event) => event.key === "Escape" && onClose();
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="resource-viewer-overlay" role="presentation" onClick={onClose}>
      <section className="resource-viewer" role="dialog" aria-modal="true" aria-labelledby="resource-viewer-title" onClick={(event) => event.stopPropagation()}>
        <header className="resource-viewer-header">
          <div>
            <span className="eyebrow">RESOURCE PREVIEW</span>
            <h2 id="resource-viewer-title">{resource.title}</h2>
          </div>
          <button type="button" className="icon-button" onClick={closeViewer} aria-label="Close resource viewer" title="Close">
            <X size={18} />
          </button>
        </header>
        <div className="resource-viewer-body">
          {previewFile ? (
            <PdfViewer file={previewFile} />
          ) : previewHtml ? (
            <div className="resource-viewer-html" dangerouslySetInnerHTML={{ __html: previewHtml }} />
          ) : (
            <div className="resource-viewer-fallback">
              <FileText size={32} />
              <h3>{previewError || (googleUrl || isPdf ? "Loading resource preview..." : "This file type cannot be previewed inside RISE.")}</h3>
              <p>{googleUrl ? "Use the original Classroom or Drive file to view this resource." : `${resource.title} · ${resource.resource_type || "Document"}`}</p>
              {googleUrl && url && <a className="button button-primary" href={url}>Open in Google Drive</a>}
            </div>
          )}
        </div>
        <footer className="resource-viewer-footer">
          <button type="button" className="button" onClick={closeViewer}>Back to notes</button>
          {googleUrl && <a className="button" href={url}>Open in Google Drive</a>}
        </footer>
      </section>
    </div>
  );
}

export function ConnectedSubjects() {
  const { subjects, setSubjects } = useWorkspace();
  const [form, setForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [needsSemester, setNeedsSemester] = useState(false);
  const [semesterForm, setSemesterForm] = useState(null);
  const [semesterSaving, setSemesterSaving] = useState(false);
  useEffect(() => {
    subjectService
      .list()
      .then((data) => setSubjects(asArray(data).map(mapSubject)))
      .catch((reason) => setError(reason.message))
      .finally(() => setLoading(false));
  }, [setSubjects]);
  const mapSubject = (subject) => ({
    ...subject,
    id: subject.id,
    short: subject.code || subject.name.slice(0, 2).toUpperCase(),
    mastery: subject.mastery_percentage ?? 0,
    risk: subject.priority_score ?? 0,
    priority:
      (subject.priority_score ?? 0) > 84
        ? "HIGH"
        : (subject.priority_score ?? 0) > 54
          ? "MEDIUM"
          : "LOW",
    exam: subject.exam_date || "Not scheduled",
    next: "First topic",
    units: [],
  });
  const save = async () => {
    const name = form?.name.trim() || "";
    if (!name) return setError("Subject name is required.");
    if (!form?.semester)
      return setError("Create a semester before adding a subject.");
    if (
      subjects.some(
        (item) =>
          item.id !== form.id &&
          item.name.trim().toLowerCase() === name.toLowerCase(),
      )
    )
      return setError(
        "A subject with this name already exists in this semester.",
      );
    setSaving(true);
    setError("");
    try {
      const payload = {
        name,
        code: form.code.trim(),
        description: form.description,
        difficulty: form.difficulty,
        target_grade: form.target_grade,
        color: form.color,
        icon: form.icon,
        exam_date: form.exam_date || null,
        semester: form.semester,
      };
      const response = form.id
        ? await subjectService.update(form.id, payload)
        : await subjectService.create(payload);
      const mapped = mapSubject(response);
      setSubjects((items) =>
        form.id
          ? items.map((item) => (item.id === form.id ? mapped : item))
          : [...items, mapped],
      );
      setForm(null);
    } catch (reason) {
      setError(reason.message);
    } finally {
      setSaving(false);
    }
  };
  const remove = async (subject) => {
    if (!window.confirm(`Delete ${subject.name}?`)) return;
    try {
      await subjectService.remove(subject.id);
      setSubjects((items) => items.filter((item) => item.id !== subject.id));
    } catch (reason) {
      setError(reason.message);
    }
  };
  const saveSemester = async () => {
    const name = semesterForm?.name.trim() || "";
    const year = Number(semesterForm?.year);
    const semesterNumber = Number(semesterForm?.semester_number);
    if (!name) return setError("Semester name is required.");
    if (!Number.isInteger(year) || year < 2000)
      return setError("Enter a valid semester year.");
    if (!Number.isInteger(semesterNumber) || semesterNumber < 1)
      return setError("Enter a valid semester number.");
    setSemesterSaving(true);
    setError("");
    try {
      const semester = await semesterService.create({
        name,
        year,
        semester_number: semesterNumber,
        is_current: Boolean(semesterForm.is_current),
        start_date: semesterForm.start_date || null,
        end_date: semesterForm.end_date || null,
      });
      if (!semester?.id) throw new Error("The semester could not be created.");
      setSemesterForm(null);
      setNeedsSemester(false);
      setForm({
        name: "",
        code: "",
        description: "",
        difficulty: "MEDIUM",
        target_grade: "A",
        color: "#9733EE",
        icon: "book-open",
        exam_date: "",
        semester: semester.id,
      });
    } catch (reason) {
      setError(reason.message);
    } finally {
      setSemesterSaving(false);
    }
  };
  const openNew = async () => {
    if (!hasSession()) {
      setNeedsSemester(false);
      return setError("Sign in to add a subject.");
    }
    try {
      const semesters = asArray(await semesterService.list());
      const semester =
        semesters.find((item) => item.is_current) || semesters[0];
      if (!semester?.id) {
        setNeedsSemester(true);
        return setError("Create a semester before adding a subject.");
      }
      setNeedsSemester(false);
      setError("");
      setForm({
        name: "",
        code: "",
        description: "",
        difficulty: "MEDIUM",
        target_grade: "A",
        color: "#9733EE",
        icon: "book-open",
        exam_date: "",
        semester: semester.id,
      });
    } catch (reason) {
      setNeedsSemester(false);
      setError(reason.message);
    }
  };
  return (
    <>
      <Header
        eyebrow="ACADEMIC WORLD"
        title="My subjects"
        description="A living map of your semester, priorities, and progress."
        action={
          <Button primary onClick={openNew} icon={Plus}>
            Add subject
          </Button>
        }
      />
      {error && needsSemester ? (
        <div className="api-error subject-error">
          <span>{error}</span>
          <Button
            primary
            onClick={() => {
              setError("");
              setSemesterForm(createSemesterForm());
            }}
            icon={Plus}
          >
            Add semester
          </Button>
        </div>
      ) : (
        error && <ErrorMessage message={error} />
      )}{" "}
      {semesterForm && (
        <div className="panel editor-panel semester-editor-panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">ACADEMIC SETUP</p>
              <h2>Add a semester</h2>
            </div>
            <button
              className="icon-button"
              onClick={() => setSemesterForm(null)}
              aria-label="Close semester editor"
            >
              <X size={17} />
            </button>
          </div>
          <div className="form-grid">
            <label>
              Semester name
              <input
                value={semesterForm.name}
                onChange={(event) =>
                  setSemesterForm({
                    ...semesterForm,
                    name: event.target.value,
                  })
                }
                placeholder="e.g. Semester 5"
              />
            </label>
            <label>
              Year
              <input
                type="number"
                min="2000"
                value={semesterForm.year}
                onChange={(event) =>
                  setSemesterForm({
                    ...semesterForm,
                    year: event.target.value,
                  })
                }
              />
            </label>
            <label>
              Semester number
              <input
                type="number"
                min="1"
                max="20"
                value={semesterForm.semester_number}
                onChange={(event) =>
                  setSemesterForm({
                    ...semesterForm,
                    semester_number: event.target.value,
                  })
                }
              />
            </label>
            <label>
              Start date
              <input
                type="date"
                value={semesterForm.start_date || ""}
                onChange={(event) =>
                  setSemesterForm({
                    ...semesterForm,
                    start_date: event.target.value,
                  })
                }
              />
            </label>
            <label>
              End date
              <input
                type="date"
                value={semesterForm.end_date || ""}
                onChange={(event) =>
                  setSemesterForm({
                    ...semesterForm,
                    end_date: event.target.value,
                  })
                }
              />
            </label>
          </div>
          <div className="button-row">
            <Button onClick={() => setSemesterForm(null)}>Cancel</Button>
            <Button primary onClick={saveSemester} disabled={semesterSaving}>
              {semesterSaving ? "Saving..." : "Save semester"}
            </Button>
          </div>
        </div>
      )}
      {form && (
        <div className="panel editor-panel">
          <div className="section-head">
            <div>
              <p className="eyebrow">
                {form.id ? "EDIT SUBJECT" : "NEW SUBJECT"}
              </p>
              <h2>{form.id ? "Tune this subject" : "Add a subject"}</h2>
            </div>
            <button className="icon-button" onClick={() => setForm(null)}>
              <X size={17} />
            </button>
          </div>
          <div className="form-grid">
            <label>
              Subject name
              <input
                value={form.name}
                onChange={(event) =>
                  setForm({ ...form, name: event.target.value })
                }
              />
            </label>
            <label>
              Code
              <input
                value={form.code}
                onChange={(event) =>
                  setForm({ ...form, code: event.target.value })
                }
              />
            </label>
            <label>
              Difficulty
              <select
                value={form.difficulty}
                onChange={(event) =>
                  setForm({ ...form, difficulty: event.target.value })
                }
              >
                <option value="EASY">Easy</option>
                <option value="MEDIUM">Medium</option>
                <option value="HARD">Hard</option>
              </select>
            </label>
            <label>
              Target grade
              <input
                value={form.target_grade}
                onChange={(event) =>
                  setForm({ ...form, target_grade: event.target.value })
                }
              />
            </label>
            <label>
              Exam date
              <input
                type="date"
                value={form.exam_date || ""}
                onChange={(event) =>
                  setForm({ ...form, exam_date: event.target.value })
                }
              />
            </label>
            <label>
              Color
              <input
                type="color"
                value={form.color}
                onChange={(event) =>
                  setForm({ ...form, color: event.target.value })
                }
              />
            </label>
          </div>
          <div className="button-row">
            <Button onClick={() => setForm(null)}>Cancel</Button>
            <Button primary onClick={save} disabled={saving}>
              {saving ? "Saving..." : "Save subject"}
            </Button>
          </div>
        </div>
      )}
      {loading ? (
        <div className="panel loading-state">Loading subjects...</div>
      ) : (
        <div className="subject-grid">
          {subjects.map((subject) => (
            <div className="subject-card" key={subject.id}>
              <Link to={`/subjects/${subject.id}`}>
                <div className="subject-card-top">
                  <div
                    className="subject-icon"
                    style={{ background: subject.color }}
                  >
                    {subject.short}
                  </div>
                </div>
                <h2>{subject.name}</h2>
                <p className="muted">
                  {subject.code || "Subject"} · Exam{" "}
                  {subject.exam || "not scheduled"}
                </p>
                <div className="mastery">
                  <span>
                    Mastery <b>{subject.mastery || 0}%</b>
                  </span>
                  <span
                    className={`priority ${(subject.priority || "LOW").toLowerCase()}`}
                  >
                    {subject.priority || "LOW"}
                  </span>
                </div>
                <div className="progress-track">
                  <span
                    style={{
                      width: `${subject.mastery || 0}%`,
                      background: subject.color,
                    }}
                  />
                </div>
              </Link>
              <div className="card-actions">
                <button
                  onClick={() =>
                    setForm({
                      ...subject,
                      target_grade: subject.target_grade || "A",
                      difficulty: subject.difficulty || "MEDIUM",
                      semester: subject.semester,
                    })
                  }
                >
                  <Pencil size={14} /> Edit
                </button>
                <button onClick={() => remove(subject)}>
                  <Trash2 size={14} /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

export function ConnectedTasks() {
  const { tasks, setTasks, subjects } = useWorkspace();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState(null);
  const [filter, setFilter] = useState("All");
  useEffect(() => {
    taskService
      .list()
      .then((data) =>
        setTasks(asArray(data).map((task) => mapTask(task, subjects))),
      )
      .catch((reason) => setError(reason.message))
      .finally(() => setLoading(false));
  }, [setTasks, subjects]);
  const save = async () => {
    if (!form?.title.trim()) return setError("Task title is required.");
    setSaving(true);
    try {
      const response = form.id
        ? await taskService.update(form.id, {
            title: form.title,
            description: form.description,
            subject: form.subject || null,
            deadline: form.deadline,
            estimated_minutes: Number(form.estimated_minutes),
            priority: form.priority,
            source: form.source,
            status: form.status || "TODO",
          })
        : await taskService.create({
            title: form.title,
            description: form.description || "",
            subject: form.subject || null,
            deadline: form.deadline,
            estimated_minutes: Number(form.estimated_minutes),
            priority: form.priority,
            source: form.source,
            status: "TODO",
          });
      const mapped = mapTask(response, subjects);
      setTasks((items) =>
        form.id
          ? items.map((item) => (item.id === form.id ? mapped : item))
          : [mapped, ...items],
      );
      setForm(null);
    } catch (reason) {
      setError(reason.message);
    } finally {
      setSaving(false);
    }
  };
  const complete = async (task) => {
    try {
      const response = await taskService.complete(task.id);
      setTasks((items) =>
        items.map((item) =>
          item.id === task.id ? mapTask(response, subjects) : item,
        ),
      );
    } catch (reason) {
      setError(reason.message);
    }
  };
  const remove = async (task) => {
    if (!window.confirm(`Delete ${task.title}?`)) return;
    try {
      await taskService.remove(task.id);
      setTasks((items) => items.filter((item) => item.id !== task.id));
    } catch (reason) {
      setError(reason.message);
    }
  };
  const shown = tasks.filter(
    (task) =>
      filter === "All" ||
      (filter === "Completed" && task.status === "completed") ||
      (filter === "Today" && task.status !== "completed" && taskIsToday(task)) ||
      (filter === "Upcoming" && task.status !== "completed" && taskIsUpcoming(task)),
  );
  const openNew = () =>
    setForm({
      title: "",
      description: "",
      subject: subjects[0]?.id || "",
      deadline: new Date(Date.now() + 86400000).toISOString().slice(0, 16),
      estimated_minutes: 60,
      priority: "MEDIUM",
      source: "MANUAL",
      status: "TODO",
    });
  return (
    <>
      <Header
        eyebrow="ACADEMIC INBOX"
        title="Tasks & deadlines"
        description="Assignments, exams, and important work in one clear runway."
        action={
          <Button primary icon={Plus} onClick={openNew}>
            Create task
          </Button>
        }
      />
      {error && <ErrorMessage message={error} />}{" "}
      {form && (
        <div className="panel quick-editor form-grid">
          <label>
            Task name
            <input
              value={form.title}
              onChange={(event) =>
                setForm({ ...form, title: event.target.value })
              }
            />
          </label>
          <label>
            Subject
            <select
              value={form.subject}
              onChange={(event) =>
                setForm({ ...form, subject: event.target.value })
              }
            >
              {subjects.map((subject) => (
                <option key={subject.id} value={subject.id}>
                  {subject.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Deadline
            <input
              type="datetime-local"
              value={form.deadline}
              onChange={(event) =>
                setForm({ ...form, deadline: event.target.value })
              }
            />
          </label>
          <label>
            Estimated minutes
            <input
              type="number"
              min="1"
              value={form.estimated_minutes}
              onChange={(event) =>
                setForm({ ...form, estimated_minutes: event.target.value })
              }
            />
          </label>
          <div className="button-row">
            <Button onClick={() => setForm(null)}>Cancel</Button>
            <Button primary onClick={save} disabled={saving}>
              {saving ? "Saving..." : "Save task"}
            </Button>
          </div>
        </div>
      )}
      <div className="filter-bar">
        <div className="tabs compact">
          {["All", "Today", "Upcoming", "Completed"].map((item) => (
            <button
              className={filter === item ? "active" : ""}
              onClick={() => setFilter(item)}
              key={item}
            >
              {item}
            </button>
          ))}
        </div>
        <Filter size={15} />
      </div>
      {loading ? (
        <div className="panel loading-state">Loading tasks...</div>
      ) : (
        <div className="panel task-list">
          {shown.map((task) => (
            <div className="task-row" key={task.id}>
              <button className="task-check" onClick={() => complete(task)}>
                {task.status === "completed" && <Check size={15} />}
              </button>
              <div className="task-details">
                <b>{task.title}</b>
                <small>
                  {task.subject} · {task.source}
                </small>
                  {task.description && <small>{task.description}</small>}
                  {task.classroomUrl && <a className="task-classroom-link" href={task.classroomUrl}>Google Classroom</a>}
              </div>
              <div className="task-due">
                <b>{task.due}</b>
                <small>{task.estimate}</small>
                  {task.submissionStatus && <small>{task.submissionStatus.replaceAll("_", " ")}</small>}
              </div>
              <button
                className="icon-button"
                onClick={() =>
                  setForm({
                    ...task,
                    subject: task.subjectId || task.subject,
                    deadline: (task.deadline || task.due || "").slice(0, 16),
                    status: task.status === "completed" ? "COMPLETED" : "TODO",
                    estimated_minutes: Number.parseInt(task.estimate) || 60,
                  })
                }
              >
                <Pencil size={14} />
              </button>
              <button
                className="icon-button danger"
                onClick={() => remove(task)}
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

export function ConnectedNotesLegacy() {
  const { notes, setNotes, subjects } = useWorkspace();
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState(null);
  const [subject, setSubject] = useState("");
  const [type, setType] = useState("NOTE");
  useEffect(() => {
    resourceService
      .list()
      .then((data) =>
        setNotes(
          asArray(data).map((item) => ({
            ...item,
            subject:
              subjects.find((subjectItem) => subjectItem.id === item.subject)
                ?.name || item.subject,
            source:
              item.source === "GOOGLE_CLASSROOM"
                ? "Google Classroom"
                : "My notes",
            meta: resourceMeta(item),
          })),
        ),
      )
      .catch((reason) => setError(reason.message))
      .finally(() => setLoading(false));
  }, [setNotes, subjects]);
  const upload = async () => {
    if (!file || !subject) return setError("Choose a file and subject first.");
    setUploading(true);
    setError("");
    const body = new FormData();
    body.append("file", file);
    body.append("title", file.name);
    body.append("subject", subject);
    body.append("resource_type", type);
    body.append("source", "USER_UPLOAD");
    try {
      const response = await resourceService.upload(body);
      setNotes((items) => [
        {
          ...response,
          subject:
            subjects.find((item) => item.id === response.subject)?.name ||
            response.subject,
          source: "My notes",
          meta: `${response.file_size || file.size} bytes`,
        },
        ...items,
      ]);
      setFile(null);
    } catch (reason) {
      setError(reason.message);
    } finally {
      setUploading(false);
    }
  };
  const remove = async (note) => {
    try {
      await resourceService.remove(note.id);
      setNotes((items) => items.filter((item) => item.id !== note.id));
    } catch (reason) {
      setError(reason.message);
    }
  };
  return (
    <>
      <Header
        eyebrow="KNOWLEDGE BASE"
        title="Notes & resources"
        description="Your study library, connected to Django."
        action={
          <label className="button button-primary">
            <Upload size={16} />
            Choose file
            <input
              hidden
              type="file"
              accept=".pdf,.doc,.docx,.ppt,.pptx,.png,.jpg,.jpeg,.webp"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>
        }
      />
      {error && <ErrorMessage message={error} />}
      <div className="upload-strip">
        <div>
          <b>{file ? file.name : "Choose a resource to upload"}</b>
          <span>PDF, DOCX, PPTX, or image</span>
        </div>
        <select
          value={subject}
          onChange={(event) => setSubject(event.target.value)}
        >
          <option value="">Choose subject</option>
          {subjects.map((item) => (
            <option value={item.id} key={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <select value={type} onChange={(event) => setType(event.target.value)}>
          <option value="NOTE">Note</option>
          <option value="SLIDES">Slides</option>
          <option value="DOCUMENT">Document</option>
          <option value="QUESTION_PAPER">Question paper</option>
          <option value="IMAGE">Image</option>
        </select>
        <Button primary onClick={upload} disabled={uploading}>
          {uploading ? "Uploading..." : "Upload"}
        </Button>
      </div>
      {loading ? (
        <div className="panel loading-state">Loading resources...</div>
      ) : (
        <div className="panel notes-list">
          {notes.map((note) => (
            <div className="note-row" key={note.id}>
              <div className="file-icon">
                <FileText size={17} />
              </div>
              <div>
                <b>{note.title}</b>
                <small>
                  {note.meta} · {note.subject}
                </small>
              </div>
              <span className="source">{note.source}</span>
              <Button>Open</Button>
              <button className="icon-button" title="Download resource" aria-label={`Download ${note.title}`} onClick={() => downloadResource(note)} disabled={!note.file && !note.description}>
                <Download size={16} />
              </button>
              <button
                className="icon-button danger"
                onClick={() => remove(note)}
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

export function ConnectedNotesSourceTabs() {
  const { notes, setNotes, subjects } = useWorkspace();
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState(null);
  const [subject, setSubject] = useState("");
  const [type, setType] = useState("NOTE");
  const [tab, setTab] = useState("personal");
  useEffect(() => {
    resourceService
      .list()
      .then((data) =>
        setNotes(
          asArray(data).map((item) => ({
            ...item,
            subject:
              subjects.find((subjectItem) => subjectItem.id === item.subject)
                ?.name || item.subject,
            source:
              item.source === "GOOGLE_CLASSROOM"
                ? "Google Classroom"
                : "My notes",
            meta: resourceMeta(item),
          })),
        ),
      )
      .catch((reason) => setError(reason.message))
      .finally(() => setLoading(false));
  }, [setNotes, subjects]);
  const upload = async () => {
    if (!file || !subject) return setError("Choose a file and subject first.");
    setUploading(true);
    setError("");
    const body = new FormData();
    body.append("file", file);
    body.append("title", file.name);
    body.append("subject", subject);
    body.append("resource_type", type);
    body.append("source", "USER_UPLOAD");
    try {
      const response = await resourceService.upload(body);
      setNotes((items) => [
        {
          ...response,
          subject:
            subjects.find((item) => item.id === response.subject)?.name ||
            response.subject,
          source: "My notes",
          meta: `${response.file_size || file.size} bytes`,
        },
        ...items,
      ]);
      setFile(null);
    } catch (reason) {
      setError(reason.message);
    } finally {
      setUploading(false);
    }
  };
  const remove = async (note) => {
    try {
      await resourceService.remove(note.id);
      setNotes((items) => items.filter((item) => item.id !== note.id));
    } catch (reason) {
      setError(reason.message);
    }
  };
  const visibleNotes = notes.filter((note) =>
    tab === "classroom"
      ? note.source === "Google Classroom"
      : note.source !== "Google Classroom",
  );
  return (
    <>
      <Header
        eyebrow="KNOWLEDGE BASE"
        title="Notes & resources"
        description="Keep your personal notes and Google Classroom materials in separate libraries."
      />
      {error && <ErrorMessage message={error} />}
      <div className="tabs compact source-tabs">
        <button
          className={tab === "personal" ? "active" : ""}
          onClick={() => setTab("personal")}
        >
          My Notes
        </button>
        <button
          className={tab === "classroom" ? "active" : ""}
          onClick={() => setTab("classroom")}
        >
          Google Classroom
        </button>
      </div>
      {tab === "personal" && (
        <div className="upload-strip">
          <div>
            <b>{file ? file.name : "Choose a resource to upload"}</b>
            <span>PDF, DOCX, PPTX, or image</span>
          </div>
          <select
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
          >
            <option value="">Choose subject</option>
            {subjects.map((item) => (
              <option value={item.id} key={item.id}>
                {item.name}
              </option>
            ))}
          </select>
          <select
            value={type}
            onChange={(event) => setType(event.target.value)}
          >
            <option value="NOTE">Note</option>
            <option value="SLIDES">Slides</option>
            <option value="DOCUMENT">Document</option>
            <option value="QUESTION_PAPER">Question paper</option>
            <option value="IMAGE">Image</option>
          </select>
          <label className="button">
            <Upload size={16} />
            Choose file
            <input
              hidden
              type="file"
              accept=".pdf,.doc,.docx,.ppt,.pptx,.png,.jpg,.jpeg,.webp"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
          </label>
          <Button primary onClick={upload} disabled={uploading}>
            {uploading ? "Uploading..." : "Upload"}
          </Button>
        </div>
      )}
      {loading ? (
        <div className="panel loading-state">Loading resources...</div>
      ) : (
        <div className="panel notes-list">
          {visibleNotes.length ? (
            visibleNotes.map((note) => (
              <div className="note-row" key={note.id}>
                <div className="file-icon">
                  <FileText size={17} />
                </div>
                <div>
                  <b>{note.title}</b>
                  <small>
                    {note.meta} · {note.subject}
                  </small>
                </div>
                <span
                  className={
                    tab === "classroom" ? "source classroom" : "source"
                  }
                >
                  {note.source}
                </span>
                <Button>Open</Button>
                <button className="icon-button" title="Download resource" aria-label={`Download ${note.title}`} onClick={() => downloadResource(note)} disabled={!note.file && !note.description}>
                  <Download size={16} />
                </button>
                {tab === "personal" && (
                  <button
                    className="icon-button danger"
                    onClick={() => remove(note)}
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            ))
          ) : (
            <div className="empty-state">
              <FileText size={22} />
              <h3>
                {tab === "classroom"
                  ? "No Classroom materials yet"
                  : "No personal notes yet"}
              </h3>
              <p>
                {tab === "classroom"
                  ? "Sync Google Classroom to import course materials here."
                  : "Upload a resource to build your personal library."}
              </p>
            </div>
          )}
        </div>
      )}
    </>
  );
}

export function ConnectedNotes() {
  const { notes, setNotes, subjects } = useWorkspace();
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState(null);
  const [subject, setSubject] = useState("");
  const [type, setType] = useState("NOTE");
  const [expanded, setExpanded] = useState({});
  const [selectedResource, setSelectedResource] = useState(null);
  useEffect(() => {
    resourceService
      .list()
      .then((data) =>
        setNotes(
          asArray(data).map((item) => ({
            ...item,
            subject:
              subjects.find((subjectItem) => subjectItem.id === item.subject)
                ?.name ||
              item.subject ||
              "Unsorted",
            source:
              item.source === "GOOGLE_CLASSROOM"
                ? "Google Classroom"
                : "My notes",
            meta: resourceMeta(item),
          })),
        ),
      )
      .catch((reason) => setError(reason.message))
      .finally(() => setLoading(false));
  }, [setNotes, subjects]);
  const upload = async () => {
    if (!file || !subject) return setError("Choose a file and subject first.");
    setUploading(true);
    setError("");
    const body = new FormData();
    body.append("file", file);
    body.append("title", file.name);
    body.append("subject", subject);
    body.append("resource_type", type);
    body.append("source", "USER_UPLOAD");
    try {
      const response = await resourceService.upload(body);
      setNotes((items) => [
        {
          ...response,
          subject:
            subjects.find((item) => item.id === response.subject)?.name ||
            response.subject,
          source: "My notes",
          meta: `${response.file_size || file.size} bytes`,
        },
        ...items,
      ]);
      setFile(null);
    } catch (reason) {
      setError(reason.message);
    } finally {
      setUploading(false);
    }
  };
  const remove = async (note) => {
    try {
      await resourceService.remove(note.id);
      setNotes((items) => items.filter((item) => item.id !== note.id));
    } catch (reason) {
      setError(reason.message);
    }
  };
  const groups = [
    ...new Set(notes.map((note) => note.subject || "Unsorted")),
  ].sort();
  return (
    <>
      <Header
        eyebrow="KNOWLEDGE BASE"
        title="Notes & resources"
        description="Organized by subject, with your notes and Classroom materials kept together."
      />
      {error && <ErrorMessage message={error} />}
      <div className="upload-strip">
        <div>
          <b>{file ? file.name : "Choose a resource to upload"}</b>
          <span>PDF, DOCX, PPTX, or image</span>
        </div>
        <select
          value={subject}
          onChange={(event) => setSubject(event.target.value)}
        >
          <option value="">Choose subject</option>
          {subjects.map((item) => (
            <option value={item.id} key={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <select value={type} onChange={(event) => setType(event.target.value)}>
          <option value="NOTE">Note</option>
          <option value="SLIDES">Slides</option>
          <option value="DOCUMENT">Document</option>
          <option value="QUESTION_PAPER">Question paper</option>
          <option value="IMAGE">Image</option>
        </select>
        <label className="button">
          <Upload size={16} />
          Choose file
          <input
            hidden
            type="file"
            accept=".pdf,.doc,.docx,.ppt,.pptx,.png,.jpg,.jpeg,.webp"
            onChange={(event) => setFile(event.target.files?.[0] || null)}
          />
        </label>
        <Button primary onClick={upload} disabled={uploading}>
          {uploading ? "Uploading..." : "Upload"}
        </Button>
      </div>
      {loading ? (
        <div className="panel loading-state">Loading resources...</div>
      ) : (
        <div className="subject-folders">
          {groups.map((group) => {
            const groupNotes = notes.filter(
              (note) => (note.subject || "Unsorted") === group,
            );
            const isOpen = expanded[group] !== false;
            return (
              <section className="panel subject-folder" key={group}>
                <button
                  className="subject-folder-head"
                  onClick={() =>
                    setExpanded((value) => ({ ...value, [group]: !isOpen }))
                  }
                >
                  <span>
                    <FileText size={17} />
                    <strong>{group}</strong>
                  </span>
                  <small>
                    {groupNotes.length}{" "}
                    {groupNotes.length === 1 ? "resource" : "resources"}
                  </small>
                  <ChevronRight
                    size={17}
                    className={isOpen ? "folder-open" : ""}
                  />
                </button>
                {isOpen && (
                  <div className="subject-folder-list">
                    {groupNotes.map((note) => (
                      <div className="note-row" key={note.id}>
                        <div className="file-icon">
                          <FileText size={17} />
                        </div>
                        <div>
                          <b>{note.title}</b>
                          <small>{note.meta}</small>
                        </div>
                        <span
                          className={
                            note.source === "Google Classroom"
                              ? "source classroom"
                              : "source"
                          }
                        >
                          {note.source}
                        </span>
                        <Button onClick={() => setSelectedResource(note)}>Open</Button>
                        <button className="icon-button" title="Download resource" aria-label={`Download ${note.title}`} onClick={() => downloadResource(note)} disabled={!note.file && !note.description}>
                          <Download size={16} />
                        </button>
                        {note.source !== "Google Classroom" && (
                          <button
                            className="icon-button danger"
                            onClick={() => remove(note)}
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      )}
      {selectedResource && (
        <ResourceViewer resource={selectedResource} onClose={() => setSelectedResource(null)} />
      )}
    </>
  );
}

export function ConnectedFocus({ active, setActive }) {
  const [seconds, setSeconds] = useState(45 * 60);
  const [paused, setPaused] = useState(false);
  const [session, setSession] = useState(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  useEffect(() => {
    studySessionService
      .list()
      .then((data) => {
        const current = asArray(data).find((item) => item.status === "ACTIVE");
        if (current) {
          setSession(current);
          setActive(true);
        }
      })
      .catch(() => null);
  }, [setActive]);
  useEffect(() => {
    if (!active || paused || seconds === 0) return undefined;
    const timer = setInterval(() => setSeconds((value) => value - 1), 1000);
    return () => clearInterval(timer);
  }, [active, paused, seconds]);
  const start = async () => {
    if (session) return setActive(true);
    try {
      const [subjectsResponse, topicsResponse] = await Promise.all([
        get("/subjects/"),
        get("/topics/"),
      ]);
      const subjects = asArray(subjectsResponse);
      const topics = asArray(topicsResponse);
      if (!subjects[0])
        throw new Error("Create a subject before starting focus.");
      const response = await studySessionService.create({
        subject: subjects[0].id,
        topic:
          topics.find((item) => item.subject === subjects[0].id)?.id || null,
        planned_minutes: 45,
        status: "ACTIVE",
        started_at: new Date().toISOString(),
      });
      setSession(response);
      setActive(true);
      setPaused(false);
    } catch (reason) {
      setError(reason.message);
    }
  };
  const finish = async (status) => {
    if (!session) return;
    try {
      const response = await studySessionService.update(session.id, {
        status,
        actual_minutes: Math.max(0, 45 - Math.ceil(seconds / 60)),
        ended_at: new Date().toISOString(),
      });
      setSession(response);
      setActive(false);
      if (status === "COMPLETED") navigate("/knowledge-check");
    } catch (reason) {
      setError(reason.message);
    }
  };
  const mins = String(Math.floor(seconds / 60)).padStart(2, "0");
  const secs = String(seconds % 60).padStart(2, "0");
  return (
    <div className="focus-page">
      <div className="focus-top">
        <div>
          <p className="eyebrow">FOCUS GUARDIAN</p>
          <h1>Make this block count.</h1>
          <p className="muted lead">
            One clear topic. No tab switching. RISE has the edges covered.
          </p>
        </div>
        <div className="focus-status">
          <span className="live-dot">
            ●{" "}
            {active
              ? paused
                ? "SESSION PAUSED"
                : "SESSION ACTIVE"
              : "READY TO FOCUS"}
          </span>
          <small>Transport Layer · Computer Networks</small>
        </div>
      </div>
      {error && <ErrorMessage message={error} />}
      <div className="timer-panel">
        <div className="timer-ring">
          <div>
            <span>
              {mins}:{secs}
            </span>
            <small>remaining</small>
          </div>
        </div>
        <p className="timer-label">
          COMPUTER NETWORKS <span>/</span> TRANSPORT LAYER
        </p>
        <div className="timer-controls">
          {!active ? (
            <Button primary onClick={start} icon={Play}>
              Start focus
            </Button>
          ) : (
            <>
              <Button onClick={() => setPaused(!paused)}>
                {paused ? "Resume" : "Pause"}
              </Button>
              <Button
                primary
                onClick={() => finish("COMPLETED")}
                icon={CircleCheck}
              >
                Finish focus
              </Button>
              <Button onClick={() => finish("ABANDONED")}>Abandon</Button>
            </>
          )}
          <Button
            onClick={() => {
              setSeconds(45 * 60);
              setPaused(false);
            }}
            icon={RefreshCw}
          >
            Reset
          </Button>
        </div>
      </div>
      <div className="guardian-grid">
        <div className="guardian panel">
          <h2>Protected space</h2>
          <p>Focus Mode ACTIVE</p>
          <span>
            <CircleCheck size={15} /> RISE
          </span>
          <span>
            <CircleCheck size={15} /> Notes
          </span>
          <span>
            <CircleCheck size={15} /> Classroom
          </span>
        </div>
        <div className="guardian blocked panel">
          <h2>Distractions</h2>
          <span>
            <X size={15} /> YouTube
          </span>
          <span>
            <X size={15} /> Instagram
          </span>
          <span>
            <X size={15} /> Reddit
          </span>
        </div>
      </div>
    </div>
  );
}

export function ConnectedOnboarding() {
  const [step, setStep] = useState(1);
  const [subjects, setSubjects] = useState([]);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();
  useEffect(() => {
    subjectService
      .list()
      .then((data) => setSubjects(asArray(data)))
      .catch(() => null);
  }, []);
  const add = () => {
    if (name.trim()) {
      setSubjects((items) => [...items, { name: name.trim(), pending: true }]);
      setName("");
    }
  };
  const continueStep = async () => {
    if (step === 1) {
      setSaving(true);
      try {
        const semesters = asArray(await semesterService.list());
        const semester =
          semesters.find((item) => item.is_current) || semesters[0];
        const saved = [];
        for (const item of subjects) {
          if (item.id && !item.pending) {
            saved.push(item);
            continue;
          }
          const response = await subjectService.create({
            semester: semester.id,
            name: item.name,
            code: item.name.slice(0, 3).toUpperCase(),
            difficulty: "MEDIUM",
            target_grade: "A",
            color: "#9733EE",
            icon: "book-open",
          });
          saved.push(response);
        }
        setSubjects(saved);
        setStep(2);
      } finally {
        setSaving(false);
      }
    } else if (step < 7) setStep(step + 1);
    else navigate("/");
  };
  return (
    <div className="onboarding">
      <div className="onboard-top">
        <Link to="/login" className="brand">
          <div className="brand-mark">R</div>
          <strong>RISE</strong>
        </Link>
        <span>Step {step} of 7</span>
      </div>
      <div className="step-progress">
        <span style={{ width: `${(step / 7) * 100}%` }} />
      </div>
      <main className="onboard-main">
        <div className="onboard-copy">
          <p className="eyebrow">BUILDING YOUR WORLD</p>
          <h1>
            {step === 7
              ? "RISE understands your semester."
              : "Let’s build your academic world."}
          </h1>
          <p>Backend-connected setup. Your progress is saved as you go.</p>
        </div>
        <div className="onboard-card">
          {step === 1 ? (
            <>
              <h2>Create your subjects</h2>
              <p className="muted">
                Subjects already saved to Django are reused.
              </p>
              <div className="subject-input">
                <input
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Add a subject..."
                />
                <button onClick={add}>
                  <Plus size={17} />
                </button>
              </div>
              <div className="onboard-subjects">
                {subjects.map((item) => (
                  <div key={item.id || item.name}>
                    {item.name}
                    <small>{item.pending ? "Ready to save" : "Saved"}</small>
                  </div>
                ))}
              </div>
            </>
          ) : step === 2 ? (
            <>
              <h2>Upload your syllabus</h2>
              <p className="muted">
                Upload a PDF, DOCX, or image. Processing remains UPLOADED in
                Phase 2.
              </p>
              <label className="drop-zone">
                <Upload size={24} />
                <b>Choose syllabus</b>
                <input
                  hidden
                  type="file"
                  accept=".pdf,.doc,.docx,.png,.jpg"
                  onChange={async (event) => {
                    const file = event.target.files?.[0];
                    if (!file) return;
                    const semesters = asArray(await semesterService.list());
                    const form = new FormData();
                    form.append(
                      "semester",
                      (
                        semesters.find((item) => item.is_current) ||
                        semesters[0]
                      ).id,
                    );
                    form.append("title", file.name);
                    form.append("file", file);
                    await syllabusService.upload(form);
                  }}
                />
              </label>
            </>
          ) : step === 7 ? (
            <div className="onboard-summary">
              <b>
                {subjects.length}
                <small>Subjects</small>
              </b>
              <b>
                27<small>Topics</small>
              </b>
              <b>
                4<small>Exams</small>
              </b>
              <b>
                12<small>Tasks</small>
              </b>
              <b>
                38<small>Resources</small>
              </b>
            </div>
          ) : (
            <>
              <h2>
                {
                  [
                    "",
                    "",
                    "Study materials",
                    "Exam timetable",
                    "College timetable",
                    "Google Classroom",
                    "Google Calendar",
                  ][step]
                }
              </h2>
              <p className="muted">
                This step is ready for backend records and can be completed
                later.
              </p>
            </>
          )}
        </div>
        <div className="onboard-actions">
          <button
            className="skip"
            onClick={() => (step < 7 ? setStep(step + 1) : navigate("/"))}
          >
            Skip for now
          </button>
          <Button primary onClick={continueStep} disabled={saving}>
            {saving
              ? "Saving..."
              : step === 7
                ? "Generate My Plan"
                : "Continue"}{" "}
            <ChevronRight size={16} />
          </Button>
        </div>
      </main>
    </div>
  );
}
