/* ==========================================================================
   Smart Attendance System — Demo Data & Storage Helpers
   This file simulates a backend. Every function here is written so a real
   Python/Flask (or FastAPI) API can be dropped in later — see the
   "BACKEND HOOK" comments for exactly where a fetch() call would go.
   ========================================================================== */

const SAS = (() => {

  const STORAGE_KEYS = {
    auth: "sas_auth",
    facultyName: "sas_faculty_name",
    sessions: "sas_sessions",
    currentSession: "sas_current_session",
  };

  /* ---------------- Seed / static demo data ---------------- */

  const COURSES = [
    "Data Structures",
    "Operating Systems",
    "Database Management Systems",
    "Computer Networks",
    "Software Engineering",
  ];

  const ROOMS = ["AB1-301", "AB1-302", "AB2-201", "AB2-305"];

  const STUDENTS = [
    { id: "101", name: "Ananya Sharma" },
    { id: "102", name: "Rahul Verma" },
    { id: "103", name: "Priya Nair" },
    { id: "104", name: "Karthik Iyer" },
    { id: "105", name: "Sneha Reddy" },
    { id: "106", name: "Aditya Kumar" },
    { id: "107", name: "Meera Pillai" },
    { id: "108", name: "Rohan Gupta" },
    { id: "109", name: "Divya Menon" },
    { id: "110", name: "Arjun Singh" },
    { id: "111", name: "Kavya Krishnan" },
    { id: "112", name: "Vikram Rao" },
    { id: "113", name: "Ishita Das" },
    { id: "114", name: "Nikhil Joshi" },
  ];

  const SEED_SESSIONS = [
    { id: "S1001", date: "2026-09-12", time: "09:00 AM", course: "Data Structures", room: "AB1-301", total: 14, present: 13, absent: 1 },
    { id: "S1002", date: "2026-09-11", time: "11:00 AM", course: "Operating Systems", room: "AB2-201", total: 14, present: 12, absent: 2 },
    { id: "S1003", date: "2026-09-11", time: "02:00 PM", course: "Database Management Systems", room: "AB1-302", total: 14, present: 14, absent: 0 },
    { id: "S1004", date: "2026-09-10", time: "10:00 AM", course: "Computer Networks", room: "AB2-305", total: 14, present: 10, absent: 4 },
    { id: "S1005", date: "2026-09-09", time: "09:00 AM", course: "Software Engineering", room: "AB1-301", total: 14, present: 11, absent: 3 },
    { id: "S1006", date: "2026-09-08", time: "11:00 AM", course: "Data Structures", room: "AB1-301", total: 14, present: 13, absent: 1 },
  ];

  const AVATAR_COLORS = ["#4F46E5", "#7C3AED", "#0EA5A5", "#E8A33D", "#DC4C4C", "#16A34A"];

  function initials(name) {
    return name.split(" ").map(w => w[0]).slice(0, 2).join("").toUpperCase();
  }

  function colorFor(id) {
    const n = parseInt(String(id).replace(/\D/g, ""), 10) || 0;
    return AVATAR_COLORS[n % AVATAR_COLORS.length];
  }

  /* ---------------- Storage helpers ---------------- */

  function readJSON(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (e) {
      return fallback;
    }
  }

  function writeJSON(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  }

  function ensureSeeded() {
    if (!localStorage.getItem(STORAGE_KEYS.sessions)) {
      writeJSON(STORAGE_KEYS.sessions, SEED_SESSIONS);
    }
  }
  ensureSeeded();

  /* ---------------- Auth ---------------- */

  function isLoggedIn() {
    return localStorage.getItem(STORAGE_KEYS.auth) === "true";
  }

  function login(name) {
    // BACKEND HOOK: replace with POST /api/auth/login { email, password }
    localStorage.setItem(STORAGE_KEYS.auth, "true");
    localStorage.setItem(STORAGE_KEYS.facultyName, name || "Dr. Meera Kulkarni");
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEYS.auth);
    window.location.href = "index.html";
  }

  function facultyName() {
    return localStorage.getItem(STORAGE_KEYS.facultyName) || "Dr. Meera Kulkarni";
  }

  /** Redirects to login if the faculty is not authenticated. Call at the
   *  top of every protected page. */
  function requireAuth() {
    if (!isLoggedIn()) window.location.href = "index.html";
  }

  /* ---------------- Sessions / attendance history ---------------- */

  function getSessions() {
    // BACKEND HOOK: replace with GET /api/sessions
    return readJSON(STORAGE_KEYS.sessions, SEED_SESSIONS);
  }

  function getSessionById(id) {
    return getSessions().find(s => s.id === id);
  }

  function saveSession(session) {
    // BACKEND HOOK: replace with POST /api/sessions
    const all = getSessions();
    all.unshift(session);
    writeJSON(STORAGE_KEYS.sessions, all);
  }

  /* ---------------- In-progress session (Take Attendance flow) ---------------- */

  function setCurrentSession(data) {
    writeJSON(STORAGE_KEYS.currentSession, data);
  }

  function getCurrentSession() {
    return readJSON(STORAGE_KEYS.currentSession, null);
  }

  /** Builds a plausible fake recognition result from the registered
   *  students list. This is ONLY for frontend demo purposes — the real
   *  version will come from the Python face-recognition backend. */
  function simulateRecognitionResult() {
    // BACKEND HOOK: replace entirely with the JSON response of
    // POST /api/attendance/recognize  (multipart form: image, course, room, session)
    const roster = STUDENTS.slice(0, 12 + Math.floor(Math.random() * 3));
    let presentCount = 0;
    const results = roster.map(s => {
      const present = Math.random() > 0.18;
      if (present) presentCount++;
      return {
        id: s.id,
        name: s.name,
        status: present ? "Present" : "Absent",
        confidence: present ? Math.round(88 + Math.random() * 11) : null,
      };
    });
    return {
      total: roster.length,
      present: presentCount,
      absent: roster.length - presentCount,
      accuracy: Math.round(94 + Math.random() * 4),
      students: results,
    };
  }

  /* ---------------- Dashboard aggregates ---------------- */

  function dashboardStats() {
    const sessions = getSessions();
    const today = sessions.filter(s => s.date === "2026-09-12");
    const totalStudents = STUDENTS.length;
    const latest = today[0] || sessions[0];
    const pct = latest ? Math.round((latest.present / latest.total) * 100) : 0;
    return {
      totalStudents,
      present: latest ? latest.present : 0,
      absent: latest ? latest.absent : 0,
      pct,
    };
  }

  return {
    COURSES, ROOMS, STUDENTS,
    initials, colorFor,
    isLoggedIn, login, logout, facultyName, requireAuth,
    getSessions, getSessionById, saveSession,
    setCurrentSession, getCurrentSession, simulateRecognitionResult,
    dashboardStats,
  };
})();
