/* ==========================================================================
   Shared UI wiring used on every dashboard-style page (sidebar, topbar,
   toasts). Runs after data.js has loaded.
   ========================================================================== */

const SIDEBAR_LINKS = [
  { key: "dashboard", href: "dashboard.html", icon: "layout-dashboard", label: "Dashboard" },
  { key: "attendance", href: "take-attendance.html", icon: "camera", label: "Take Attendance" },
  { key: "history", href: "history.html", icon: "history", label: "Attendance History" },
  { key: "reports", href: "history.html", icon: "bar-chart-3", label: "Reports" },
  { key: "students", href: "student-details.html?id=101", icon: "users", label: "Students" },
  { key: "profile", href: "#", icon: "user", label: "Profile" },
  { key: "settings", href: "#", icon: "settings", label: "Settings" },
];

/** Builds the sidebar markup into #sidebarRoot and highlights the active
 *  link. Call this once near the top of each protected page's script. */
function renderSidebar(activeKey) {
  const root = document.getElementById("sidebarRoot");
  if (!root) return;

  const navHTML = SIDEBAR_LINKS.map(link => `
    <a href="${link.href}" class="nav-link ${link.key === activeKey ? "active" : ""}">
      <i data-lucide="${link.icon}" class="icon"></i> ${link.label}
    </a>`).join("");

  root.innerHTML = `
    <button class="sidebar-toggle" aria-label="Toggle menu"><i data-lucide="menu" class="icon"></i></button>
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark"><i data-lucide="scan-face" class="icon" style="stroke:white"></i></div>
        <div class="brand-name">Smart Attendance<span>Face Recognition Platform</span></div>
      </div>

      <nav>
        <div class="nav-group">
          <div class="nav-label">Main</div>
          ${navHTML}
        </div>
      </nav>

      <div class="sidebar-footer">
        <a href="#" class="js-logout nav-link" style="margin-bottom:10px;">
          <i data-lucide="log-out" class="icon"></i> Logout
        </a>
        <div class="sidebar-user">
          <div class="avatar js-faculty-initials"></div>
          <div class="sidebar-user-info">
            <div class="name js-faculty-name"></div>
            <div class="role">Faculty</div>
          </div>
        </div>
      </div>
    </aside>`;

  if (window.lucide) lucide.createIcons();
}

document.addEventListener("DOMContentLoaded", () => {
  // Fill in faculty name / initials wherever placeholders exist
  document.querySelectorAll(".js-faculty-name").forEach(el => {
    el.textContent = SAS.facultyName();
  });
  document.querySelectorAll(".js-faculty-initials").forEach(el => {
    el.textContent = SAS.initials(SAS.facultyName());
  });

  // Mobile sidebar toggle
  const toggleBtn = document.querySelector(".sidebar-toggle");
  const sidebar = document.querySelector(".sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", () => sidebar.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (sidebar.classList.contains("open") &&
          !sidebar.contains(e.target) &&
          !toggleBtn.contains(e.target)) {
        sidebar.classList.remove("open");
      }
    });
  }

  // Logout buttons
  document.querySelectorAll(".js-logout").forEach(el => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      SAS.logout();
    });
  });
});

/** Small toast notification, reused across pages. */
function showToast(message, iconSvg) {
  let toast = document.querySelector(".toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.innerHTML = (iconSvg || '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 6 9 17l-5-5" stroke-linecap="round" stroke-linejoin="round"/></svg>') +
    `<span>${message}</span>`;
  toast.classList.add("show");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.remove("show"), 3200);
}
