/* eslint-disable react-hooks/rules-of-hooks, no-unused-vars, no-func-assign */
import { useEffect, useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";
import { motion } from "framer-motion";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import {
  LayoutDashboard,
  BookOpen,
  CheckSquare,
  FileText,
  CalendarDays,
  Timer,
  Brain,
  ClipboardCheck,
  TrendingUp,
  Settings,
  Plug,
  Bell,
  Search,
  Plus,
  ArrowUpRight,
  Sparkles,
  Upload,
  MoreHorizontal,
  Play,
  ChevronRight,
  Menu,
  X,
  CircleCheck,
  Clock3,
  Zap,
  Send,
  RefreshCw,
  Trash2,
  Pencil,
  Filter,
  Target,
  Trophy,
  LoaderCircle,
  RotateCcw,
} from "lucide-react";
import {
  mockAnalytics,
  mockEvents,
  mockMaterials,
  mockNotes,
  mockQuiz,
  mockStudent,
  mockSubjects,
  mockTasks,
} from "./data/mockData";
import {
  aiService,
  classroomService,
  plannerService,
} from "./services/mockServices";
import { firebaseAuthService } from "./services/firebase";
import {
  ConnectedFocus as ConnectedFocusPage,
  ConnectedNotes as ConnectedNotesPage,
  ConnectedSubjects as ConnectedSubjectsPage,
  ConnectedTasks as ConnectedTasksPage,
} from "./ConnectedPages";
import ConnectedOnboardingPage from "./ConnectedOnboardingFinal";
import GoogleIntegrationPage from "./GoogleIntegration";
import ConnectedTutorPage from "./ConnectedTutor";
import PlannerPage from "./PlannerPage";
import { ClayAnalytics, ClayDashboard, ClaySettings } from "./ClayPages";
import ClayFocusPage from "./ClayFocus";
import { useWorkspace, WorkspaceContext } from "./context/WorkspaceContext";
import { useAuth } from "./context/auth";
import "./interactionBridge";
import "./sidebar.css";
import "./avatar.css";
import "./product.css";
import "./search.css";
import "./connected.css";
import "./clay.css";

LegacyPlanner = PlannerPage;
HomeDashboard = ClayDashboard;
Progress = ClayAnalytics;
SettingsPage = ClaySettings;

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/planner", label: "Timetable", icon: CalendarDays },
  { to: "/tutor", label: "Study Coach", icon: Brain },
  { to: "/progress", label: "Analytics", icon: TrendingUp },
  { to: "/subjects", label: "My Subjects", icon: BookOpen },
  { to: "/tasks", label: "Tasks", icon: CheckSquare },
  { to: "/notes", label: "Notes & Resources", icon: FileText },
  { to: "/tests", label: "Tests", icon: ClipboardCheck },
  { to: "/focus", label: "Focus", icon: Timer },
];
const Button = ({
  children,
  primary = false,
  onClick,
  className = "",
  icon: Icon,
  disabled = false,
}) => (
  <button
    disabled={disabled}
    onClick={onClick}
    className={`button ${primary ? "button-primary" : ""} ${className}`}
  >
    {Icon && <Icon size={16} />} {children}
  </button>
);
const PageHeader = ({ eyebrow, title, description, action }) => (
  <div className="page-header">
    <div>
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      {description && <p className="muted lead">{description}</p>}
    </div>
    {action}
  </div>
);
const ProgressBar = ({ value, color = "#9733EE" }) => (
  <div className="progress-track">
    <span style={{ width: `${value}%`, background: color }} />
  </div>
);
const Priority = ({ children, onClick }) => (
  <button onClick={onClick} className={`priority ${children?.toLowerCase()}`}>
    {children}
  </button>
);
function SectionHead({ eyebrow, title, link }) {
  return (
    <div className="section-head">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      {link && (
        <Link to={link} className="text-link">
          View all <ArrowUpRight size={15} />
        </Link>
      )}
    </div>
  );
}
function Stat({ label, value, trend, icon: Icon, accent = "purple" }) {
  return (
    <div className="stat">
      <div className={`stat-icon ${accent}`}>
        <Icon size={18} />
      </div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small className="trend">{trend}</small>
      </div>
    </div>
  );
}

function App() {
  const [subjects, setSubjects] = useState([...mockSubjects]);
  const [tasks, setTasks] = useState(mockTasks);
  const [notes, setNotes] = useState(mockNotes);
  const [mastery, setMastery] = useState({});
  const [integrations, setIntegrations] = useState({
    classroom: false,
    calendar: false,
  });
  const [notifications, setNotifications] = useState([
    { id: 1, text: "CN Lab Report is due tomorrow", tone: "red" },
    { id: 2, text: "New Classroom material added", tone: "purple" },
  ]);
  const value = {
    subjects,
    setSubjects,
    tasks,
    setTasks,
    notes,
    setNotes,
    mastery,
    setMastery,
    integrations,
    setIntegrations,
    notifications,
    setNotifications,
  };
  return (
    <WorkspaceContext.Provider value={value}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/onboarding" element={<ConnectedOnboardingPage />} />
          <Route path="*" element={<Shell />} />
        </Routes>
      </BrowserRouter>
    </WorkspaceContext.Provider>
  );
}
function Shell() {
  const [open, setOpen] = useState(false);
  const [focus, setFocus] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const navigate = useNavigate();
  const { tasks, _subjects, _integrations, notifications } = useWorkspace();
  return (
    <div className="app-shell">
      <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">R</div>
          <div>
            <strong>RISE</strong>
            <small>Real-time study engine</small>
          </div>
          <button
            className="icon-button mobile-only"
            onClick={() => setOpen(false)}
            aria-label="Close navigation"
          >
            <X size={18} />
          </button>
        </div>
        <nav>
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              onClick={() => setOpen(false)}
            >
              <Icon size={17} />
              <span>{label}</span>
              {label === "Tasks" && (
                <em>
                  {tasks.filter((task) => task.status !== "completed").length}
                </em>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="nav-section">
          <span>WORKSPACE</span>
          <NavLink to="/integrations">
            <Plug size={17} />
            Integrations
          </NavLink>
          <NavLink to="/settings">
            <Settings size={17} />
            Settings
          </NavLink>
        </div>
        <div className="profile">
          <div className="avatar">AM</div>
          <div>
            <strong>{mockStudent.name}</strong>
            <small>{mockStudent.semester}</small>
          </div>
          <MoreHorizontal size={17} />
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <button
            className="icon-button mobile-only"
            onClick={() => setOpen(true)}
            aria-label="Open navigation"
          >
            <Menu size={20} />
          </button>
          <div className="breadcrumb">
            Monday, August 17 <span>/</span> <b>Semester 5</b>
          </div>
          <div className="top-actions">
            <button className="search">
              <Search size={16} />
              Search <kbd>⌘ K</kbd>
            </button>
            <div className="notification-wrap">
              <button
                className="icon-button"
                aria-label="Notifications"
                onClick={() => setShowNotifications(!showNotifications)}
              >
                <Bell size={18} />
                <i />
              </button>
              {showNotifications && (
                <div className="notification-pop">
                  {notifications.map((note) => (
                    <div key={note.id}>
                      <span className={`signal ${note.tone}`}>●</span>
                      {note.text}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="avatar small">AM</div>
          </div>
        </header>
        <div className="page-wrap">
          <Routes>
            <Route
              path="/"
              element={
                <HomeDashboard
                  setFocus={() => {
                    setFocus(true);
                    navigate("/focus");
                  }}
                />
              }
            />
            <Route path="/subjects" element={<ConnectedSubjectsPage />} />
            <Route path="/subjects/:id" element={<SubjectDetail />} />
            <Route path="/tasks" element={<ConnectedTasksPage />} />
            <Route path="/notes" element={<ConnectedNotesPage />} />
            <Route path="/planner" element={<LegacyPlanner />} />
            <Route
              path="/focus"
              element={<ClayFocusPage active={focus} setActive={setFocus} />}
            />
            <Route path="/knowledge-check" element={<KnowledgeCheck />} />
            <Route path="/tutor" element={<ConnectedTutorPage />} />
            <Route path="/tests" element={<Tests />} />
            <Route path="/progress" element={<Progress />} />
            <Route path="/integrations" element={<GoogleIntegrationPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<HomeDashboard />} />
          </Routes>
        </div>
      </main>
      <nav className="mobile-tabbar" aria-label="Primary navigation">
        {navItems.slice(0, 4).map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === "/"}>
            <Icon size={20} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}

function HomeDashboard({ setFocus }) {
  const { tasks, subjects } = useWorkspace();
  const openTasks = tasks.filter((task) => task.status !== "completed");
  const complete = (id) =>
    useWorkspace().setTasks((items) =>
      items.map((task) =>
        task.id === id ? { ...task, status: "completed" } : task,
      ),
    );
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <div className="welcome">
        <div>
          <p className="eyebrow">YOUR COMMAND CENTER</p>
          <h1>
            Good morning, {mockStudent.name.split(" ")[0]} <span>✦</span>
          </h1>
          <p className="muted lead">
            Here’s what matters today. Let’s make the next hour count.
          </p>
        </div>
        <div className="date-chip">
          <CalendarDays size={17} />
          <span>
            <b>MON</b> AUG 17
          </span>
        </div>
      </div>
      <div className="focus-banner">
        <div className="focus-copy">
          <div className="live-dot">● LIVE FOCUS</div>
          <h2>What should I do right now?</h2>
          <p>
            RISE found the best next step based on your exams, mastery, and
            available time.
          </p>
          <div className="focus-meta">
            <b>Computer Networks</b>
            <span>Transport Layer</span>
            <span>
              <Clock3 size={14} /> 45 min
            </span>
            <Priority
              onClick={() =>
                window.alert(
                  "Priority Score: 91\n\nExam urgency +30\nLow mastery +25\nSyllabus remaining +20\nAssignment deadline +10\nPast performance +6",
                )
              }
            >
              HIGH
            </Priority>
          </div>
          <Button primary onClick={setFocus} icon={Play}>
            Start Focus Session
          </Button>
        </div>
        <div className="focus-orbit">
          <div className="orbit-ring">
            <span>52%</span>
            <small>mastery</small>
          </div>
          <div className="orbit-label">
            +12 priority
            <br />
            <small>since yesterday</small>
          </div>
        </div>
      </div>
      <div className="dashboard-grid">
        <section className="panel">
          <SectionHead
            eyebrow="YOUR DAY"
            title="Today’s plan"
            link="/planner"
          />
          <Timeline />
        </section>
        <section className="panel risk-panel">
          <SectionHead
            eyebrow="KNOW YOUR EDGE"
            title="Academic risk"
            link="/progress"
          />
          {subjects.map((subject) => (
            <Link
              className="risk-row"
              to={`/subjects/${subject.id}`}
              key={subject.id}
            >
              <div
                className="subject-dot"
                style={{ background: subject.color }}
              >
                {subject.short}
              </div>
              <div className="risk-name">
                <b>{subject.name}</b>
                <small>{subject.priority} priority</small>
              </div>
              <div className="risk-meter">
                <ProgressBar
                  value={subject.risk}
                  color={
                    subject.risk > 80
                      ? "#EF6A6A"
                      : subject.risk > 60
                        ? "#E7984A"
                        : "#6DAA7A"
                  }
                />
              </div>
              <strong>{subject.risk}</strong>
              <ChevronRight size={15} />
            </Link>
          ))}
        </section>
      </div>
      <div className="dashboard-grid lower">
        <section className="panel">
          <SectionHead
            eyebrow="ACADEMIC INBOX"
            title="Upcoming deadlines"
            link="/tasks"
          />
          {openTasks.slice(0, 3).map((task) => (
            <TaskRow key={task.id} task={task} onComplete={complete} />
          ))}
        </section>
        <section className="insight">
          <div className="insight-head">
            <div className="spark">
              <Sparkles size={18} />
            </div>
            <span>RISE INSIGHT</span>
          </div>
          <h3>Your evening edge is real.</h3>
          <p>
            You perform best between 6–8 PM. I’ve moved your highest-risk CN
            revision into that window.
          </p>
          <Link to="/planner" className="button button-light">
            View adjusted plan <ArrowUpRight size={15} />
          </Link>
        </section>
      </div>
      <section className="panel materials">
        <SectionHead
          eyebrow="JUST IN"
          title="New from Google Classroom"
          link="/notes"
        />
        <div className="material-grid">
          {mockMaterials.map((material) => (
            <div className="material" key={material.title}>
              <div className="file-icon">
                <FileText size={18} />
              </div>
              <div>
                <b>{material.title}</b>
                <small>
                  {material.subject} · {material.time}
                </small>
              </div>
              <button className="icon-button">
                <ArrowUpRight size={16} />
              </button>
            </div>
          ))}
        </div>
      </section>
    </motion.div>
  );
}
function Timeline() {
  return (
    <div className="timeline">
      {mockEvents.map((event) => (
        <div className="timeline-row" key={event.time}>
          <time>{event.time}</time>
          <div className={`timeline-card ${event.type}`}>
            <div>
              <b>{event.title}</b>
              <small>{event.meta}</small>
            </div>
            <span>
              {event.type === "class" ? "COLLEGE" : event.type.toUpperCase()}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
function TaskRow({ task, onComplete }) {
  return (
    <div className="task-row">
      <button
        className="task-check"
        onClick={() => onComplete(task.id)}
        aria-label={`Complete ${task.title}`}
      >
        {task.status === "completed" && <CircleCheck size={17} />}
      </button>
      <div className="task-details">
        <b>{task.title}</b>
        <small>
          {task.subject} · {task.source}
        </small>
      </div>
      <div className="task-due">
        <b>{task.due}</b>
        <small>{task.estimate}</small>
      </div>
      <Priority
        onClick={() =>
          window.alert(
            `Priority Score: ${task.priority === "HIGH" ? 91 : 72}\n\nExam urgency +30\nLow mastery +25\nSyllabus remaining +20\nAssignment deadline +10\nPast performance +6`,
          )
        }
      >
        {task.priority}
      </Priority>
    </div>
  );
}

function MockSubjectsLegacy() {
  const { subjects, setSubjects } = useWorkspace();
  const [editing, setEditing] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [imported, setImported] = useState(false);
  const blank = {
    name: "",
    short: "NEW",
    color: "#9733EE",
    mastery: 0,
    risk: 50,
    priority: "MEDIUM",
    exam: "Sep 15",
    next: "First topic",
    units: [0, 0, 0, 0, 0],
    difficulty: "Medium",
    target: "A",
  };
  const [form, setForm] = useState(blank);
  const save = () => {
    if (!form.name.trim()) return;
    setSubjects((items) =>
      editing
        ? items.map((item) =>
            item.id === editing ? { ...form, id: editing } : item,
          )
        : [...items, { ...form, id: `subject-${Date.now()}` }],
    );
    setForm(blank);
    setEditing(null);
    setShowForm(false);
  };
  const edit = (subject) => {
    setForm(subject);
    setEditing(subject.id);
    setShowForm(true);
  };
  const remove = (id) =>
    setSubjects((items) => items.filter((item) => item.id !== id));
  const importClassroom = () => {
    setImported(true);
    setSubjects((items) =>
      items.some((item) => item.id === "math")
        ? items
        : [
            ...items,
            {
              ...blank,
              id: "math",
              name: "Mathematics",
              short: "MA",
              color: "#6c8cc7",
              mastery: 66,
              risk: 47,
              exam: "Sep 08",
              next: "Probability",
              units: [92, 80, 65, 50, 35],
            },
          ],
    );
  };
  return (
    <>
      <PageHeader
        eyebrow="ACADEMIC WORLD"
        title="My subjects"
        description="A living map of your semester, priorities, and progress."
        action={
          <div className="button-row">
            <Button onClick={importClassroom} icon={Plug}>
              {imported
                ? "Imported from Classroom"
                : "Import from Google Classroom"}
            </Button>
            <Button
              primary
              onClick={() => {
                setForm(blank);
                setEditing(null);
                setShowForm(true);
              }}
              icon={Plus}
            >
              Add subject
            </Button>
          </div>
        }
      />
      {showForm && (
        <div className="panel editor-panel">
          <SectionHead
            eyebrow={editing ? "EDIT SUBJECT" : "NEW SUBJECT"}
            title={editing ? "Tune this subject" : "Add a subject"}
          />
          <div className="form-grid">
            <label>
              Subject name
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g. Mathematics"
              />
            </label>
            <label>
              Exam date
              <input
                value={form.exam}
                onChange={(e) => setForm({ ...form, exam: e.target.value })}
              />
            </label>
            <label>
              Difficulty
              <select
                value={form.difficulty}
                onChange={(e) =>
                  setForm({ ...form, difficulty: e.target.value })
                }
              >
                <option>Easy</option>
                <option>Medium</option>
                <option>Hard</option>
              </select>
            </label>
            <label>
              Target grade
              <select
                value={form.target}
                onChange={(e) => setForm({ ...form, target: e.target.value })}
              >
                <option>A</option>
                <option>A+</option>
                <option>B</option>
              </select>
            </label>
          </div>
          <div className="button-row">
            <Button onClick={() => setShowForm(false)}>Cancel</Button>
            <Button primary onClick={save}>
              Save subject
            </Button>
          </div>
        </div>
      )}
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
                <MoreHorizontal size={18} />
              </div>
              <h2>{subject.name}</h2>
              <p className="muted">Next up · {subject.next}</p>
              <div className="mastery">
                <span>
                  Mastery <b>{subject.mastery}%</b>
                </span>
                <Priority>{subject.priority}</Priority>
              </div>
              <ProgressBar value={subject.mastery} color={subject.color} />
              <div className="subject-foot">
                <span>
                  Exam <b>{subject.exam}</b>
                </span>
                <span>
                  Units{" "}
                  <b>{subject.units.filter((unit) => unit >= 80).length}/5</b>
                </span>
              </div>
            </Link>
            <div className="card-actions">
              <button onClick={() => edit(subject)}>
                <Pencil size={14} /> Edit
              </button>
              <button onClick={() => remove(subject.id)}>
                <Trash2 size={14} /> Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

function SubjectDetail() {
  const { subjects, tasks, notes, mastery } = useWorkspace();
  const { id } = useParams();
  const subject = subjects.find((item) => item.id === id) || subjects[0];
  const [tab, setTab] = useState("Overview");
  const currentMastery = mastery[subject.id] || subject.mastery;
  const subjectNotes = notes.filter((note) => note.subject === subject.name);
  const subjectTasks = tasks.filter((task) => task.subject === subject.name);
  return (
    <>
      <PageHeader
        eyebrow="SUBJECT SPACE"
        title={subject.name}
        description="Everything RISE knows about this subject, in one focused view."
        action={
          <Button primary icon={Play}>
            Start study session
          </Button>
        }
      />
      <div className="subject-hero">
        <div
          className="subject-icon large"
          style={{ background: subject.color }}
        >
          {subject.short}
        </div>
        <div>
          <h2>{subject.name}</h2>
          <div className="inline-meta">
            <Priority>{subject.priority}</Priority>
            <span>Exam {subject.exam}</span>
            <span>Target {subject.target || "A"}</span>
          </div>
        </div>
        <div className="hero-mastery">
          <b>{currentMastery}%</b>
          <span>mastery</span>
        </div>
      </div>
      <div className="tabs">
        {[
          "Overview",
          "Topics",
          "My Notes",
          "Classroom",
          "Assignments",
          "Tests",
          "Progress",
        ].map((item) => (
          <button
            className={tab === item ? "active" : ""}
            onClick={() => setTab(item)}
            key={item}
          >
            {item}
          </button>
        ))}
      </div>
      {tab === "Overview" && (
        <div className="detail-grid">
          <section className="panel">
            <SectionHead
              eyebrow="AI RECOMMENDATION"
              title={`Focus on ${subject.next}`}
            />
            <p className="recommendation">
              Your exam is approaching and this topic is the largest remaining
              gap in your mastery map. One 45-minute session tonight will move
              the needle.
            </p>
            <Button primary icon={Play}>
              Study this topic
            </Button>
          </section>
          <section className="panel">
            <SectionHead eyebrow="SYLLABUS" title="Topic progress" />
            {subject.units.map((value, index) => (
              <div className="unit" key={index}>
                <span>Unit {index + 1}</span>
                <ProgressBar value={value} color={subject.color} />
                <b>{value}%</b>
              </div>
            ))}
          </section>
        </div>
      )}
      {tab === "Topics" && (
        <div className="panel tab-panel">
          <SectionHead eyebrow="SYLLABUS MAP" title="Topics to master" />
          {subject.units.map((value, index) => (
            <div className="topic-line" key={index}>
              <div>
                <b>Unit {index + 1}</b>
                <small>
                  {value >= 80
                    ? "Strong foundation"
                    : value > 0
                      ? "Needs another pass"
                      : "Not started"}
                </small>
              </div>
              <ProgressBar value={value} color={subject.color} />
              <strong>{value}%</strong>
            </div>
          ))}
        </div>
      )}
      {tab === "My Notes" && (
        <SubjectResources notes={subjectNotes} title="My Notes" />
      )}
      {tab === "Classroom" && (
        <SubjectResources
          notes={notes.filter(
            (note) =>
              note.subject === subject.name &&
              note.source === "Google Classroom",
          )}
          title="Google Classroom"
          classroom
        />
      )}
      {tab === "Assignments" && (
        <div className="panel tab-panel">
          <SectionHead eyebrow="ACADEMIC INBOX" title="Subject assignments" />
          {subjectTasks.length ? (
            subjectTasks.map((task) => (
              <TaskRow key={task.id} task={task} onComplete={() => {}} />
            ))
          ) : (
            <EmptyState
              title="No assignments yet"
              text="This subject is clear for now."
            />
          )}
        </div>
      )}
      {tab === "Tests" && (
        <div className="panel tab-panel">
          <SectionHead
            eyebrow="KNOWLEDGE CHECKS"
            title="Tests for {subject.name}"
          />
          <Button primary onClick={() => (window.location.href = "/tests")}>
            Open recommended tests
          </Button>
        </div>
      )}
      {tab === "Progress" && <Progress subjectId={subject.id} />}
    </>
  );
}
function SubjectResources({ notes, title, classroom = false }) {
  return (
    <div className="panel tab-panel">
      <SectionHead
        eyebrow={classroom ? "SOURCE: GOOGLE CLASSROOM" : "PERSONAL LIBRARY"}
        title={title}
      />
      {notes.length ? (
        notes.map((note) => (
          <div className="note-row" key={note.id}>
            <div className="file-icon">
              <FileText size={17} />
            </div>
            <div>
              <b>{note.title}</b>
              <small>
                {note.meta}
                {classroom ? " · Posted by Professor" : ""}
              </small>
            </div>
            <span className={classroom ? "source classroom" : "source"}>
              {classroom ? "Google Classroom" : "My notes"}
            </span>
            <Button>View</Button>
            <Button icon={Sparkles}>Add to Knowledge Base</Button>
          </div>
        ))
      ) : (
        <EmptyState
          title="No materials yet"
          text="Upload the first resource for this subject."
        />
      )}
    </div>
  );
}
function EmptyState({ title, text }) {
  return (
    <div className="empty-state">
      <Sparkles size={22} />
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

function MockTasksLegacy() {
  const { tasks, setTasks } = useWorkspace();
  const [filter, setFilter] = useState("All");
  const [source, setSource] = useState("All sources");
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const shown = tasks
    .filter(
      (task) =>
        filter === "All" ||
        (filter === "Completed"
          ? task.status === "completed"
          : filter === "Upcoming"
            ? task.status !== "completed"
            : task.status !== "completed"),
    )
    .filter((task) => source === "All sources" || task.source === source);
  const complete = (id) =>
    setTasks((items) =>
      items.map((item) =>
        item.id === id
          ? {
              ...item,
              status: item.status === "completed" ? "open" : "completed",
            }
          : item,
      ),
    );
  const create = () => {
    if (!title.trim()) return;
    setTasks((items) => [
      {
        id: Date.now(),
        title,
        subject: "Computer Networks",
        due: "Aug 22",
        estimate: "60 min",
        priority: "MEDIUM",
        source: "Manual",
        status: "open",
      },
      ...items,
    ]);
    setTitle("");
    setShowForm(false);
  };
  return (
    <>
      <PageHeader
        eyebrow="ACADEMIC INBOX"
        title="Tasks & deadlines"
        description="Assignments, exams, and important work in one clear runway."
        action={
          <Button primary icon={Plus} onClick={() => setShowForm(true)}>
            Create task
          </Button>
        }
      />
      {showForm && (
        <div className="panel quick-editor">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="What needs doing?"
            autoFocus
          />
          <Button onClick={() => setShowForm(false)}>Cancel</Button>
          <Button primary onClick={create}>
            Create
          </Button>
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
        <label className="filter-select">
          <Filter size={14} />
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            <option>All sources</option>
            <option>Google Classroom</option>
            <option>Manual</option>
            <option>RISE Tutor</option>
          </select>
        </label>
      </div>
      <div className="panel task-list">
        {shown.length ? (
          shown.map((task) => (
            <TaskRow key={task.id} task={task} onComplete={complete} />
          ))
        ) : (
          <EmptyState
            title="You’re all caught up"
            text="No tasks match this view."
          />
        )}
      </div>
    </>
  );
}

function MockNotesLegacy() {
  const { notes, setNotes, subjects } = useWorkspace();
  const [query, setQuery] = useState("");
  const [subject, setSubject] = useState("All subjects");
  const [classroom, setClassroom] = useState(false);
  const [uploading, setUploading] = useState(false);
  const upload = () => {
    setUploading(true);
    setTimeout(() => {
      setNotes((items) => [
        {
          id: Date.now(),
          title: "New study material.pdf",
          type: "PDF",
          meta: "Uploaded just now · 8 pages",
          subject: "Computer Networks",
          source: "My notes",
        },
        ...items,
      ]);
      setUploading(false);
    }, 650);
  };
  const filtered = notes
    .filter((note) => !classroom || note.source === "Google Classroom")
    .filter((note) => note.title.toLowerCase().includes(query.toLowerCase()))
    .filter((note) => subject === "All subjects" || note.subject === subject);
  const remove = (id) =>
    setNotes((items) => items.filter((note) => note.id !== id));
  return (
    <>
      <PageHeader
        eyebrow="KNOWLEDGE BASE"
        title="Notes & resources"
        description="Your study library, classroom materials, and AI-ready knowledge."
        action={
          <Button primary onClick={upload} icon={Upload}>
            {uploading ? "Processing..." : "Upload material"}
          </Button>
        }
      />
      <div className="upload-strip">
        <div className="upload-icon">
          <Upload size={20} />
        </div>
        <div>
          <b>Drop PDF, DOCX, PPTX, or image files here</b>
          <span>
            RISE will organize them by subject and make them available to Tutor.
          </span>
        </div>
        <Button onClick={upload}>Browse files</Button>
      </div>
      <div className="resource-toolbar">
        <label className="note-search">
          <Search size={15} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search your knowledge base"
          />
        </label>
        <select value={subject} onChange={(e) => setSubject(e.target.value)}>
          <option>All subjects</option>
          {subjects.map((item) => (
            <option key={item.id}>{item.name}</option>
          ))}
        </select>
        <Button onClick={() => setClassroom(!classroom)} icon={Plug}>
          {classroom ? "Showing Classroom" : "Show Classroom"}
        </Button>
      </div>
      <div className="section-head page-section">
        <div>
          <p className="eyebrow">
            {classroom ? "GOOGLE CLASSROOM" : "MY NOTES"}
          </p>
          <h2>{filtered.length} resources</h2>
        </div>
        <Button>Sort by recent</Button>
      </div>
      <div className="panel notes-list">
        {filtered.length ? (
          filtered.map((note) => (
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
                  note.source === "Google Classroom"
                    ? "source classroom"
                    : "source"
                }
              >
                {note.source}
              </span>
              <Button>Open</Button>
              <Button icon={Sparkles}>AI</Button>
              <button
                className="icon-button danger"
                onClick={() => remove(note.id)}
                aria-label={`Delete ${note.title}`}
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))
        ) : (
          <EmptyState
            title="Upload your first study material"
            text="Your academic journey starts with one useful resource."
          />
        )}
      </div>
    </>
  );
}

function LegacyPlanner() {
  const [view, setView] = useState("Week");
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const generate = async () => {
    setGenerating(true);
    await plannerService.generate();
    setGenerating(false);
    setGenerated(true);
  };
  return (
    <>
      <PageHeader
        eyebrow="YOUR WEEK, INTELLIGENTLY ARRANGED"
        title="Study planner"
        description="A plan that adapts to your real schedule, not an idealized version of it."
        action={
          <Button primary onClick={generate} icon={Sparkles}>
            Generate AI plan
          </Button>
        }
      />
      {generating ? (
        <div className="ai-loading panel">
          <div className="loading-orb">
            <Sparkles size={22} />
          </div>
          <h2>Analyzing your semester...</h2>
          <p>RISE is checking every signal before committing your time.</p>
          <div className="loading-steps">
            <span>
              <CircleCheck size={15} /> Exam timetable
            </span>
            <span>
              <CircleCheck size={15} /> College timetable
            </span>
            <span>
              <CircleCheck size={15} /> Syllabus + mastery
            </span>
            <span className="active">
              <RefreshCw size={15} /> Generating optimal plan
            </span>
          </div>
        </div>
      ) : (
        <>
          <div className="planner-tabs">
            {["Day", "Week", "Semester"].map((item) => (
              <button
                className={view === item ? "active" : ""}
                onClick={() => setView(item)}
                key={item}
              >
                {item}
                <small>
                  {item === "Week"
                    ? "Aug 17–23"
                    : item === "Day"
                      ? "Mon, Aug 17"
                      : "5 exams ahead"}
                </small>
              </button>
            ))}
          </div>
          {view === "Week" && (
            <div className="planner-layout">
              <div className="week-grid">
                {["MON 17", "TUE 18", "WED 19", "THU 20", "FRI 21"].map(
                  (day, i) => (
                    <div className="day-column" key={day}>
                      <b>{day}</b>
                      <div className="day-line" />
                      {(i === 0
                        ? mockEvents.slice(0, 4)
                        : i === 1
                          ? [
                              {
                                time: "09:00",
                                title: "Python · Async patterns",
                                type: "study",
                                meta: "60 min",
                              },
                              {
                                time: "14:00",
                                title: "College · Operating Systems",
                                type: "class",
                                meta: "Room 102",
                              },
                            ]
                          : [
                              {
                                time: "16:00",
                                title: "Revision block",
                                type: "study",
                                meta: "45 min",
                              },
                            ]
                      ).map((event) => (
                        <div
                          className={`planner-event ${event.type}`}
                          key={event.time + event.title}
                        >
                          <small>{event.time}</small>
                          <b>{event.title.replace("College · ", "")}</b>
                          <span>{event.meta}</span>
                        </div>
                      ))}
                    </div>
                  ),
                )}
              </div>
              <div className="adaptive panel">
                <SectionHead
                  eyebrow="ADAPTIVE PLAN"
                  title={
                    accepted ? "Plan updated" : "Your plan needs adjustment"
                  }
                />
                <p>
                  You missed <b>Computer Networks, 4:00–5:00 PM</b>. RISE
                  adjusted your schedule.
                </p>
                <div className="change">
                  <span>Moved</span>
                  <b>Python revision</b>
                  <small>Tomorrow · 5:00 PM</small>
                </div>
                <div className="change added">
                  <span>Added</span>
                  <b>Computer Networks</b>
                  <small>Tomorrow · 6:00 PM</small>
                </div>
                <div className="button-row">
                  <Button icon={Pencil}>Edit</Button>
                  <Button primary onClick={() => setAccepted(true)}>
                    {accepted ? "Accepted" : "Accept"}
                  </Button>
                </div>
                {accepted && (
                  <small className="success">
                    <CircleCheck size={14} /> Plan updated around your missed
                    session
                  </small>
                )}
              </div>
            </div>
          )}
          {view === "Day" && (
            <div className="panel">
              <SectionHead
                eyebrow="MONDAY, AUGUST 17"
                title="Your focused day"
              />
              <Timeline />
            </div>
          )}
          {view === "Semester" && (
            <div className="panel semester-plan">
              <SectionHead
                eyebrow="SEMESTER RUNWAY"
                title="Exams and milestones"
              />
              {[
                "Computer Networks · Aug 25",
                "Database Systems · Aug 28",
                "Operating Systems · Aug 31",
                "Python Programming · Sep 04",
              ].map((item) => (
                <div className="semester-row" key={item}>
                  <CalendarDays size={16} />
                  <b>{item}</b>
                  <span>Plan ready</span>
                </div>
              ))}
            </div>
          )}
          {generated && (
            <div className="success plan-success">
              <CircleCheck size={15} /> Optimal plan generated from your
              semester signals.
            </div>
          )}
        </>
      )}
    </>
  );
}

function MockFocusLegacy({ active, setActive }) {
  const navigate = useNavigate();
  const [seconds, setSeconds] = useState(45 * 60);
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    if (!active || paused || seconds === 0) return undefined;
    const timer = setInterval(() => setSeconds((value) => value - 1), 1000);
    return () => clearInterval(timer);
  }, [active, paused, seconds]);
  const finish = () => {
    setActive(false);
    navigate("/knowledge-check");
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
            <Button
              primary
              onClick={() => {
                setActive(true);
                setPaused(false);
              }}
              icon={Play}
            >
              Start focus
            </Button>
          ) : (
            <>
              <Button
                onClick={() => setPaused(!paused)}
                icon={paused ? Play : Timer}
              >
                {paused ? "Resume" : "Pause"}
              </Button>
              <Button primary onClick={finish} icon={CircleCheck}>
                Finish focus
              </Button>
            </>
          )}
          <Button
            onClick={() => {
              setSeconds(45 * 60);
              setActive(false);
              setPaused(false);
            }}
            icon={RotateCcw}
          >
            Reset
          </Button>
        </div>
      </div>
      <div className="guardian-grid">
        <div className="guardian panel">
          <SectionHead eyebrow="FOCUS MODE" title="Protected space" />
          {["RISE", "Your Notes", "Google Classroom", "Study Resources"].map(
            (item) => (
              <span key={item}>
                <CircleCheck size={15} />
                {item}
              </span>
            ),
          )}
        </div>
        <div className="guardian blocked panel">
          <SectionHead eyebrow="BLOCKED FOR NOW" title="Distractions" />
          {["YouTube", "Instagram", "Reddit", "Gaming"].map((item) => (
            <span key={item}>
              <X size={15} />
              {item}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
function KnowledgeCheck() {
  const { setMastery } = useWorkspace();
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const submit = () => {
    setSubmitted(true);
    setMastery((value) => ({ ...value, cn: 59 }));
  };
  return (
    <>
      <PageHeader
        eyebrow="SESSION COMPLETE"
        title="Knowledge check"
        description="Let’s make sure your focus became understanding."
      />
      {!submitted ? (
        <div className="quiz panel knowledge-quiz">
          <div className="quiz-top">
            <span>5 QUESTIONS</span>
            <span>Computer Networks · Transport Layer</span>
          </div>
          {[
            ...mockQuiz,
            {
              question: "Which protocol guarantees ordered delivery?",
              options: ["UDP", "TCP", "IP", "ARP"],
            },
            {
              question:
                "In your own words, why does congestion control matter?",
              options: ["Short answer"],
            },
            {
              question: "What does a three-way handshake establish?",
              options: [
                "A TCP connection",
                "A DNS record",
                "A subnet",
                "A firewall rule",
              ],
            },
          ].map((question, index) => (
            <div className="question-block" key={question.question}>
              <b>Question {index + 1}</b>
              <h2>{question.question}</h2>
              {question.options.length === 1 ? (
                <textarea
                  aria-label="Short answer"
                  placeholder="Write a concise answer..."
                  onChange={(e) =>
                    setAnswers({ ...answers, [index]: e.target.value })
                  }
                />
              ) : (
                <div className="options">
                  {question.options.map((option, optionIndex) => (
                    <button
                      className={
                        answers[index] === optionIndex ? "selected" : ""
                      }
                      onClick={() =>
                        setAnswers({ ...answers, [index]: optionIndex })
                      }
                      key={option}
                    >
                      <span>{String.fromCharCode(65 + optionIndex)}</span>
                      {option}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
          <Button primary onClick={submit}>
            Submit knowledge check <ChevronRight size={16} />
          </Button>
        </div>
      ) : (
        <div className="knowledge-result panel">
          <div className="result-mark">
            <Trophy size={25} />
          </div>
          <p className="eyebrow">FOCUS OBJECTIVE COMPLETED</p>
          <h2>Strong work. You’re retaining more.</h2>
          <div className="score-line">
            <b>4/5</b>
            <span>
              Knowledge Score
              <br />
              <strong>82%</strong>
            </span>
            <span>
              Mastery
              <br />
              <strong>52% → 59%</strong>
            </span>
          </div>
          <p className="muted">
            Your Computer Networks priority has been recalculated, and
            tomorrow’s plan is updated.
          </p>
          <Link to="/planner" className="button button-primary">
            View updated plan <ArrowUpRight size={15} />
          </Link>
        </div>
      )}
    </>
  );
}

function MockTutorLegacy() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: `Hey ${mockStudent.name.split(" ")[0]}. I’ve mapped your semester. What should we make clearer today?`,
    },
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const ask = async (prompt) => {
    const text = prompt || input;
    if (!text) return;
    setInput("");
    setMessages((items) => [...items, { role: "user", content: text }]);
    setTyping(true);
    const response = await aiService.ask(text);
    setTyping(false);
    setMessages((items) => [...items, response]);
  };
  return (
    <>
      <PageHeader
        eyebrow="YOUR ACADEMIC COACH"
        title="RISE Tutor"
        description="A focused conversation with the intelligence behind your plan."
      />
      <div className="tutor-layout">
        <section className="chat panel">
          <div className="chat-head">
            <div className="tutor-avatar">
              <Sparkles size={18} />
            </div>
            <div>
              <b>RISE Tutor</b>
              <small>Knows your subjects, notes, and goals</small>
            </div>
            <span className="online">Online</span>
          </div>
          <div className="messages">
            {messages.map((message, index) => (
              <div className={`message ${message.role}`} key={index}>
                <div className="message-bubble">
                  {message.content}
                  {message.role === "assistant" && (
                    <small className="citation">
                      Based on: CN Unit 4 Notes.pdf · Page 12
                    </small>
                  )}
                </div>
              </div>
            ))}
            {typing && (
              <div className="message assistant">
                <div className="message-bubble typing">
                  <LoaderCircle size={14} /> RISE is thinking...
                </div>
              </div>
            )}
          </div>
          <div className="quick-actions">
            {[
              "Explain this topic",
              "Summarize my notes",
              "Quiz me",
              "What should I study?",
              "Find my weak topics",
              "Create revision plan",
            ].map((item) => (
              <button onClick={() => ask(item)} key={item}>
                {item}
              </button>
            ))}
          </div>
          <div className="chat-input">
            <input
              aria-label="Ask RISE"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => event.key === "Enter" && ask()}
              placeholder="Ask RISE anything about your semester..."
            />
            <button onClick={() => ask()} aria-label="Send message">
              <Send size={17} />
            </button>
          </div>
        </section>
        <aside className="source-panel panel">
          <p className="eyebrow">YOUR SOURCES</p>
          <h2>Grounded in your world</h2>
          <p className="muted">
            RISE Tutor cites the materials it uses so you can trust every
            answer.
          </p>
          {mockNotes.slice(0, 3).map((note) => (
            <div className="source-item" key={note.title}>
              <FileText size={16} />
              <div>
                <b>{note.title}</b>
                <small>{note.subject}</small>
              </div>
            </div>
          ))}
        </aside>
      </div>
    </>
  );
}

function Tests() {
  const [started, setStarted] = useState(false);
  const [tab, setTab] = useState("Recommended");
  const [answer, setAnswer] = useState(null);
  const items = [
    "Transport Layer Test",
    "DBMS Foundations",
    "Operating Systems Mock",
  ];
  return (
    <>
      <PageHeader
        eyebrow="KNOWLEDGE CHECKS"
        title="AI tests"
        description="Turn study time into lasting understanding."
        action={<Button icon={ClipboardCheck}>Test history</Button>}
      />
      <div className="tabs test-tabs">
        {["Recommended", "Practice", "Mock Exams", "Completed"].map((item) => (
          <button
            className={tab === item ? "active" : ""}
            onClick={() => setTab(item)}
            key={item}
          >
            {item}
          </button>
        ))}
      </div>
      {started ? (
        <div className="quiz panel">
          <div className="quiz-top">
            <span>QUESTION 1 / 5</span>
            <span>Computer Networks · Medium</span>
          </div>
          <h2>{mockQuiz[0].question}</h2>
          <div className="options">
            {mockQuiz[0].options.map((option, index) => (
              <button
                className={answer === index ? "selected" : ""}
                onClick={() => setAnswer(index)}
                key={option}
              >
                <span>{String.fromCharCode(65 + index)}</span>
                {option}
              </button>
            ))}
          </div>
          <div className="quiz-footer">
            <span className="muted">Answer saved locally</span>
            <Button primary onClick={() => setStarted(false)}>
              Submit test <ChevronRight size={16} />
            </Button>
          </div>
        </div>
      ) : (
        <div className="test-grid">
          {items.map((title, index) => (
            <div className="test-card panel" key={title}>
              <div className="test-icon">
                <Brain size={19} />
              </div>
              <Priority>{index === 0 ? "RECOMMENDED" : "PRACTICE"}</Priority>
              <h2>{title}</h2>
              <p className="muted">
                {index === 0
                  ? "Computer Networks · Transport Layer"
                  : index === 1
                    ? "Database Systems · Normalization"
                    : "Operating Systems · Scheduling"}
              </p>
              <div className="test-meta">
                <span>
                  <ClipboardCheck size={14} /> {index === 0 ? 10 : 15} Questions
                </span>
                <span>
                  <Clock3 size={14} /> 15 min
                </span>
                <span>Medium</span>
              </div>
              <Button primary onClick={() => setStarted(true)}>
                Start test <ArrowUpRight size={15} />
              </Button>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

function Progress({ subjectId }) {
  const { subjects, mastery } = useWorkspace();
  const chartData = mockAnalytics.weekly.map((value, index) => ({
    day: ["M", "T", "W", "T", "F", "S", "S"][index],
    hours: value,
    focus: 68 + index * 3,
  }));
  const subjectData = subjects.map((item) => ({
    name: item.short,
    value: mastery[item.id] || item.mastery,
  }));
  return (
    <>
      <PageHeader
        eyebrow="THE BIGGER PICTURE"
        title={subjectId ? "Subject progress" : "Progress"}
        description="Small sessions, visible momentum, better decisions."
        action={<Button icon={CalendarDays}>Last 7 days</Button>}
      />
      {!subjectId && (
        <div className="stats-grid analytics-stats">
          <Stat
            label="Study time"
            value={mockAnalytics.studyTime}
            trend="↑ 18%"
            icon={Clock3}
          />
          <Stat
            label="Focus score"
            value={mockAnalytics.focusScore}
            trend="↑ 6%"
            icon={Zap}
            accent="orange"
          />
          <Stat
            label="Completion rate"
            value={mockAnalytics.completion}
            trend="↑ 4%"
            icon={CircleCheck}
            accent="blue"
          />
          <Stat
            label="Knowledge growth"
            value={mockAnalytics.growth}
            trend="This month"
            icon={TrendingUp}
            accent="green"
          />
          <Stat
            label="Current streak"
            value={`${mockStudent.streak} days`}
            trend="+1 this week"
            icon={Target}
            accent="green"
          />
        </div>
      )}
      <div className="analytics-grid">
        <section className="panel chart-panel">
          <SectionHead eyebrow="CONSISTENCY" title="Weekly study time" />
          <ResponsiveContainer width="100%" height={230}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="studyFill2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#9733EE" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#9733EE" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#eeeaf5" vertical={false} />
              <XAxis dataKey="day" axisLine={false} tickLine={false} />
              <YAxis axisLine={false} tickLine={false} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="hours"
                stroke="#9733EE"
                strokeWidth={3}
                fill="url(#studyFill2)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </section>
        <section className="panel chart-panel">
          <SectionHead eyebrow="MASTERY MAP" title="Subject mastery" />
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={subjectData} layout="vertical">
              <XAxis type="number" hide />
              <YAxis
                type="category"
                dataKey="name"
                axisLine={false}
                tickLine={false}
              />
              <Tooltip />
              <Bar
                dataKey="value"
                fill="#3E5275"
                radius={[0, 3, 3, 0]}
                barSize={18}
              />
            </BarChart>
          </ResponsiveContainer>
        </section>
      </div>
      {!subjectId && (
        <>
          <div className="analytics-grid extra-charts">
            <section className="panel chart-panel">
              <SectionHead eyebrow="FOCUS TREND" title="When focus sticks" />
              <ResponsiveContainer width="100%" height={190}>
                <LineChart data={chartData}>
                  <CartesianGrid stroke="#eeeaf5" vertical={false} />
                  <XAxis dataKey="day" axisLine={false} tickLine={false} />
                  <YAxis hide />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="focus"
                    stroke="#E7984A"
                    strokeWidth={3}
                  />
                </LineChart>
              </ResponsiveContainer>
            </section>
            <section className="panel heatmap-panel">
              <SectionHead eyebrow="CONSISTENCY" title="Study heatmap" />
              <Heatmap />
            </section>
          </div>
          <section className="panel insights">
            <SectionHead
              eyebrow="WHAT RISE HAS LEARNED ABOUT YOU"
              title="AI insights"
            />
            <div className="insight-grid">
              <div>
                <span className="signal purple">●</span>
                <b>You perform best between 6–8 PM.</b>
                <small>Protect this window for high-risk topics.</small>
              </div>
              <div>
                <span className="signal orange">●</span>
                <b>You frequently postpone Computer Networks.</b>
                <small>
                  RISE has shortened your next block to lower friction.
                </small>
              </div>
              <div>
                <span className="signal green">●</span>
                <b>DBMS mastery increased 14% this week.</b>
                <small>Your retrieval practice is working.</small>
              </div>
              <div>
                <span className="signal red">●</span>
                <b>Computer Networks is your highest academic risk.</b>
                <small>Two revision blocks are now protected.</small>
              </div>
            </div>
          </section>
          <Companion />
        </>
      )}
    </>
  );
}
function Heatmap() {
  return (
    <div className="heatmap">
      {Array.from({ length: 84 }, (_, index) => (
        <span
          className={`heat-${index % 5}`}
          key={index}
          title={`${(index % 4) + 1} study sessions`}
        />
      ))}
    </div>
  );
}
function Companion() {
  return (
    <section className="companion panel">
      <div className="companion-art">✦</div>
      <div>
        <p className="eyebrow">RISE COMPANION</p>
        <h2>Keep the streak alive.</h2>
        <p className="muted">Level 12 · 1,240 XP · 🔥 7 day streak</p>
        <ProgressBar value={68} color="#E7984A" />
      </div>
      <div className="companion-actions">
        <span>
          Next level <b>760 XP</b>
        </span>
        <Button primary icon={Trophy}>
          View rewards
        </Button>
      </div>
    </section>
  );
}

function MockIntegrationsLegacy() {
  const { integrations, setIntegrations } = useWorkspace();
  const [syncing, setSyncing] = useState("");
  const connect = (key) => {
    setIntegrations((value) => ({ ...value, [key]: true }));
  };
  const sync = async (key) => {
    setSyncing(key);
    await classroomService.sync();
    setSyncing("");
  };
  return (
    <>
      <PageHeader
        eyebrow="CONNECTED ACADEMICS"
        title="Integrations"
        description="Bring your academic world into one intelligent workspace."
      />
      <div className="integration-grid">
        <IntegrationCard
          title="Google Classroom"
          description="Import courses, assignments, and materials"
          connected={integrations.classroom}
          onConnect={() => connect("classroom")}
          onSync={() => sync("classroom")}
          syncing={syncing === "classroom"}
          stats={["5 courses", "12 assignments", "34 materials"]}
        />
        <IntegrationCard
          title="Google Calendar"
          description="Sync classes, exams, and events"
          connected={integrations.calendar}
          onConnect={() => connect("calendar")}
          onSync={() => sync("calendar")}
          syncing={syncing === "calendar"}
          stats={["18 events synced"]}
        />
      </div>
    </>
  );
}
function IntegrationCard({
  title,
  description,
  connected,
  onConnect,
  onSync,
  syncing,
  stats,
}) {
  return (
    <div className="integration-card panel">
      <div className="integration-logo">
        {title.includes("Classroom") ? "G" : "31"}
      </div>
      <div className="integration-title">
        <div>
          <h2>{title}</h2>
          <p className="muted">{description}</p>
        </div>
        <span className={connected ? "connected" : "not-connected"}>
          {connected ? "● Connected" : "Not connected"}
        </span>
      </div>
      {connected ? (
        <div className="integration-stats">
          {stats.map((stat) => (
            <b key={stat}>
              {stat}
              <small>Last synced 2 minutes ago</small>
            </b>
          ))}
        </div>
      ) : (
        <div className="empty-inline">
          <Plug size={17} /> Connect to bring your academic world into RISE.
        </div>
      )}
      <div className="button-row">
        {connected ? (
          <Button onClick={onSync} icon={RefreshCw}>
            {syncing ? "Syncing..." : "Sync now"}
          </Button>
        ) : (
          <Button primary onClick={onConnect}>
            Connect {title}
          </Button>
        )}
        <Button>Manage access</Button>
      </div>
    </div>
  );
}
function SettingsPage() {
  const [tab, setTab] = useState("Profile");
  const [saved, setSaved] = useState(false);
  const { user, logout } = useAuth();
  const nameParts = (user?.first_name || mockStudent.name).split(" ");
  const signOut = async () => {
    await logout();
    window.location.assign("/login");
  };
  return (
    <>
      <PageHeader
        eyebrow="YOUR SPACE"
        title="Settings"
        description="Tune RISE to the way you actually study."
      />
      <div className="settings-layout">
        <div className="settings-nav">
          {[
            "Profile",
            "Academic Profile",
            "Subjects",
            "Notifications",
            "Study Preferences",
            "Focus Settings",
            "Integrations",
            "Privacy",
            "Appearance",
          ].map((item) => (
            <button
              className={tab === item ? "active" : ""}
              onClick={() => setTab(item)}
              key={item}
            >
              {item}
              <ChevronRight size={15} />
            </button>
          ))}
        </div>
        <div className="panel settings-form">
          <p className="eyebrow">{tab.toUpperCase()}</p>
          <h2>
            {tab === "Profile" ? "How RISE knows you" : `${tab} preferences`}
          </h2>
          <div className="form-grid">
            <label>
              First name
              <input defaultValue={user?.first_name || nameParts[0]} />
            </label>
            <label>
              Last name
              <input
                defaultValue={user?.last_name || nameParts.slice(1).join(" ")}
              />
            </label>
            <label>
              Email
              <input defaultValue={user?.email || "Not connected"} readOnly />
            </label>
            <label>
              Semester
              <select defaultValue="5">
                <option value="5">Semester 5</option>
                <option value="4">Semester 4</option>
              </select>
            </label>
          </div>
          <label className="toggle-row">
            <span>
              <b>Smart notifications</b>
              <small>Let RISE surface deadlines and plan changes.</small>
            </span>
            <input type="checkbox" defaultChecked />
          </label>
          <div className="button-row">
            <Button
              primary
              onClick={() => {
                setSaved(true);
                setTimeout(() => setSaved(false), 1600);
              }}
            >
              Save changes
            </Button>
            <Button onClick={signOut}>Log out</Button>
          </div>
          {saved && (
            <small className="success">
              <CircleCheck size={14} /> Settings saved
            </small>
          )}
        </div>
      </div>
    </>
  );
}

function Login() {
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState("");
  const googleLogin = async () => {
    setError("");
    setGoogleLoading(true);
    try {
      await firebaseAuthService.login();
      window.location.assign("/onboarding");
    } catch (reason) {
      setError(reason.message);
      setGoogleLoading(false);
    }
  };
  return (
    <div className="auth-page">
      <div className="auth-brand">
        <div className="brand-mark">R</div>
        <strong>RISE</strong>
      </div>
      <div className="auth-card">
        <div className="auth-heading">
          <p className="eyebrow">WELCOME BACK</p>
          <h1>Rise to your best work.</h1>
          <p className="muted">Your academic world, intelligently arranged.</p>
        </div>
        <button
          className="google-button"
          onClick={googleLogin}
          disabled={googleLoading}
        >
          <span>G</span>{" "}
          {googleLoading ? "Connecting..." : "Continue with Google"}
        </button>
        {error && <p className="api-error">{error}</p>}
      </div>
      <p className="auth-tagline">Plan smarter. Focus deeper. Rise higher.</p>
    </div>
  );
}
function MockOnboardingLegacy() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [subjects, setSubjects] = useState([
    "Computer Networks",
    "Database Systems",
    "Operating Systems",
  ]);
  const [newSubject, setNewSubject] = useState("");
  const steps = [
    "Subjects",
    "Syllabus",
    "Notes",
    "Exams",
    "College timetable",
    "Google Classroom",
    "Google Calendar",
  ];
  const next = () => (step < 7 ? setStep(step + 1) : navigate("/"));
  return (
    <div className="onboarding">
      <div className="onboard-top">
        <Link to="/login" className="brand">
          <div className="brand-mark">R</div>
          <strong>RISE</strong>
        </Link>
        <span>
          Step {step} of 7 · {steps[step - 1]}
        </span>
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
          <p>
            {step === 7
              ? "Your workspace is ready for a smarter semester."
              : "Give RISE the information it needs to plan your semester intelligently."}
          </p>
        </div>
        <div className="onboard-card">
          {step === 1 && (
            <>
              <h2>Create your subjects</h2>
              <p className="muted">
                Start with the subjects that matter this semester.
              </p>
              <div className="subject-input">
                <input
                  value={newSubject}
                  onChange={(event) => setNewSubject(event.target.value)}
                  placeholder="Add a subject..."
                />
                <button
                  onClick={() =>
                    newSubject &&
                    (setSubjects([...subjects, newSubject]), setNewSubject(""))
                  }
                >
                  <Plus size={17} />
                </button>
              </div>
              <div className="onboard-subjects">
                {subjects.map((subject, index) => (
                  <div key={subject}>
                    <span
                      className="mini-dot"
                      style={{
                        background: ["#9733EE", "#E7984A", "#3E5275"][
                          index % 3
                        ],
                      }}
                    />
                    {subject}
                    <button
                      onClick={() =>
                        setSubjects(subjects.filter((item) => item !== subject))
                      }
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
              <button className="import-link">
                <Plug size={16} /> Import from Google Classroom{" "}
                <ArrowUpRight size={14} />
              </button>
            </>
          )}
          {step === 2 && (
            <OnboardUpload
              title="Upload your syllabus"
              detail="5 subjects detected · 27 units · 143 topics"
            />
          )}
          {step === 3 && (
            <OnboardUpload
              title="Add your study material"
              detail="PDF, DOCX, PPTX, or images"
            />
          )}
          {step === 4 && (
            <TimetableOnboard
              title="Upload your exam timetable"
              items={[
                "Computer Networks · Aug 25 · 9:00 AM",
                "Database Systems · Aug 28 · 2:00 PM",
                "Operating Systems · Aug 31 · 9:00 AM",
              ]}
            />
          )}
          {step === 5 && (
            <TimetableOnboard
              title="Map your college week"
              items={[
                "MON · 09:00 CN · 11:00 DBMS",
                "TUE · 09:00 Python · 10:00 Mathematics",
                "WED · 11:00 Operating Systems",
              ]}
            />
          )}
          {step === 6 && (
            <ConnectOnboard
              title="Connect Google Classroom"
              detail="Import courses, assignments, and materials."
            />
          )}
          {step === 7 && (
            <>
              <div className="onboard-summary">
                <b>
                  5<small>Subjects</small>
                </b>
                <b>
                  27<small>Topics</small>
                </b>
                <b>
                  4<small>Exams</small>
                </b>
                <b>
                  12<small>Assignments</small>
                </b>
                <b>
                  38<small>Resources</small>
                </b>
              </div>
              <div className="connect-hero">
                <div className="integration-logo">✦</div>
                <h2>Your plan is ready to begin.</h2>
                <p className="muted">
                  RISE has enough context to prioritize, plan, and adapt.
                </p>
              </div>
            </>
          )}
        </div>
        <div className="onboard-actions">
          <button
            className="skip"
            onClick={() => (step < 7 ? setStep(step + 1) : navigate("/"))}
          >
            {step < 7 ? "Skip for now" : "Enter dashboard"}
          </button>
          <Button primary onClick={next}>
            {step === 7 ? "Generate My Plan" : "Continue"}{" "}
            <ChevronRight size={16} />
          </Button>
        </div>
      </main>
    </div>
  );
}
function OnboardUpload({ title, detail }) {
  return (
    <>
      <h2>{title}</h2>
      <p className="muted">
        RISE will turn this into an organized, useful layer of your academic
        world.
      </p>
      <div className="drop-zone">
        <Upload size={24} />
        <b>Drop files here</b>
        <span>{detail}</span>
        <Button>Browse files</Button>
      </div>
    </>
  );
}
function TimetableOnboard({ title, items }) {
  return (
    <>
      <h2>{title}</h2>
      <p className="muted">
        You can edit this information later from Settings.
      </p>
      <div className="exam-list">
        {items.map((item) => (
          <div key={item}>
            <b>{item}</b>
            <MoreHorizontal size={16} />
          </div>
        ))}
      </div>
      <Button icon={Plus}>Add manually</Button>
    </>
  );
}
function ConnectOnboard({ title, detail }) {
  return (
    <>
      <div className="connect-hero">
        <div className="integration-logo">G</div>
        <h2>{title}</h2>
        <p className="muted">{detail}</p>
      </div>
      <div className="connect-option">
        <div>
          <b>Ready to connect</b>
          <small>Mock connection for this prototype</small>
        </div>
        <Button primary>Connect</Button>
      </div>
    </>
  );
}

export default App;
