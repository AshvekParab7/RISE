import { useEffect, useState } from "react";
import {
  CheckCircle2,
  Pause,
  Play,
  RefreshCw,
  ShieldCheck,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { get } from "./services/api";
import { studySessionService } from "./services/studySessionService";

const asArray = (value) =>
  Array.isArray(value) ? value : value?.results || [];

export default function ClayFocus({ active, setActive }) {
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
    const timer = window.setInterval(
      () => setSeconds((value) => value - 1),
      1000,
    );
    return () => window.clearInterval(timer);
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
    if (!session) {
      setActive(false);
      return;
    }
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
    <div className="clay-focus page-enter">
      <div className="clay-focus-heading">
        <p className="eyebrow">
          <ShieldCheck size={15} /> DEEP FOCUS SESSION
        </p>
        <h1>Transport Layer</h1>
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
            <button className="clay-action primary" onClick={start}>
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
              >
                <CheckCircle2 size={16} /> Finish session
              </button>
            </>
          )}
          <button
            className="clay-action clay-quit"
            onClick={() => finish("ABANDONED")}
          >
            <X size={15} /> Quit session
          </button>
          <button
            className="clay-round-button"
            onClick={() => {
              setSeconds(45 * 60);
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
          <span>COMPUTER NETWORKS</span>
          <b>Transport Layer</b>
          <small>45 minute deep work block</small>
        </div>
      </div>
    </div>
  );
}
