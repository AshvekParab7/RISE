import { useEffect, useState } from "react";
import { BookOpen, CalendarDays, Zap } from "lucide-react";
import { loadBackendWorkspace } from "../services/backendBridge";
import "./backend-loading.css";

export function BackendGate({ children }) {
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!localStorage.getItem("rise_access_token")) {
      setReady(true);
      return undefined;
    }
    loadBackendWorkspace()
      .catch(() => null)
      .finally(() => setReady(true));
    return undefined;
  }, []);
  if (ready) return children;
  return (
    <main className="backend-loading" role="status" aria-live="polite">
      <section className="backend-loading-panel">
        <div className="backend-loading-brand" aria-hidden="true">
          <div className="backend-loading-mark">R</div>
          <span className="backend-loading-line" />
          <span className="backend-loading-spark backend-loading-spark-one" />
          <span className="backend-loading-spark backend-loading-spark-two" />
        </div>
        <div className="backend-loading-copy">
          <p className="eyebrow">RISE STUDY ENGINE</p>
          <h1>Setting up your study space</h1>
          <p className="backend-loading-message">
            Gathering your subjects, timetable, and next best move.
          </p>
          <div className="backend-loading-signals" aria-hidden="true">
            <span>
              <BookOpen size={14} /> Subjects
            </span>
            <span>
              <CalendarDays size={14} /> Timetable
            </span>
            <span>
              <Zap size={14} /> Focus plan
            </span>
          </div>
        </div>
      </section>
    </main>
  );
}
