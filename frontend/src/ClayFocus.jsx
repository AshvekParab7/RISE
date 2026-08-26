import { useEffect, useState } from "react";
import {
  CheckCircle2,
  Pause,
  Play,
  RefreshCw,
  ShieldCheck,
  X,
} from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { get } from "./services/api";
import { studySessionService } from "./services/studySessionService";

const asArray = (value) => {
  const items = Array.isArray(value) ? value : value?.results;
  return Array.isArray(items) ? items : [];
};
const DEFAULT_PLANNED_MINUTES = 45;
const normalizeMinutes = (value) => {
  const minutes = Number(value);
  return Number.isFinite(minutes) && minutes > 0
    ? Math.min(180, Math.round(minutes))
    : DEFAULT_PLANNED_MINUTES;
};
const sameId = (left, right) => String(left || "") === String(right || "");
const findById = (items, id) => items.find((item) => sameId(item.id, id));

export default function ClayFocus({ active, setActive }) {
  const location = useLocation();
  const navigate = useNavigate();
  const routeAction = location.state?.action || null;
  const initialMinutes = normalizeMinutes(routeAction?.duration_minutes);
  const [plannedMinutes, setPlannedMinutes] = useState(initialMinutes);
  const [seconds, setSeconds] = useState(initialMinutes * 60);
  const [paused, setPaused] = useState(false);
  const [session, setSession] = useState(null);
  const [subjects, setSubjects] = useState([]);
  const [topics, setTopics] = useState([]);
  const [focusPlan, setFocusPlan] = useState(routeAction);
  const [starting, setStarting] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    Promise.allSettled([
      studySessionService.list(),
      get("/subjects/"),
      get("/topics/"),
    ]).then(([sessionsResult, subjectsResult, topicsResult]) => {
      if (!mounted) return;
      const subjectItems =
        subjectsResult.status === "fulfilled"
          ? asArray(subjectsResult.value)
          : [];
      const topicItems =
        topicsResult.status === "fulfilled" ? asArray(topicsResult.value) : [];
      setSubjects(subjectItems);
      setTopics(topicItems);
      if (sessionsResult.status !== "fulfilled") return;
      const current = asArray(sessionsResult.value).find(
        (item) => item.status === "ACTIVE",
      );
      if (!current) return;
      const minutes = normalizeMinutes(current.planned_minutes);
      const startedAt = current.started_at
        ? new Date(current.started_at)
        : null;
      const elapsedSeconds =
        startedAt && !Number.isNaN(startedAt.getTime())
          ? Math.max(0, Math.floor((Date.now() - startedAt.getTime()) / 1000))
          : 0;
      setSession(current);
      setPlannedMinutes(minutes);
      setSeconds(Math.max(0, minutes * 60 - elapsedSeconds));
      setActive(true);
      const subject = findById(subjectItems, current.subject);
      const topic = findById(topicItems, current.topic);
      setFocusPlan((plan) => ({
        ...(plan || {}),
        subject_id: current.subject,
        topic_id: current.topic,
        subject: subject?.name || plan?.subject || "",
        topic: topic?.name || plan?.topic || "",
        duration_minutes: minutes,
      }));
    });
    return () => {
      mounted = false;
    };
  }, [setActive]);

  useEffect(() => {
    if (!routeAction || session) return;
    const minutes = normalizeMinutes(routeAction.duration_minutes);
    setFocusPlan(routeAction);
    setPlannedMinutes(minutes);
    setSeconds(minutes * 60);
    setPaused(false);
  }, [routeAction, session]);

  useEffect(() => {
    if (!active || paused || seconds === 0) return undefined;
    const timer = window.setInterval(
      () => setSeconds((value) => value - 1),
      1000,
    );
    return () => window.clearInterval(timer);
  }, [active, paused, seconds]);

  const start = async () => {
    if (session?.status === "ACTIVE") {
      setActive(true);
      return;
    }
    if (starting) return;
    setStarting(true);
    setError("");
    try {
      const subject =
        findById(subjects, focusPlan?.subject_id) ||
        subjects.find((item) => item.name === focusPlan?.subject) ||
        subjects[0] ||
        (focusPlan?.subject_id
          ? {
              id: focusPlan.subject_id,
              name: focusPlan.subject || "Study session",
            }
          : null);
      if (!subject) throw new Error("Create a subject before starting focus.");
      const subjectTopics = topics.filter((item) =>
        sameId(item.subject?.id || item.subject, subject.id),
      );
      const topic =
        subjectTopics.find((item) => sameId(item.id, focusPlan?.topic_id)) ||
        subjectTopics.find((item) => item.name === focusPlan?.topic) ||
        subjectTopics[0] ||
        (focusPlan?.topic_id
          ? { id: focusPlan.topic_id, name: focusPlan.topic || "" }
          : null);
      const minutes = normalizeMinutes(focusPlan?.duration_minutes);
      const response = await studySessionService.create({
        subject: subject.id,
        topic: topic?.id || null,
        planned_minutes: minutes,
        status: "ACTIVE",
        started_at: new Date().toISOString(),
      });
      setSession(response);
      setFocusPlan({
        ...(focusPlan || {}),
        subject_id: subject.id,
        topic_id: topic?.id || null,
        subject: subject.name,
        topic: topic?.name || "",
        duration_minutes: minutes,
      });
      setPlannedMinutes(minutes);
      setSeconds(minutes * 60);
      setActive(true);
      setPaused(false);
    } catch (reason) {
      setError(reason.message);
    } finally {
      setStarting(false);
    }
  };

  const finish = async (status) => {
    if (finishing) return;
    if (!session) {
      setActive(false);
      return;
    }
    setFinishing(true);
    setError("");
    try {
      const response = await studySessionService.update(session.id, {
        status,
        actual_minutes: Math.min(
          plannedMinutes,
          Math.max(0, Math.floor((plannedMinutes * 60 - seconds) / 60)),
        ),
        ended_at: new Date().toISOString(),
      });
      setSession(response);
      setActive(false);
      setPaused(false);
      if (status === "COMPLETED") navigate("/knowledge-check");
    } catch (reason) {
      setError(reason.message);
    } finally {
      setFinishing(false);
    }
  };

  const mins = String(Math.floor(seconds / 60)).padStart(2, "0");
  const secs = String(seconds % 60).padStart(2, "0");
  const currentSubject = findById(
    subjects,
    session?.subject || focusPlan?.subject_id,
  );
  const currentTopic = findById(topics, session?.topic || focusPlan?.topic_id);
  const subjectName =
    currentSubject?.name || focusPlan?.subject || "Study session";
  const topicName = currentTopic?.name || focusPlan?.topic || "";

  return (
    <div className="clay-focus page-enter">
      <div className="clay-focus-heading">
        <p className="eyebrow">
          <ShieldCheck size={15} /> DEEP FOCUS SESSION
        </p>
        <h1>{topicName || subjectName}</h1>
        <span className={active ? "focus-live" : "focus-ready"}>
          {active
            ? paused
              ? "Session paused"
              : "Session active"
            : "Ready when you are"}
        </span>
      </div>
      {error && <p className="api-error">{error}</p>}
      <section className="clay-focus-timer">
        <div className="clay-timer-ring">
          <div>
            <strong>
              {mins}:{secs}
            </strong>
            <span>Remaining</span>
          </div>
        </div>
        <div className="clay-focus-controls">
          {!active ? (
            <button
              className="clay-action primary"
              onClick={start}
              disabled={starting}
            >
              <Play size={16} /> Start session
            </button>
          ) : (
            <>
              <button
                className="clay-action"
                onClick={() => setPaused((value) => !value)}
              >
                {paused ? <Play size={16} /> : <Pause size={16} />}
                {paused ? "Resume" : "Pause"}
              </button>
              <button
                className="clay-action primary"
                onClick={() => finish("COMPLETED")}
                disabled={finishing}
              >
                <CheckCircle2 size={16} /> Finish session
              </button>
            </>
          )}
          <button
            className="clay-action clay-quit"
            onClick={() => finish("ABANDONED")}
            disabled={finishing}
          >
            <X size={15} /> Quit session
          </button>
          <button
            className="clay-round-button"
            onClick={() => {
              setSeconds(plannedMinutes * 60);
              setPaused(false);
            }}
            aria-label="Reset timer"
          >
            <RefreshCw size={16} />
          </button>
        </div>
      </section>
      <div className="clay-focus-status">
        <div>
          <span className="status-mark">
            <ShieldCheck size={18} />
          </span>
          <div>
            <strong>Protected space</strong>
            <small>RISE is keeping this block clear.</small>
          </div>
        </div>
        <div className="focus-topic">
          <span>{subjectName.toUpperCase()}</span>
          <b>{topicName || "Focused study"}</b>
          <small>{plannedMinutes} minute deep work block</small>
        </div>
      </div>
    </div>
  );
}
