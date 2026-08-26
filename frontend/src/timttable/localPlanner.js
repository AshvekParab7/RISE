const LOCAL_EVENTS_KEY = "rise_planner_events";
const DEFAULT_SUBJECTS = [
  "Computer Networks",
  "Database Systems",
  "Operating Systems",
];
const WEEKDAYS = [
  "sunday",
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
];

const pad = (value) => String(value).padStart(2, "0");
const normalize = (value) =>
  String(value || "")
    .trim()
    .toLowerCase();
const currentDateKey = () => {
  const date = new Date();
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
};
const shiftDate = (value, offset) => {
  const date = new Date(`${value}T12:00:00`);
  date.setDate(date.getDate() + offset);
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
};
const dayLabel = (value) =>
  new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(new Date(`${value}T12:00:00`));

const subjectChoices = (subjects) => {
  const choices = (subjects || [])
    .map((subject) => ({ id: subject.id, name: subject.name }))
    .filter((subject) => subject.name);
  for (const name of DEFAULT_SUBJECTS) {
    if (
      !choices.some((subject) => normalize(subject.name) === normalize(name))
    ) {
      choices.push({ id: null, name });
    }
  }
  return choices.sort((left, right) => right.name.length - left.name.length);
};

const parseDuration = (text) => {
  const match = text.match(
    /\b(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?|hr)\b/i,
  );
  if (!match) return 45;
  const amount = Number(match[1]);
  const minutes = /hour|hr/i.test(match[2]) ? amount * 60 : amount;
  return Math.max(15, Math.min(180, Math.round(minutes)));
};

const toMinutes = (hourValue, minuteValue, suffix = "") => {
  let hour = Number(hourValue);
  const minute = Number(minuteValue || 0);
  const normalizedSuffix = suffix.toLowerCase().replaceAll(".", "");
  if (minute > 59) return null;
  if (normalizedSuffix === "pm" && hour < 12) hour += 12;
  if (normalizedSuffix === "am" && hour === 12) hour = 0;
  if (!normalizedSuffix && hour < 8) hour += 12;
  if (hour > 23) return null;
  return hour * 60 + minute;
};

const parseTime = (text) => {
  const contextMatch = text.match(
    /\b(?:at|around|from|between)\s+(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?/i,
  );
  const clockMatch = text.match(
    /\b(\d{1,2}):(\d{2})\s*(a\.?m\.?|p\.?m\.?)?\b/i,
  );
  const suffixMatch = text.match(/\b(\d{1,2})\s*(a\.?m\.?|p\.?m\.?)\b/i);
  const match = contextMatch || clockMatch || suffixMatch;
  if (!match) return null;
  const minute = contextMatch ? match[2] : clockMatch ? match[2] : "0";
  const suffix = contextMatch ? match[3] : clockMatch ? match[3] : match[2];
  const minutes = toMinutes(match[1], minute, suffix);
  return minutes === null ? null : { minutes };
};

const parseDay = (text, selectedDay) => {
  const fallback = selectedDay || currentDateKey();
  if (/\btomorrow\b/i.test(text)) return shiftDate(fallback, 1);
  if (/\b(today|tonight)\b/i.test(text)) return fallback;
  const requestedDay = WEEKDAYS.findIndex((weekday) =>
    new RegExp(`\\b${weekday}\\b`, "i").test(text),
  );
  if (requestedDay < 0) return fallback;
  const selectedDate = new Date(`${fallback}T12:00:00`);
  let offset = (requestedDay - selectedDate.getDay() + 7) % 7;
  if (/\bnext\b/i.test(text) && offset === 0) offset = 7;
  return shiftDate(fallback, offset);
};

const hasExplicitDay = (text) =>
  /\b(?:today|tonight|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\b/i.test(
    text,
  ) || /\b20\d{2}-\d{2}-\d{2}\b/.test(text);

const parseAvailability = (text) => {
  const range = text.match(
    /\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?\s*(?:to|until|and|-)\s*(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?\b/i,
  );
  if (range) {
    const start = toMinutes(range[1], range[2], range[3]);
    let end = toMinutes(range[4], range[5], range[6]);
    if (start !== null && end !== null) {
      if (end <= start && !range[3] && !range[6]) end += 12 * 60;
      if (end > start) return { start, end };
    }
  }
  if (/\b(all day|anytime|any time)\b/i.test(text)) {
    return { start: 8 * 60, end: 22 * 60 };
  }
  for (const [label, start, end] of [
    ["morning", 8 * 60, 12 * 60],
    ["afternoon", 13 * 60, 17 * 60],
    ["evening", 17 * 60, 22 * 60],
  ]) {
    if (new RegExp(`\\b${label}\\b`, "i").test(text)) {
      return { start, end };
    }
  }
  const parsedTime = parseTime(text);
  if (parsedTime) {
    return {
      start: parsedTime.minutes,
      end: Math.min(parsedTime.minutes + 120, 22 * 60),
    };
  }
  return /\b(free|available)\b/i.test(text)
    ? { start: 8 * 60, end: 22 * 60 }
    : null;
};

const findSubject = (text, choices) => {
  const normalizedText = normalize(text);
  return choices.find((subject) =>
    normalizedText.includes(normalize(subject.name)),
  );
};

const extractTopic = (text) => {
  const match = text.match(
    /\b(?:about|on|topic|chapter|unit)\s+([^,.!?]+?)(?=\s+(?:today|tomorrow|at|around|from|for)\b|$)/i,
  );
  return match?.[1]?.trim() || "";
};

const timeLabel = (minutes) => {
  const hour = Math.floor(minutes / 60);
  const suffix = hour >= 12 ? "PM" : "AM";
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${pad(minutes % 60)} ${suffix}`;
};

const timeValue = (minutes) =>
  `${pad(Math.floor(minutes / 60))}:${pad(minutes % 60)}`;

const isBlocked = (day, startMinutes, duration, events) =>
  (events || []).some((event) => {
    if (!event.start_at || event.start_at.slice(0, 10) !== day) return false;
    const date = new Date(event.start_at);
    const eventStart = date.getHours() * 60 + date.getMinutes();
    const eventEnd = eventStart + Number(event.duration_minutes || 45);
    return startMinutes < eventEnd && startMinutes + duration > eventStart;
  });

const nextOpenTime = (day, requestedMinutes, duration, events) => {
  let candidate = requestedMinutes;
  while (candidate + duration <= 22 * 60) {
    if (!isBlocked(day, candidate, duration, events)) return candidate;
    candidate += 30;
  }
  return null;
};

export function localPlannerReply({
  history = [],
  subjects = [],
  selectedDay,
  events = [],
  plannerContext = {},
}) {
  const userMessages = history
    .filter((message) => message.role === "user")
    .map((message) => message.content)
    .filter(Boolean);
  const latestMessage = userMessages.at(-1) || "";
  const text = userMessages.join(" ");
  const normalizedText = normalize(text);
  const choices = subjectChoices(subjects);
  const subject = findSubject(text, choices);
  const parsedTime = parseTime(text);
  const availability = parseAvailability(text);
  const lastMessage = latestMessage.trim().toLowerCase();
  const recentAssistantText = history
    .filter((message) => message.role === "assistant")
    .slice(-3)
    .map((message) => message.content)
    .join(" ")
    .toLowerCase();
  const confirmedAvailability =
    !availability &&
    ["yes", "y", "sure", "yes i am free", "yes, i'm free"].includes(
      lastMessage,
    ) &&
    recentAssistantText.includes("free")
      ? { start: 8 * 60, end: 22 * 60 }
      : availability;
  const duration = parseDuration(text);
  const greeting =
    /^(hi|hello|hey|good morning|good afternoon|good evening)\b/i.test(
      latestMessage.trim(),
    );
  const planningRequest =
    greeting ||
    Boolean(subject || parsedTime) ||
    /study|revise|review|learn|exam|assignment|homework|available|free|plan|schedule|focus|practice|prepare|chapter|topic|quiz|test/i.test(
      normalizedText,
    );

  if (!planningRequest) {
    return {
      related: false,
      reply:
        "I can help schedule study sessions, exam preparation, assignments, and revision time.",
      question: null,
      ready: false,
      plan: [],
    };
  }

  if (!subject) {
    return {
      related: true,
      reply:
        "I can turn your availability into a focused study block. Which subject should we plan?",
      question: {
        id: "subject",
        type: "mcq",
        text: "What should you study?",
        options: choices.slice(0, 4).map((choice) => choice.name),
      },
      ready: false,
      plan: [],
    };
  }

  const day = parseDay(text, selectedDay);
  if (!hasExplicitDay(text)) {
    const options = [0, 1, 2].map((offset) => dayLabel(shiftDate(day, offset)));
    return {
      related: true,
      reply: `Which day should I plan ${subject.name} for? I will check your study blocks, exams, and timetable first.`,
      question: {
        id: "day",
        type: "mcq",
        text: "Choose a study day",
        options,
      },
      ready: false,
      plan: [],
    };
  }

  if (!confirmedAvailability) {
    return {
      related: true,
      reply: `Are you free on ${dayLabel(day)}? Tell me a window and I will avoid your existing study blocks and timetable events.`,
      question: {
        id: "availability",
        type: "mcq",
        text: `When are you free on ${dayLabel(day)}?`,
        options: [
          "Morning (08:00-12:00)",
          "Afternoon (13:00-17:00)",
          "Evening (17:00-22:00)",
          "I am free all day",
        ],
      },
      ready: false,
      plan: [],
    };
  }

  const contextEvents = [
    ...events,
    ...(plannerContext.exams || []).map((exam) => ({
      start_at: `${exam.exam_date || exam.date}T${exam.start_time}`,
      duration_minutes: 120,
      title: exam.title,
    })),
    ...(plannerContext.classes || [])
      .filter((entry) => {
        const javascriptDay = new Date(`${day}T12:00:00`).getDay();
        const mondayBasedDay = (javascriptDay + 6) % 7;
        return Number(entry.day_of_week) === mondayBasedDay;
      })
      .map((entry) => ({
        start_at: `${day}T${entry.start_time}`,
        duration_minutes: 60,
        title: entry.subject || entry.title || "College timetable",
      })),
  ];
  const scheduledTime = nextOpenTime(
    day,
    confirmedAvailability.start,
    duration,
    contextEvents,
  );
  if (scheduledTime === null) {
    return {
      related: true,
      reply: `I could not find an open ${duration}-minute window on ${dayLabel(day)}. Choose another start time.`,
      question: {
        id: "availability",
        type: "mcq",
        text: "Choose another start time",
        options: ["Morning (09:00)", "Afternoon (14:00)", "Evening (18:00)"],
      },
      ready: false,
      plan: [],
    };
  }

  const topic = extractTopic(latestMessage);
  const exam = (plannerContext.exams || [])
    .filter(
      (item) =>
        item.subject === subject.name ||
        item.subject === subject.id ||
        item.subject_id === subject.id,
    )
    .sort((left, right) =>
      String(left.exam_date || left.date).localeCompare(
        String(right.exam_date || right.date),
      ),
    )[0];
  const resources = (plannerContext.resources || [])
    .filter(
      (item) =>
        item.subject === subject.name ||
        item.subject === subject.id ||
        item.subject_id === subject.id,
    )
    .slice(0, 2);
  const resourceTitles = resources.map((item) => item.title).filter(Boolean);
  const title = topic
    ? `Study ${subject.name}: ${topic}`
    : `Study ${subject.name}`;
  const adjustment =
    scheduledTime === confirmedAvailability.start
      ? ""
      : " The next open slot is shown to avoid a conflict.";
  const contextDetail = exam
    ? ` Your ${exam.title} is on ${exam.exam_date || exam.date}.`
    : "";
  const resourceDetail = resourceTitles.length
    ? ` You can use ${resourceTitles.join(" and ")} for this session.`
    : "";
  return {
    related: true,
    reply: `I found a ${duration}-minute block for ${subject.name} on ${dayLabel(day)} at ${timeLabel(scheduledTime)}.${adjustment}${contextDetail}${resourceDetail} Add it to your planner?`,
    question: {
      id: "confirmation",
      type: "confirmation",
      text: "Add this study block?",
      options: ["Yes, add it", "No, let me change it"],
    },
    ready: true,
    plan: [
      {
        day: dayLabel(day),
        time: timeValue(scheduledTime),
        title,
        subtopic: topic || "Focused review",
        duration,
        type: "study",
        meta: `${duration} min`,
        subject: subject.id || null,
        resource_titles: resourceTitles,
      },
    ],
  };
}

export function readLocalPlannerEvents() {
  try {
    const value = JSON.parse(localStorage.getItem(LOCAL_EVENTS_KEY) || "[]");
    return Array.isArray(value)
      ? value.filter((event) => event?.id && event?.title && event?.start_at)
      : [];
  } catch {
    return [];
  }
}

export function writeLocalPlannerEvents(events) {
  try {
    localStorage.setItem(LOCAL_EVENTS_KEY, JSON.stringify(events));
  } catch {}
}

export function createLocalPlannerEvent(payload) {
  const identifier =
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return {
    ...payload,
    id: `local-${identifier}`,
    source: "RISE",
    read_only: false,
  };
}
