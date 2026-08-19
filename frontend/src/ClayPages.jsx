import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowUpRight,
  Bell,
  ChevronRight,
  CircleCheck,
  LayoutDashboard,
  LogOut,
  Play,
  Sparkles,
  Target,
  Timer,
  UserRound,
  Zap,
} from "lucide-react";
import {
  mockAnalytics,
  mockMaterials,
  mockStudent,
  mockSubjects,
  mockTasks,
} from "./data/mockData";
import { useAuth } from "./context/auth";
import { useWorkspace } from "./context/WorkspaceContext";

const localSubjects = (items) => (items.length ? items : mockSubjects);
const localTasks = (items) => (items.length ? items : mockTasks);
const firstNameFor = (user) =>
  user?.first_name || mockStudent.name.split(" ")[0];

function ClayButton({
  children,
  primary = false,
  icon: Icon,
  onClick,
  type = "button",
}) {
  return (
    <button
      type={type}
      className={`clay-action ${primary ? "primary" : ""}`}
      onClick={onClick}
    >
      {Icon && <Icon size={16} />}
      {children}
    </button>
  );
}

function ClayIcon({ children }) {
  return <span className="clay-icon">{children}</span>;
}

function SectionTitle({ eyebrow, title, link }) {
  return (
    <div className="clay-section-title">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      {link && (
        <Link to={link} className="clay-inline-link">
          View all <ArrowUpRight size={14} />
        </Link>
      )}
    </div>
  );
}

function ClayDashboard({ setFocus }) {
  const { user } = useAuth();
  const { subjects, tasks, setTasks } = useWorkspace();
  const availableSubjects = localSubjects(subjects);
  const availableTasks = localTasks(tasks);
  const firstName = firstNameFor(user);
  const completeTask = (id) =>
    setTasks((items) =>
      items.map((task) =>
        task.id === id ? { ...task, status: "completed" } : task,
      ),
    );
  const openTasks = availableTasks.filter(
    (task) => task.status !== "completed",
  );
  const velocity = [42, 60, 48, 76, 94];

  return (
    <div className="clay-dashboard page-enter">
      <header className="clay-dashboard-header">
        <div>
          <p className="eyebrow">ACADEMIC INTELLIGENCE</p>
          <h1>Good morning, {firstName}</h1>
          <p className="muted lead">
            Ready to dive into Advanced Calculus today?
          </p>
        </div>
        <ClayButton primary icon={Play} onClick={setFocus}>
          Start focus session
        </ClayButton>
      </header>

      <div className="clay-dashboard-desktop">
        <div className="clay-dashboard-grid">
          <section className="clay-card clay-schedule-card">
            <SectionTitle
              eyebrow="TODAY, AUG 19"
              title="Adaptive timetable"
              link="/planner"
            />
            <div className="clay-schedule-list">
              <div className="clay-schedule-row muted-row">
                <time>08:00</time>
                <span>Literature Review</span>
                <CircleCheck size={17} />
              </div>
              <div className="clay-schedule-row active-row">
                <time>10:00</time>
                <div>
                  <strong>Advanced Calculus</strong>
                  <small>Deep Work Session · 90 min</small>
                </div>
                <button
                  className="clay-round-button"
                  onClick={setFocus}
                  aria-label="Start Advanced Calculus focus"
                >
                  <Play size={15} />
                </button>
              </div>
              <div className="clay-schedule-row">
                <time>13:00</time>
                <span>Physics Lab Prep</span>
              </div>
            </div>
          </section>

          <section className="clay-card clay-velocity-card">
            <SectionTitle eyebrow="THIS WEEK" title="Focus velocity" />
            <p className="muted">Your concentration trend</p>
            <div className="clay-bars" aria-label="Focus velocity chart">
              {velocity.map((height, index) => (
                <span
                  key={height}
                  className={index === velocity.length - 1 ? "peak" : ""}
                  style={{ height: `${height}%` }}
                >
                  <i>{index === velocity.length - 1 ? "95%" : ""}</i>
                </span>
              ))}
            </div>
            <div className="clay-bar-labels">
              <span>M</span>
              <span>T</span>
              <span>W</span>
              <span>T</span>
              <b>F</b>
            </div>
          </section>

          <section className="clay-card clay-companion-card">
            <div className="clay-companion-image">
              <img
                src="/assets/stitch/dashboard-companion.png"
                alt="RISE companion owl"
              />
            </div>
            <div>
              <p className="eyebrow">RISE COMPANION</p>
              <h3>Archimedes says</h3>
              <p className="muted italic">
                "Your focus is peaking. Tackle the tough integral set next."
              </p>
            </div>
          </section>

          <section className="clay-card clay-stat-card">
            <ClayIcon>
              <Zap size={22} />
            </ClayIcon>
            <strong>12</strong>
            <span>DAY STREAK</span>
          </section>
          <section className="clay-card clay-stat-card">
            <ClayIcon>
              <Timer size={22} />
            </ClayIcon>
            <strong>14h</strong>
            <span>FOCUS THIS WEEK</span>
          </section>
        </div>
      </div>

      <div className="clay-dashboard-mobile">
        <section className="clay-card mobile-velocity-card">
          <SectionTitle eyebrow="FOCUS VELOCITY" title="84%" />
          <p className="muted">+12% from last week. Keep it up!</p>
          <div className="clay-progress">
            <span style={{ width: "84%" }} />
          </div>
        </section>
        <div className="mobile-dashboard-pair">
          <Link to="/tutor" className="clay-card mobile-quick-card">
            <ClayIcon>
              <UserRound size={19} />
            </ClayIcon>
            <strong>Study Coach</strong>
            <span>2 insights</span>
          </Link>
          <Link to="/subjects" className="clay-card mobile-quick-card">
            <ClayIcon>
              <LayoutDashboard size={19} />
            </ClayIcon>
            <strong>Physics 101</strong>
            <span>in 30 mins</span>
          </Link>
        </div>
        <section className="clay-card mobile-goal-card">
          <div>
            <strong>Daily Goal</strong>
            <span>3 / 4 hours completed</span>
          </div>
          <div className="clay-goal-ring">75%</div>
        </section>
      </div>

      <div className="clay-dashboard-lower">
        <section className="clay-card clay-deadlines-card">
          <SectionTitle
            eyebrow="ACADEMIC INBOX"
            title="Upcoming deadlines"
            link="/tasks"
          />
          {openTasks.slice(0, 3).map((task) => (
            <div className="clay-deadline-row" key={task.id}>
              <button
                className={`clay-check ${task.status === "completed" ? "checked" : ""}`}
                onClick={() => completeTask(task.id)}
                aria-label={`Complete ${task.title}`}
              >
                {task.status === "completed" && <CircleCheck size={16} />}
              </button>
              <div>
                <strong>{task.title}</strong>
                <span>
                  {task.subject} · {task.source}
                </span>
              </div>
              <small>{task.due}</small>
            </div>
          ))}
        </section>
        <section className="clay-card clay-subject-pulse-card">
          <SectionTitle
            eyebrow="MASTERY MAP"
            title="Subject pulse"
            link="/progress"
          />
          {availableSubjects.slice(0, 4).map((subject) => (
            <Link
              to={`/subjects/${subject.id}`}
              className="clay-subject-row"
              key={subject.id}
            >
              <span
                className="subject-badge"
                style={{ background: subject.color }}
              >
                {subject.short}
              </span>
              <strong>{subject.name}</strong>
              <span className="clay-mini-progress">
                <i
                  style={{
                    width: `${subject.mastery}%`,
                    background: subject.color,
                  }}
                />
              </span>
              <b>{subject.mastery}%</b>
              <ChevronRight size={14} />
            </Link>
          ))}
        </section>
      </div>

      <section className="clay-card clay-materials-card">
        <SectionTitle
          eyebrow="JUST IN"
          title="New from Google Classroom"
          link="/notes"
        />
        <div className="clay-material-grid">
          {mockMaterials.map((material) => (
            <Link
              to="/notes"
              className="clay-material-row"
              key={material.title}
            >
              <span className="file-token">PDF</span>
              <div>
                <strong>{material.title}</strong>
                <small>
                  {material.subject} · {material.time}
                </small>
              </div>
              <ArrowUpRight size={15} />
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

function ClayAnalytics({ subjectId }) {
  const { subjects, mastery } = useWorkspace();
  const availableSubjects = localSubjects(subjects);
  const selectedSubject = subjectId
    ? availableSubjects.find((subject) => subject.id === subjectId) ||
      availableSubjects[0]
    : null;
  const topSubject = [...availableSubjects].sort(
    (left, right) =>
      (mastery[right.id] || right.mastery) - (mastery[left.id] || left.mastery),
  )[0];
  const [range, setRange] = useState("Week");
  const bars = [28, 42, 35, 65, 57, 82, 46];
  const blocks = [
    "8AM",
    "9AM",
    "10AM",
    "11AM",
    "12PM",
    "1PM",
    "2PM",
    "3PM",
    "4PM",
  ];

  return (
    <div className="clay-analytics page-enter">
      <header className="clay-page-heading">
        <div>
          <p className="eyebrow">
            {selectedSubject ? "SUBJECT INSIGHTS" : "COGNITIVE PERFORMANCE"}
          </p>
          <h1>{selectedSubject ? selectedSubject.name : "Focus insights"}</h1>
          <p className="muted lead">
            Your cognitive performance mapping for this week.
          </p>
        </div>
        <div className="clay-segmented">
          {["Day", "Week", "Month"].map((item) => (
            <button
              key={item}
              className={range === item ? "active" : ""}
              onClick={() => setRange(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </header>
      <div className="clay-analytics-grid">
        <section className="clay-card clay-insight-stat">
          <div className="clay-stat-heading">
            <ClayIcon>
              <Zap size={18} />
            </ClayIcon>
            <h2>Focus velocity</h2>
          </div>
          <div className="clay-big-number">
            {selectedSubject
              ? `${mastery[selectedSubject.id] || selectedSubject.mastery}`
              : "85"}
            <small>Score</small>
          </div>
          <p className="muted">Optimal flow state maintained.</p>
          <div className="clay-progress">
            <span
              style={{
                width: selectedSubject
                  ? `${mastery[selectedSubject.id] || selectedSubject.mastery}%`
                  : "85%",
              }}
            />
          </div>
        </section>
        <section className="clay-card clay-insight-stat">
          <div className="clay-stat-heading">
            <ClayIcon>
              <Target size={18} />
            </ClayIcon>
            <h2>Study streak</h2>
          </div>
          <div className="clay-big-number">
            14<small>Days</small>
          </div>
          <p className="clay-trend">+3 from last week</p>
        </section>
        <section className="clay-card clay-insight-stat">
          <div className="clay-stat-heading">
            <ClayIcon>
              <Sparkles size={18} />
            </ClayIcon>
            <h2>Top mastery</h2>
          </div>
          <div className="clay-mastery-name">
            {topSubject?.name || "Biology"}
          </div>
          <p className="muted">
            {topSubject?.next || "Cellular Respiration"} module completed.
          </p>
        </section>
        <section className="clay-card clay-distribution-card">
          <SectionTitle eyebrow="DEEP WORK DISTRIBUTION" title="" />
          <div className="clay-distribution-chart">
            {bars.map((height, index) => (
              <div key={index} className={index === 2 ? "peak" : ""}>
                <span style={{ height: `${height}%` }} />
                <small>
                  {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][index]}
                </small>
              </div>
            ))}
          </div>
        </section>
        <section className="clay-card clay-blocks-card">
          <SectionTitle eyebrow="OPTIMAL BLOCKS" title="" />
          <div className="clay-block-grid">
            {blocks.map((block, index) => (
              <button
                key={block}
                className={
                  index > 5 ? "accent" : index % 3 === 2 ? "active" : ""
                }
              >
                {block}
              </button>
            ))}
          </div>
        </section>
      </div>
      <section className="clay-card clay-analytics-footer">
        <SectionTitle eyebrow="WEEKLY RHYTHM" title="Study time" />
        <div className="clay-weekly-bars">
          {mockAnalytics.weekly.map((hours, index) => (
            <div key={index}>
              <span style={{ height: `${(hours / 5.2) * 100}%` }} />
              <small>{["M", "T", "W", "T", "F", "S", "S"][index]}</small>
            </div>
          ))}
        </div>
        <div className="clay-footer-insight">
          <Bell size={17} />
          <span>
            <strong>{range} view</strong> keeps your study rhythm visible
            without breaking your flow.
          </span>
        </div>
      </section>
    </div>
  );
}

function ClaySettings() {
  const { user, logout } = useAuth();
  const nameParts = (user?.first_name || mockStudent.name).split(" ");
  const [saved, setSaved] = useState(false);
  const [focusDuration, setFocusDuration] = useState(45);
  const [verbosity, setVerbosity] = useState("Balanced");
  const [avatar, setAvatar] = useState(
    "/assets/stitch/settings-profile-avatar.png",
  );
  const [notifications, setNotifications] = useState({
    reminders: true,
    analytics: true,
    goals: false,
  });
  const save = () => {
    setSaved(true);
    window.setTimeout(() => setSaved(false), 1800);
  };
  const signOut = async () => {
    await logout();
    window.location.assign("/login");
  };
  const toggle = (key) =>
    setNotifications((value) => ({ ...value, [key]: !value[key] }));

  return (
    <div className="clay-settings page-enter">
      <header className="clay-page-heading settings-heading">
        <div>
          <p className="eyebrow">YOUR SPACE</p>
          <h1>Settings</h1>
          <p className="muted lead">
            Manage your academic profile and preferences.
          </p>
        </div>
        <div className="settings-heading-actions">
          <button className="clay-round-button" aria-label="Notifications">
            <Bell size={17} />
          </button>
          <button className="clay-round-button" aria-label="Account">
            <UserRound size={17} />
          </button>
        </div>
      </header>
      <div className="clay-settings-grid">
        <section className="clay-card clay-profile-card">
          <h2>Profile</h2>
          <div className="clay-profile-avatar">
            <img src={avatar} alt="Profile" />
            <label className="clay-action">
              Change avatar
              <input
                hidden
                type="file"
                accept="image/*"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) setAvatar(URL.createObjectURL(file));
                }}
              />
            </label>
          </div>
          <small className="muted">JPG, GIF or PNG. Max 2MB.</small>
          <label>
            Full Name
            <input
              defaultValue={[
                user?.first_name || nameParts[0],
                user?.last_name || nameParts.slice(1).join(" "),
              ]
                .filter(Boolean)
                .join(" ")}
            />
          </label>
          <label>
            Academic Email
            <input
              defaultValue={user?.email || "jane.doe@university.edu"}
              readOnly
            />
          </label>
        </section>
        <div className="clay-settings-side">
          <section className="clay-card clay-preferences-card">
            <h2>Study preferences</h2>
            <div className="preference-heading">
              <span>Focus Duration (Minutes)</span>
              <b>{focusDuration}</b>
            </div>
            <input
              className="clay-range"
              type="range"
              min="15"
              max="90"
              step="15"
              value={focusDuration}
              onChange={(event) => setFocusDuration(Number(event.target.value))}
            />
            <div className="clay-divider" />
            <span className="preference-label">AI Coach Verbosity</span>
            <div className="clay-segmented full">
              {["Concise", "Balanced", "Detailed"].map((item) => (
                <button
                  key={item}
                  className={verbosity === item ? "active" : ""}
                  onClick={() => setVerbosity(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          </section>
          <section className="clay-card clay-notifications-card">
            <h2>Notifications</h2>
            {[
              {
                key: "reminders",
                title: "Session Reminders",
                detail: "Get notified 15 minutes before a study block.",
              },
              {
                key: "analytics",
                title: "Weekly Analytics",
                detail: "Receive a summary of your study performance.",
              },
              {
                key: "goals",
                title: "Goal Alerts",
                detail: "Notifications when you reach a milestone.",
              },
            ].map((item) => (
              <div className="clay-toggle-row" key={item.key}>
                <span>
                  <strong>{item.title}</strong>
                  <small>{item.detail}</small>
                </span>
                <button
                  className={`clay-switch ${notifications[item.key] ? "on" : ""}`}
                  role="switch"
                  aria-checked={notifications[item.key]}
                  onClick={() => toggle(item.key)}
                >
                  <i />
                </button>
              </div>
            ))}
          </section>
        </div>
      </div>
      <div className="clay-settings-actions">
        <ClayButton onClick={signOut} icon={LogOut}>
          Log out
        </ClayButton>
        <ClayButton primary onClick={save} icon={CircleCheck}>
          Save changes
        </ClayButton>
        {saved && (
          <span className="clay-saved">
            <CircleCheck size={15} /> Settings saved
          </span>
        )}
      </div>
    </div>
  );
}

export { ClayDashboard, ClayAnalytics, ClaySettings };
