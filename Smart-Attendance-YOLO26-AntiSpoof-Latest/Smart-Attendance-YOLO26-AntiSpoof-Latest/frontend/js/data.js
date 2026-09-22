/* ==========================================================================
   Smart Attendance System — Production API Integration & Client Storage
   ========================================================================== */

const SAS = (() => {
  const API_BASE = window.location.origin;

  const STORAGE_KEYS = {
    auth: "sas_auth",
    token: "sas_token",
    role: "sas_role",
    user: "sas_user",
    facultyName: "sas_faculty_name",
    sessions: "sas_sessions",
    currentSession: "sas_current_session",
    analysisResult: "sas_analysis_result",
  };

  /* ---------------- Fallback / Default Data ---------------- */
  let COURSES = [
    "CSE2025 - Computer Architecture",
    "CSE4006 - Deep Learning",
    "CSE2008 - Operating Systems",
    "CSE3004 - Design and Analysis of Algorithms",
    "STS3007 - Soft Skills",
    "CSE3003 - Computer Networks",
  ];

  let ROOMS = ["401", "402", "403", "504", "505", "506"];

  let STUDENTS = [
    { id: "24BCA3008", name: "Student 3008" },
    { id: "24BCA3456", name: "Student 3456" },
    { id: "24BCA4890", name: "Student 4890" },
    { id: "24BCA5631", name: "Student 5631" },
    { id: "24BCA6789", name: "Student 6789" },
    { id: "24BCA7237", name: "Student 7237" },
    { id: "24BCA7286", name: "Student 7286" },
    { id: "24BCA7313", name: "Student 7313" },
    { id: "24BCA7428", name: "Student 7428" },
    { id: "24BCA7569", name: "Student 7569" },
    { id: "24BCA7913", name: "Student 7913" },
    { id: "24BCA8190", name: "Student 8190" },
    { id: "24BCA8920", name: "Student 8920" },
    { id: "24BCA9012", name: "Student 9012" },
  ];

  const AVATAR_COLORS = ["#4F46E5", "#7C3AED", "#0EA5A5", "#E8A33D", "#DC4C4C", "#16A34A"];

  function initials(name) {
    if (!name) return "FA";
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

  /* ---------------- Auth ---------------- */
  function isLoggedIn() {
    return localStorage.getItem(STORAGE_KEYS.auth) === "true";
  }

  function getToken() {
    return localStorage.getItem(STORAGE_KEYS.token) || "";
  }

  function getAuthHeaders() {
    const token = getToken();
    const headers = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return headers;
  }

  async function login(username, password) {
    username = username || "faculty";
    password = password || "faculty123";

    try {
      const resp = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      if (!resp.ok) {
        // Fallback for offline demo
        localStorage.setItem(STORAGE_KEYS.auth, "true");
        localStorage.setItem(STORAGE_KEYS.facultyName, username);
        return { success: true, role: "FACULTY", name: username };
      }

      const data = await resp.json();
      localStorage.setItem(STORAGE_KEYS.auth, "true");
      localStorage.setItem(STORAGE_KEYS.token, data.access_token);
      localStorage.setItem(STORAGE_KEYS.role, data.role);
      localStorage.setItem(STORAGE_KEYS.facultyName, data.name || username);
      writeJSON(STORAGE_KEYS.user, data);
      return { success: true, ...data };
    } catch (err) {
      console.warn("API login failed, using local session:", err);
      localStorage.setItem(STORAGE_KEYS.auth, "true");
      localStorage.setItem(STORAGE_KEYS.facultyName, username);
      return { success: true, role: "FACULTY", name: username };
    }
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEYS.auth);
    localStorage.removeItem(STORAGE_KEYS.token);
    localStorage.removeItem(STORAGE_KEYS.role);
    localStorage.removeItem(STORAGE_KEYS.user);
    window.location.href = "index.html";
  }

  function facultyName() {
    return localStorage.getItem(STORAGE_KEYS.facultyName) || "Dr. Anil Kumar";
  }

  function requireAuth() {
    if (!isLoggedIn()) window.location.href = "index.html";
  }

  /* ---------------- Dynamic API loaders ---------------- */
  async function loadCourses() {
    try {
      const resp = await fetch(`${API_BASE}/courses`);
      if (resp.ok) {
        const data = await resp.json();
        COURSES = data.map(c => `${c.course_id} - ${c.course_name}`);
        return data;
      }
    } catch (e) {
      console.warn("Could not fetch courses from backend:", e);
    }
    return COURSES;
  }

  async function loadRooms() {
    try {
      const resp = await fetch(`${API_BASE}/rooms`);
      if (resp.ok) {
        const data = await resp.json();
        ROOMS = data.map(r => String(r.room_number));
        return data;
      }
    } catch (e) {
      console.warn("Could not fetch rooms from backend:", e);
    }
    return ROOMS;
  }

  async function loadStudents() {
    try {
      const resp = await fetch(`${API_BASE}/students`);
      if (resp.ok) {
        const data = await resp.json();
        STUDENTS = data.map(s => ({ id: s.student_id, name: s.name }));
        return data;
      }
    } catch (e) {
      console.warn("Could not fetch students from backend:", e);
    }
    return STUDENTS;
  }

  /* ---------------- Sessions / attendance history ---------------- */
  async function getSessions() {
    try {
      const resp = await fetch(`${API_BASE}/attendance/sessions`);
      if (resp.ok) {
        const data = await resp.json();
        if (data && data.length > 0) {
          writeJSON(STORAGE_KEYS.sessions, data);
          return data;
        }
      }
    } catch (e) {
      console.warn("Could not fetch sessions from backend:", e);
    }
    return readJSON(STORAGE_KEYS.sessions, []);
  }

  function getSessionById(id) {
    const list = readJSON(STORAGE_KEYS.sessions, []);
    return list.find(s => s.id === id || s.session_id === id);
  }

  function saveSession(session) {
    const all = readJSON(STORAGE_KEYS.sessions, []);
    all.unshift(session);
    writeJSON(STORAGE_KEYS.sessions, all);
  }

  /* ---------------- Take Attendance Flow ---------------- */
  function setCurrentSession(data) {
    writeJSON(STORAGE_KEYS.currentSession, data);
  }

  function getCurrentSession() {
    return readJSON(STORAGE_KEYS.currentSession, null);
  }

  async function analyzeClassroomImage(imageBlob, filename = "capture.jpg") {
    const formData = new FormData();
    formData.append("image", imageBlob, filename);

    const resp = await fetch(`${API_BASE}/analyze-image`, {
      method: "POST",
      body: formData,
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: "Image analysis failed" }));
      throw new Error(err.detail || "Image analysis failed");
    }

    return await resp.json();
  }

  async function commitAttendanceSession(payload) {
    const resp = await fetch(`${API_BASE}/attendance`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: "Saving attendance failed" }));
      throw new Error(err.detail || "Saving attendance failed");
    }

    return await resp.json();
  }

  /* ---------------- Dashboard aggregates ---------------- */
  async function dashboardStats() {
    try {
      const resp = await fetch(`${API_BASE}/analytics`);
      if (resp.ok) {
        const data = await resp.json();
        return {
          totalStudents: data.total_students,
          totalCourses: data.total_courses,
          totalSessions: data.total_sessions,
          pct: Math.round(data.overall_attendance_rate),
        };
      }
    } catch (e) {
      console.warn("Could not fetch analytics:", e);
    }

    const sessions = readJSON(STORAGE_KEYS.sessions, []);
    const totalStudents = STUDENTS.length;
    const latest = sessions[0];
    const pct = latest && latest.total > 0 ? Math.round((latest.present / latest.total) * 100) : 0;
    return {
      totalStudents,
      totalCourses: COURSES.length,
      totalSessions: sessions.length,
      present: latest ? latest.present : 0,
      absent: latest ? latest.absent : 0,
      pct,
    };
  }

  // Auto-init loaders in background
  if (typeof window !== "undefined") {
    loadCourses();
    loadRooms();
    loadStudents();
  }

  return {
    COURSES, ROOMS, STUDENTS,
    initials, colorFor,
    isLoggedIn, login, logout, facultyName, requireAuth,
    getSessions, getSessionById, saveSession,
    setCurrentSession, getCurrentSession,
    analyzeClassroomImage, commitAttendanceSession,
    loadCourses, loadRooms, loadStudents,
    dashboardStats,
  };
})();
