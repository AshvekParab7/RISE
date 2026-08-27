import { useEffect, useState } from "react";
import {
  BookOpen,
  CheckCircle2,
  ChevronDown,
  Clock3,
  LockKeyhole,
  Pause,
  Play,
  Send,
  ShieldCheck,
  Upload,
  X,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { resourceService } from "../services/resourceService";
import { subjectService } from "../services/subjectService";
import { topicService } from "../services/topicService";
import { exitFocusFullscreen, requestFocusFullscreen } from "../services/focusFullscreen";
import { focusSessionService } from "./focusSessionService";
import "./focus.css";

const asArray = (value) =>
  Array.isArray(value) ? value : value?.results || [];

const LOCAL_TEST_SUBJECT_ID = "local-test-subject";
const LOCAL_TEST_TOPIC_ID = "local-test-topic";
const LOCAL_TEST_SESSION_ID = "local-test-session";
const LOCAL_TEST_SESSION_STORAGE_KEY = "rise_local_focus_session";
const localTestSubject = { id: LOCAL_TEST_SUBJECT_ID, name: "Computer Networks", code: "CN" };
const localTestTopic = { id: LOCAL_TEST_TOPIC_ID, subject: LOCAL_TEST_SUBJECT_ID, name: "Unit 2 PDF study" };
const localTestResource = {
  id: "local-test-pdf",
  subject: LOCAL_TEST_SUBJECT_ID,
  title: "Unit 2 Question Answers.pdf",
  resource_type: "DOCUMENT",
  processing_status: "READY",
};

const readLocalTestSession = () => {
  try {
    const stored = JSON.parse(localStorage.getItem(LOCAL_TEST_SESSION_STORAGE_KEY) || "null");
    if (!stored || stored.remaining_seconds <= 0) {
      localStorage.removeItem(LOCAL_TEST_SESSION_STORAGE_KEY);
      return null;
    }
    if (stored.focus_state !== "ACTIVE") return stored;
    const elapsed = Math.floor((Date.now() - stored.last_synced_at) / 1000);
    const remaining = Math.max(0, stored.remaining_seconds - elapsed);
    if (remaining === 0) {
      localStorage.removeItem(LOCAL_TEST_SESSION_STORAGE_KEY);
      return null;
    }
    return { ...stored, remaining_seconds: remaining, last_synced_at: Date.now() };
  } catch {
    localStorage.removeItem(LOCAL_TEST_SESSION_STORAGE_KEY);
    return null;
  }
};

const persistLocalTestSession = (value) => {
  localStorage.setItem(LOCAL_TEST_SESSION_STORAGE_KEY, JSON.stringify({ ...value, last_synced_at: Date.now() }));
};

export default function ClayFocus({ active, setActive, fullscreenActive = true, startRequested = false, clearStartRequest = () => {} }) {
  const [seconds, setSeconds] = useState(45 * 60);
  const [session, setSession] = useState(null);
  const [studyGuide, setStudyGuide] = useState(null);
  const [studyGuideLoading, setStudyGuideLoading] = useState(false);
  const [subjects, setSubjects] = useState([]);
  const [topics, setTopics] = useState([]);
  const [resources, setResources] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [selectedTopicId, setSelectedTopicId] = useState("");
  const [selectedResourceIds, setSelectedResourceIds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [smartBreakOpen, setSmartBreakOpen] = useState(false);
  const [smartBreakQuestion, setSmartBreakQuestion] = useState(null);
  const [smartBreakAnswer, setSmartBreakAnswer] = useState("");
  const [smartBreakResult, setSmartBreakResult] = useState(null);
  const [smartBreakLoading, setSmartBreakLoading] = useState(false);
  const [quitQuizOpen, setQuitQuizOpen] = useState(false);
  const [quitQuizQuestion, setQuitQuizQuestion] = useState(null);
  const [quitQuizAnswer, setQuitQuizAnswer] = useState("");
  const [quitQuizResult, setQuitQuizResult] = useState(null);
  const [quitQuizLoading, setQuitQuizLoading] = useState(false);
  const [breakSeconds, setBreakSeconds] = useState(0);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const localTestMode = import.meta.env.DEV && !localStorage.getItem("rise_access_token");

  useEffect(() => {
    let mounted = true;
    Promise.allSettled([
      focusSessionService.current(),
      subjectService.list(),
      topicService.list(),
      resourceService.list(),
    ])
      .then(([currentResult, subjectsResult, topicsResult, resourcesResult]) => {
        if (!mounted) return;
        const current = currentResult.status === "fulfilled" ? currentResult.value : null;
        const apiSubjects = subjectsResult.status === "fulfilled" ? asArray(subjectsResult.value) : [];
        const apiTopics = topicsResult.status === "fulfilled" ? asArray(topicsResult.value) : [];
        const apiResources = resourcesResult.status === "fulfilled" ? asArray(resourcesResult.value) : [];
        const useLocalTestData = localTestMode && apiSubjects.length === 0;
        const loadedSubjects = useLocalTestData ? [localTestSubject] : apiSubjects;
        const loadedTopics = useLocalTestData ? [localTestTopic] : apiTopics;
        const loadedResources = useLocalTestData ? [localTestResource] : apiResources;
        setSubjects(loadedSubjects);
        setTopics(loadedTopics);
        setResources(loadedResources);
        const storedLocalSession = useLocalTestData ? readLocalTestSession() : null;
        if (storedLocalSession) {
          setSession(storedLocalSession);
          setSeconds(storedLocalSession.remaining_seconds);
          setActive(true);
          return;
        }
        if (current) {
          setSession(current);
          setSeconds(current.remaining_seconds ?? 45 * 60);
          setActive(true);
          return;
        }
        const initialSubjectId = loadedSubjects[0]?.id || "";
        const initialReadyResource = loadedResources.find(
          (resource) => resource.subject === initialSubjectId && resource.processing_status === "READY",
        );
        setSelectedSubjectId(initialSubjectId);
        setSelectedResourceIds(initialReadyResource ? [initialReadyResource.id] : []);
        const failedResult = [subjectsResult, topicsResult, resourcesResult].find((result) => result.status === "rejected");
        if (failedResult && !useLocalTestData) setError(failedResult.reason.message);
      })
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, [localTestMode, setActive]);

  useEffect(() => {
    if (!active || !session?.id) return undefined;
    let mounted = true;
    if (localTestMode && session.id === LOCAL_TEST_SESSION_ID) {
      setStudyGuide({
        title: "Unit 2 PDF study guide",
        summary: "Work through the uploaded Test_pdf notes by explaining each answer, then check your recall without looking back.",
        steps: [
          { title: "Preview the questions", detail: "Scan the PDF and group questions by the concept or unit they test.", minutes: 8 },
          { title: "Explain each answer", detail: "For every selected question, explain why the answer is correct in your own words.", minutes: 17 },
          { title: "Retrieve without notes", detail: "Close the PDF and reconstruct the key answers from memory.", minutes: 10 },
          { title: "Check the gaps", detail: "Reopen the PDF, correct missed details, and mark two questions to revisit.", minutes: 10 },
        ],
        key_takeaways: ["Logistic Regression predicts binary outcomes by using the sigmoid function to convert a linear output into a probability between 0 and 1."],
        practice_questions: ["Which answer was hardest to recall, and what clue in the PDF supports it?"],
        source_titles: ["Unit 2 Question Answers.pdf"],
        generated_with: "Local Test_pdf",
      });
      setStudyGuideLoading(false);
      return () => {
        mounted = false;
      };
    }
    setError("");
    setStudyGuide(null);
    setStudyGuideLoading(true);
    focusSessionService.studyGuide(session.id)
      .then((guide) => mounted && setStudyGuide(guide))
      .catch((reason) => mounted && setError(reason.message))
      .finally(() => mounted && setStudyGuideLoading(false));
    return () => {
      mounted = false;
    };
  }, [active, localTestMode, session?.id]);

  useEffect(() => {
    if (!active || !fullscreenActive || session?.focus_state !== "ACTIVE" || seconds === 0) return undefined;
    const timer = window.setInterval(
      () => setSeconds((value) => value - 1),
      1000,
    );
    return () => window.clearInterval(timer);
  }, [active, fullscreenActive, session?.focus_state, seconds]);

  useEffect(() => {
    if (!localTestMode || !session?.local_test) return;
    persistLocalTestSession({ ...session, remaining_seconds: seconds });
  }, [localTestMode, seconds, session]);

  useEffect(() => {
    if (!active || !session || session.focus_state !== "ACTIVE") return undefined;
    const sync = window.setInterval(async () => {
      try {
        const response = await focusSessionService.state(session.id, "sync");
        setSession(response);
        setSeconds(response.remaining_seconds ?? 0);
      } catch {
        // Keep the local display running until the next sync succeeds.
      }
    }, 15000);
    return () => window.clearInterval(sync);
  }, [active, session]);

  const paused = session?.focus_state === "PAUSED_BREAK";
  const breakExpiresAt = session?.break_unlock_expires_at;
  const smartBreakAuthorized = paused && Boolean(breakExpiresAt);

  useEffect(() => {
    if (!smartBreakAuthorized || !breakExpiresAt || !session) {
      setBreakSeconds(0);
      return undefined;
    }
    const syncBreak = async () => {
      const remaining = Math.max(0, Math.ceil((Date.parse(breakExpiresAt) - Date.now()) / 1000));
      setBreakSeconds(remaining);
      if (remaining === 0) {
        try {
          const response = await focusSessionService.state(session.id, "sync");
          setSession(response);
          setSeconds(response.remaining_seconds ?? 0);
          setSmartBreakOpen(false);
        } catch (reason) {
          setError(reason.message);
        }
      }
    };
    syncBreak();
    const timer = window.setInterval(syncBreak, 1000);
    return () => window.clearInterval(timer);
  }, [breakExpiresAt, session, smartBreakAuthorized]);

  const availableTopics = topics.filter(
    (topic) => topic.subject === selectedSubjectId,
  );
  const availableResources = resources.filter(
    (resource) => resource.subject === selectedSubjectId,
  );

  const beginSession = async (subjectId, topicId, resourceIds) => {
    setError("");
    setStudyGuide(null);
    setStarting(true);
    if (localTestMode && subjectId === LOCAL_TEST_SUBJECT_ID) {
      setSession({
        id: LOCAL_TEST_SESSION_ID,
        local_test: true,
        subject_name: localTestSubject.name,
        topic_name: selectedTopic?.name || localTestTopic.name,
        remaining_seconds: 45 * 60,
        focus_state: "ACTIVE",
        status: "ACTIVE",
        selected_resources: resourceIds,
      });
      persistLocalTestSession({
        id: LOCAL_TEST_SESSION_ID,
        local_test: true,
        subject_name: localTestSubject.name,
        topic_name: selectedTopic?.name || localTestTopic.name,
        remaining_seconds: 45 * 60,
        focus_state: "ACTIVE",
        status: "ACTIVE",
        selected_resources: resourceIds,
      });
      setSeconds(45 * 60);
      setActive(true);
      setStarting(false);
      return;
    }
    try {
      const response = await focusSessionService.start({
        subject: subjectId,
        topic: topicId || null,
        selected_resource_ids: resourceIds,
      });
      setSession(response);
      setSeconds(response.remaining_seconds ?? 45 * 60);
      setActive(true);
    } catch (reason) {
      setError(reason.message);
    } finally {
      setStarting(false);
    }
  };

  useEffect(() => {
    if (!startRequested || loading || active || session || starting) return undefined;
    const subjectId = selectedSubjectId || subjects[0]?.id;
    const firstReadyResource = resources.find(
      (resource) => resource.subject === subjectId && resource.processing_status === "READY",
    );
    clearStartRequest();
    if (!subjectId || !firstReadyResource) {
      exitFocusFullscreen();
      setError("Sign in and add at least one ready note before starting a focus session.");
      return undefined;
    }
    setSelectedSubjectId(subjectId);
    setSelectedResourceIds([firstReadyResource.id]);
    beginSession(subjectId, null, [firstReadyResource.id]);
    return undefined;
  }, [active, clearStartRequest, loading, resources, selectedSubjectId, session, startRequested, starting, subjects]);

  const uploadResource = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const uploadSubjectId = selectedSubjectId || subjects[0]?.id;
    if (!uploadSubjectId) {
      setError("Sign in and choose a subject before uploading a resource.");
      return;
    }
    if (!selectedSubjectId) setSelectedSubjectId(uploadSubjectId);
    setUploading(true);
    setUploadStatus("");
    setError("");
    if (localTestMode && uploadSubjectId === LOCAL_TEST_SUBJECT_ID) {
      const localUpload = {
        id: `local-upload-${Date.now()}`,
        subject: LOCAL_TEST_SUBJECT_ID,
        title: file.name,
        resource_type: "DOCUMENT",
        processing_status: "READY",
      };
      setResources((current) => [...current, localUpload]);
      setSelectedResourceIds((current) => [...current, localUpload.id]);
      setUploadStatus(`${file.name} is ready and selected for the local test session.`);
      setUploading(false);
      return;
    }
    try {
      const form = new FormData();
      form.append("subject", uploadSubjectId);
      form.append("title", file.name);
      form.append("file", file);
      form.append("resource_type", "DOCUMENT");
      const uploaded = await resourceService.upload(form);
      setResources((current) => [...current, uploaded]);
      if (uploaded.processing_status === "READY") {
        setSelectedResourceIds((current) => [...current, uploaded.id]);
        setUploadStatus(`${file.name} is ready and selected for this session.`);
      } else if (uploaded.processing_status === "FAILED") {
        setError(uploaded.processing_error || `${file.name} could not be processed.`);
        setUploadStatus(`${file.name} was uploaded but could not be read.`);
      } else {
        setUploadStatus(`${file.name} uploaded. It will be selectable when ready.`);
      }
    } catch (reason) {
      exitFocusFullscreen();
      setError(reason.message);
    } finally {
      setUploading(false);
    }
  };

  const updateState = async (action, endReason) => {
    if (!session) return;
    if (session.local_test) {
      if (action === "quit") {
        setActive(false);
        setSession(null);
        setSeconds(45 * 60);
        setStudyGuide(null);
        localStorage.removeItem(LOCAL_TEST_SESSION_STORAGE_KEY);
        exitFocusFullscreen();
      } else {
        setSession((current) => ({ ...current, focus_state: action === "pause" ? "PAUSED_BREAK" : "ACTIVE" }));
      }
      return;
    }
    try {
      const response = await focusSessionService.state(
        session.id,
        action,
        endReason,
      );
      setSession(response);
      setSeconds(response.remaining_seconds ?? 0);
      if (action === "quit") {
        setActive(false);
        setSession(null);
        setSeconds(45 * 60);
        setStudyGuide(null);
        exitFocusFullscreen();
      }
    } catch (reason) {
      setError(reason.message);
    }
  };

  const requestSmartBreak = async () => {
    if (!session) return;
    setError("");
    setSmartBreakOpen(true);
    setSmartBreakLoading(true);
    setSmartBreakResult(null);
    setSmartBreakAnswer("");
    if (session.local_test) {
      setSmartBreakQuestion({
        question: "Which idea from the selected notes should you explain without looking back?",
        options: [
          "The sigmoid function predicts binary outcomes",
          "File compression reduces every file to zero bytes",
          "Authentication removes the need for passwords",
          "A database index replaces all queries",
        ],
        correct_answer: "The sigmoid function predicts binary outcomes",
      });
      setSmartBreakLoading(false);
      return;
    }
    try {
      const response = await focusSessionService.smartBreakQuestion(session.id);
      setSmartBreakQuestion(response.question);
    } catch (reason) {
      setSmartBreakQuestion(null);
      setError(reason.message);
    } finally {
      setSmartBreakLoading(false);
    }
  };

  const requestQuitQuiz = async () => {
    if (!session) return;
    setQuitQuizOpen(true);
    setQuitQuizLoading(true);
    setQuitQuizQuestion(null);
    setQuitQuizAnswer("");
    setQuitQuizResult(null);
    if (session.local_test) {
      setQuitQuizQuestion({
        question: "How does Logistic Regression differ from Linear Regression according to the notes?",
        options: ["It predicts binary outcomes using a sigmoid probability", "It predicts only continuous values using a straight line", "It removes the need for training data", "It always uses a threshold of 1.0"],
        correct_answer: "It predicts binary outcomes using a sigmoid probability",
      });
      setQuitQuizLoading(false);
      return;
    }
    try {
      const response = await focusSessionService.smartBreakQuestion(session.id);
      setQuitQuizQuestion(response.question);
    } catch (reason) {
      setQuitQuizOpen(false);
      setError(reason.message);
    } finally {
      setQuitQuizLoading(false);
    }
  };

  const submitQuitQuiz = async (event) => {
    event.preventDefault();
    if (!session || !quitQuizQuestion || !quitQuizAnswer) return;
    setQuitQuizLoading(true);
    try {
      if (session.local_test) {
        if (quitQuizAnswer === quitQuizQuestion.correct_answer) {
          setQuitQuizResult("correct");
          await updateState("quit", "Student passed the Focus exit quiz");
          setQuitQuizOpen(false);
        } else {
          setQuitQuizResult("incorrect");
          setQuitQuizAnswer("");
        }
        return;
      }
      const response = await focusSessionService.smartBreakAnswer(session.id, quitQuizAnswer);
      if (response.correct) {
        setQuitQuizResult("correct");
        await updateState("quit", "Student passed the Focus exit quiz");
        setQuitQuizOpen(false);
      } else {
        setQuitQuizResult("incorrect");
        setQuitQuizAnswer("");
      }
    } catch (reason) {
      setError(reason.message);
    } finally {
      setQuitQuizLoading(false);
    }
  };

  const submitSmartBreak = async (event) => {
    event.preventDefault();
    if (!session || !smartBreakAnswer) return;
    setSmartBreakLoading(true);
    try {
      if (session.local_test) {
        const correct = smartBreakAnswer === smartBreakQuestion?.correct_answer;
        setSmartBreakResult(correct ? "correct" : "incorrect");
        if (correct) {
          const breakUnlockExpiresAt = new Date(Date.now() + 10 * 60 * 1000).toISOString();
          setSession((current) => ({
            ...current,
            focus_state: "PAUSED_BREAK",
            break_unlock_expires_at: breakUnlockExpiresAt,
          }));
          setBreakSeconds(600);
        } else {
          setSmartBreakQuestion(null);
          setSmartBreakAnswer("");
        }
        return;
      }
      const response = await focusSessionService.smartBreakAnswer(session.id, smartBreakAnswer);
      setSmartBreakResult(response.correct ? "correct" : "incorrect");
      setSession((current) => ({
        ...current,
        focus_state: response.focus_state,
        break_unlock_expires_at: response.break_unlock_expires_at || null,
      }));
      if (response.correct) {
        setBreakSeconds(response.break_seconds || 600);
      } else {
        setSmartBreakQuestion(null);
        setSmartBreakAnswer("");
      }
    } catch (reason) {
      setError(reason.message);
    } finally {
      setSmartBreakLoading(false);
    }
  };

  const start = async () => {
    if (session) return setActive(true);
    const startSubjectId = selectedSubjectId || subjects[0]?.id;
    const startResourceIds = selectedResourceIds.length
      ? selectedResourceIds
      : availableResources
        .filter((resource) => resource.processing_status === "READY")
        .map((resource) => resource.id);
    if (!startSubjectId || startResourceIds.length === 0) {
      setError("Choose a subject and at least one ready note to begin.");
      return;
    }
    if (!selectedSubjectId) setSelectedSubjectId(startSubjectId);
    if (selectedResourceIds.length === 0) setSelectedResourceIds(startResourceIds);
    requestFocusFullscreen();
    await beginSession(startSubjectId, selectedTopicId, startResourceIds);
  };

  const mins = String(Math.floor(seconds / 60)).padStart(2, "0");
  const secs = String(seconds % 60).padStart(2, "0");
  const breakMins = String(Math.floor(breakSeconds / 60)).padStart(2, "0");
  const breakSecs = String(breakSeconds % 60).padStart(2, "0");
  const selectedSubject = subjects.find((subject) => subject.id === selectedSubjectId);
  const selectedTopic = availableTopics.find((topic) => topic.id === selectedTopicId);
  const focusTitle = session?.topic_name || selectedTopic?.name || selectedSubject?.name || "Deep focus";

  return (
    <div className="clay-focus page-enter">
      <div className="clay-focus-heading">
        <p className="eyebrow">
          <ShieldCheck size={15} /> DEEP FOCUS SESSION
        </p>
        <h1>{focusTitle}</h1>
        <span className={active ? "focus-live" : "focus-ready"}>
          {active
            ? paused
              ? "Session paused"
              : "Session active"
            : "Ready when you are"}
        </span>
      </div>
      {error && <p className="api-error">{error}</p>}
      {!loading && (
        <div className={`clay-focus-workspace ${active ? "session-active" : ""}`}>
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
              <button className="clay-action primary" onClick={start} disabled={starting}>
                <Play size={16} /> {starting ? "Starting..." : "Start 45-minute session"}
              </button>
            ) : (
              <>
                {smartBreakAuthorized ? (
                  <button className="clay-action" disabled>
                    <Clock3 size={16} /> Break {breakMins}:{breakSecs}
                  </button>
                ) : (
                  <button
                    className="clay-action"
                    onClick={() => updateState(paused ? "resume" : "pause")}
                  >
                    {paused ? <Play size={16} /> : <Pause size={16} />}
                    {paused ? "Resume" : "Pause"}
                  </button>
                )}
                {!paused && (
                  <button className="clay-action focus-break-action" onClick={requestSmartBreak} disabled={smartBreakLoading}>
                    <LockKeyhole size={16} /> {smartBreakLoading ? "Loading..." : "Smart Break"}
                  </button>
                )}
                <button
                  className="clay-action primary"
                  onClick={() => {
                    setActive(false);
                    exitFocusFullscreen();
                    navigate("/knowledge-check", { state: { focusSessionId: session.local_test ? null : session.id } });
                  }}
                >
                  <CheckCircle2 size={16} /> Finish session
                </button>
              </>
            )}
            {active && (
              <button
                className="clay-action clay-quit"
                onClick={requestQuitQuiz}
              >
                <X size={15} /> Quit session
              </button>
            )}
          </div>
        </section>
        {!active ? (
          <section className="clay-focus-setup" aria-label="Focus session setup">
            <div className="clay-focus-setup-heading">
              <BookOpen size={18} />
              <div>
                <strong>Choose your study block</strong>
                <small>Focus sessions use ready, note-grounded resources.</small>
              </div>
            </div>
            <label>
              Subject
              <span className="focus-select-wrap">
                <select
                  value={selectedSubjectId}
                  onChange={(event) => {
                    setSelectedSubjectId(event.target.value);
                    setSelectedTopicId("");
                    setSelectedResourceIds([]);
                    setUploadStatus("");
                  }}
                >
                  <option value="">Select a subject</option>
                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>{subject.name}</option>
                  ))}
                </select>
                <ChevronDown size={15} />
              </span>
            </label>
            <label>
              Topic or chapter
              <span className="focus-select-wrap">
                <select value={selectedTopicId} onChange={(event) => setSelectedTopicId(event.target.value)} disabled={!selectedSubjectId}>
                  <option value="">All topics</option>
                  {availableTopics.map((topic) => (
                    <option key={topic.id} value={topic.id}>{topic.name}</option>
                  ))}
                </select>
                <ChevronDown size={15} />
              </span>
            </label>
            <fieldset>
              <div className="focus-resource-heading">
                <legend>Notes and resources</legend>
                <label className="focus-upload-button" htmlFor="focus-resource-upload">
                  <Upload size={14} /> {uploading ? "Uploading..." : "Upload doc or PDF"}
                </label>
                <input
                  id="focus-resource-upload"
                  type="file"
                  accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={uploadResource}
                  disabled={uploading}
                  hidden
                />
              </div>
              {uploadStatus && <small className="focus-upload-status">{uploadStatus}</small>}
              {availableResources.length === 0 ? (
                <small className="focus-empty">No ready resources for this subject yet.</small>
              ) : (
                <div className="focus-resource-list">
                  {availableResources.map((resource) => {
                    const ready = resource.processing_status === "READY";
                    return (
                      <label className={`focus-resource ${ready ? "" : "is-pending"}`} key={resource.id}>
                        <input
                          type="checkbox"
                          checked={selectedResourceIds.includes(resource.id)}
                          disabled={!ready}
                          onChange={() => setSelectedResourceIds((current) => current.includes(resource.id)
                            ? current.filter((id) => id !== resource.id)
                            : [...current, resource.id])}
                        />
                        <span><strong>{resource.title}</strong><small>{ready ? (resource.resource_type || "Note") : "Processing"}</small></span>
                      </label>
                    );
                  })}
                </div>
              )}
            </fieldset>
          </section>
        ) : (
          <section className="clay-focus-setup clay-study-guide" aria-label="Study guide">
            <div className="clay-focus-setup-heading">
              <BookOpen size={18} />
              <div>
                <strong>Study guide</strong>
                <small>Built from the content in this focus session.</small>
              </div>
            </div>
            {studyGuideLoading && (
              <div className="study-guide-loading">Reading your selected material...</div>
            )}
            {!studyGuideLoading && !studyGuide && (
              <div className="study-guide-loading">Your guide will appear here once the selected study content is ready.</div>
            )}
            {!studyGuideLoading && studyGuide && (
              <div className="study-guide-content">
                <div className="study-guide-intro">
                  <span>YOUR 45-MINUTE PLAN</span>
                  <h2>{studyGuide.title}</h2>
                  <p>{studyGuide.summary}</p>
                </div>
                <ol className="study-guide-steps">
                  {studyGuide.steps.map((step, index) => (
                    <li key={`${step.title || "step"}-${index}`}>
                      <span>{String(index + 1).padStart(2, "0")}</span>
                      <div>
                        <strong>{step.title}</strong>
                        <small>{step.minutes ? `${step.minutes} min` : "Focus block"}</small>
                        <p>{step.detail}</p>
                      </div>
                    </li>
                  ))}
                </ol>
                {studyGuide.key_takeaways?.length > 0 && (
                  <div className="study-guide-section">
                    <span className="study-guide-label">ANCHORS FROM YOUR NOTES</span>
                    <ul>
                      {studyGuide.key_takeaways.map((takeaway, index) => <li key={`${takeaway}-${index}`}>{takeaway}</li>)}
                    </ul>
                  </div>
                )}
                {studyGuide.practice_questions?.length > 0 && (
                  <div className="study-guide-section">
                    <span className="study-guide-label">CHECK YOUR RECALL</span>
                    <ul>
                      {studyGuide.practice_questions.map((question, index) => <li key={`${question}-${index}`}>{question}</li>)}
                    </ul>
                  </div>
                )}
                <small className="study-guide-sources">Sources: {studyGuide.source_titles.join(", ")}</small>
              </div>
            )}
          </section>
        )}
        </div>
      )}
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
          <span>{session?.subject_name || "FOCUS SESSION"}</span>
          <b>{session?.topic_name || "Selected resources"}</b>
          <small>45 minute deep work block</small>
        </div>
      </div>
      {quitQuizOpen && (
        <div className="focus-lock-overlay" role="presentation">
          <section className="focus-lock-dialog" role="dialog" aria-modal="true" aria-labelledby="quit-quiz-title">
            <div className="focus-lock-icon"><ShieldCheck size={20} /></div>
            <span className="eyebrow">FOCUS EXIT CHECK</span>
            <h2 id="quit-quiz-title">Answer before you quit</h2>
            <p>Show what you learned from this session before ending it early.</p>
            {quitQuizLoading && !quitQuizQuestion ? (
              <div className="focus-break-loading">Preparing a question from your study material...</div>
            ) : quitQuizQuestion ? (
              <form className="focus-break-form" onSubmit={submitQuitQuiz}>
                <strong>{quitQuizQuestion.question}</strong>
                <div className="focus-break-options">
                  {quitQuizQuestion.options.map((option) => (
                    <label className="focus-break-option" key={option}>
                      <input
                        type="radio"
                        name="quit-quiz-answer"
                        value={option}
                        checked={quitQuizAnswer === option}
                        onChange={(event) => setQuitQuizAnswer(event.target.value)}
                      />
                      <span>{option}</span>
                    </label>
                  ))}
                </div>
                {quitQuizResult === "incorrect" && <small className="focus-break-feedback">That answer is not supported by the selected study material. Keep studying.</small>}
                <div className="focus-break-actions">
                  <button type="button" className="clay-action" onClick={() => setQuitQuizOpen(false)}>Keep studying</button>
                  <button type="submit" className="clay-action primary" disabled={!quitQuizAnswer || quitQuizLoading}>Submit answer</button>
                </div>
              </form>
            ) : null}
          </section>
        </div>
      )}
      {smartBreakOpen && (
        <div className="focus-lock-overlay" role="presentation">
          <section className="focus-lock-dialog" role="dialog" aria-modal="true" aria-labelledby="focus-lock-title">
            <div className="focus-lock-icon"><LockKeyhole size={20} /></div>
            <span className="eyebrow">WEBSITE-ONLY FOCUS LOCK</span>
            <h2 id="focus-lock-title">Answer before you take a break</h2>
            <p>RISE can protect this Focus view, but it cannot block other browser tabs or sites.</p>
            {smartBreakLoading && !smartBreakQuestion ? (
              <div className="focus-break-loading"><Clock3 size={18} /> Preparing a note-grounded question...</div>
            ) : smartBreakResult === "correct" ? (
              <div className="focus-break-result success">
                <strong>Break unlocked for 10 minutes.</strong>
                <span>The Focus timer is paused while this authorization is active.</span>
                <button className="clay-action primary" onClick={() => setSmartBreakOpen(false)}>Take break</button>
              </div>
            ) : smartBreakQuestion ? (
              <form className="focus-break-form" onSubmit={submitSmartBreak}>
                <strong>{smartBreakQuestion.question}</strong>
                <div className="focus-break-options">
                  {smartBreakQuestion.options.map((option) => (
                    <label className="focus-break-option" key={option}>
                      <input
                        type="radio"
                        name="smart-break-answer"
                        value={option}
                        checked={smartBreakAnswer === option}
                        onChange={(event) => setSmartBreakAnswer(event.target.value)}
                      />
                      <span>{option}</span>
                    </label>
                  ))}
                </div>
                {smartBreakResult === "incorrect" && <small className="focus-break-feedback">Not quite. Stay with the session and try a fresh question.</small>}
                <div className="focus-break-actions">
                  <button type="button" className="clay-action" onClick={() => setSmartBreakOpen(false)}>Keep studying</button>
                  <button type="submit" className="clay-action primary" disabled={!smartBreakAnswer || smartBreakLoading}><Send size={15} /> Submit answer</button>
                </div>
              </form>
            ) : (
              <div className="focus-break-result">
                <strong>RISE could not prepare that question.</strong>
                <button className="clay-action" onClick={requestSmartBreak}>Try again</button>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
