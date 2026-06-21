"use strict";

const MONTHS = ["January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"];

let settings = { course_codes: [], activities: [] };
let editingId = null;

// --- helpers --------------------------------------------------------------
const $ = (id) => document.getElementById(id);

async function api(path, opts) {
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

function toast(msg, kind = "success", actionHtml = "") {
  const t = $("toast");
  t.className = "toast " + kind;
  t.innerHTML = `<span>${msg}</span>${actionHtml}`;
  t.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (t.hidden = true), kind === "error" ? 6000 : 5000);
}

function fmtHours(v) {
  if (v === "" || v === null || v === undefined) return "—";
  const n = Math.round(parseFloat(v) * 100) / 100;
  return Number.isInteger(n) ? String(n) : String(n);
}

function computeHours(start, end) {
  if (!start || !end) return "";
  const [h0, m0] = start.split(":").map(Number);
  const [h1, m1] = end.split(":").map(Number);
  let mins = (h1 * 60 + m1) - (h0 * 60 + m0);
  if (mins < 0) mins += 24 * 60;
  return fmtHours(mins / 60);
}

// --- sessions -------------------------------------------------------------
async function loadSessions() {
  const sessions = await api("/api/sessions");
  const body = $("sessionsBody");
  body.innerHTML = "";
  $("emptyState").hidden = sessions.length > 0;
  $("countLabel").textContent = sessions.length
    ? `${sessions.length} session${sessions.length > 1 ? "s" : ""} recorded`
    : "No sessions yet";

  for (const s of sessions) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="date-pill">${s.date_display}</td>
      <td>${s.course_code}</td>
      <td>${s.activity}</td>
      <td>${s.time_started}</td>
      <td>${s.time_ended}</td>
      <td><span class="hours-pill">${s.hours}</span></td>
      <td><div class="row-actions">
        <button class="icon-btn" data-edit="${s.id}">Edit</button>
        <button class="icon-btn del" data-del="${s.id}">Delete</button>
      </div></td>`;
    body.appendChild(tr);
  }
  body.querySelectorAll("[data-edit]").forEach((b) =>
    b.addEventListener("click", () => openSession(sessions.find((x) => x.id === b.dataset.edit))));
  body.querySelectorAll("[data-del]").forEach((b) =>
    b.addEventListener("click", () => deleteSession(b.dataset.del)));
}

async function deleteSession(id) {
  if (!confirm("Delete this session?")) return;
  await api(`/api/sessions/${id}`, { method: "DELETE" });
  toast("Session deleted");
  loadSessions();
}

// --- session modal --------------------------------------------------------
function openSession(s) {
  editingId = s ? s.id : null;
  $("sessionModalTitle").textContent = s ? "Edit session" : "Add session";
  $("sessionError").hidden = true;

  $("fDate").value = s ? s.date : new Date().toISOString().slice(0, 10);
  buildCourseOptions(s ? s.course_code : "");
  buildActivityOptions(s ? s.activity : "");
  $("fStart").value = s ? s.time_started : "14:00";
  $("fEnd").value = s ? s.time_ended : "17:00";
  const hasOverride = s && s.total_hours_override !== null && s.total_hours_override !== undefined;
  $("fOverrideOn").checked = !!hasOverride;
  $("fOverrideVal").value = hasOverride ? s.total_hours_override : "";
  $("fOverrideVal").disabled = !hasOverride;
  refreshAuto();
  $("sessionModal").hidden = false;
  $("fCourse").focus();
}

function buildCourseOptions(selected) {
  const sel = $("fCourse");
  const codes = settings.course_codes || [];
  if (!codes.length) {
    sel.innerHTML = '<option value="" disabled selected>No course codes — add them in ⚙ Settings</option>';
    return;
  }
  sel.innerHTML = '<option value="" disabled>Choose…</option>';
  let found = false;
  for (const c of codes) {
    const o = document.createElement("option");
    o.value = c; o.textContent = c;
    if (c === selected) { o.selected = true; found = true; }
    sel.appendChild(o);
  }
  // keep an existing code that's no longer in the configured list
  if (selected && !found) {
    const o = document.createElement("option");
    o.value = selected; o.textContent = selected; o.selected = true;
    sel.appendChild(o);
  }
  if (!selected) sel.value = "";
}

function buildActivityOptions(selected) {
  const sel = $("fActivity");
  sel.innerHTML = '<option value="" disabled>Choose…</option>';
  for (const a of settings.activities) {
    const o = document.createElement("option");
    o.value = a; o.textContent = a;
    if (a === selected) o.selected = true;
    sel.appendChild(o);
  }
  if (!selected) sel.value = "";
}

function refreshAuto() {
  $("autoHours").textContent = computeHours($("fStart").value, $("fEnd").value) || "—";
}

async function saveSession() {
  const payload = {
    date: $("fDate").value,
    course_code: $("fCourse").value.trim(),
    activity: $("fActivity").value,
    time_started: $("fStart").value,
    time_ended: $("fEnd").value,
    total_hours_override: $("fOverrideOn").checked ? $("fOverrideVal").value : null,
  };
  try {
    if (editingId) {
      await api(`/api/sessions/${editingId}`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      toast("Session updated");
    } else {
      await api("/api/sessions", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      toast("Session added");
    }
    $("sessionModal").hidden = true;
    loadSessions();
  } catch (e) {
    const err = $("sessionError");
    err.textContent = e.message;
    err.hidden = false;
  }
}

// --- settings -------------------------------------------------------------
async function loadSettings() {
  settings = await api("/api/settings");
}

function openSettings() {
  $("sName").value = settings.student_name || "";
  $("sNo").value = settings.student_no || "";
  $("sSchool").value = settings.school || "";
  $("sLogo").value = settings.logo_path || "";
  $("sLogoW").value = settings.logo_width_cm || 4.3;
  $("sCourses").value = (settings.course_codes || []).join("\n");
  $("settingsError").hidden = true;
  $("settingsModal").hidden = false;
}

async function saveSettings() {
  const payload = {
    student_name: $("sName").value,
    student_no: $("sNo").value,
    school: $("sSchool").value,
    logo_path: $("sLogo").value,
    logo_width_cm: $("sLogoW").value,
    course_codes: $("sCourses").value,
  };
  try {
    await api("/api/settings", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    $("settingsModal").hidden = true;
    await loadSettings();
    toast("Settings saved");
  } catch (e) {
    const err = $("settingsError");
    err.textContent = e.message;
    err.hidden = false;
  }
}

// --- generate -------------------------------------------------------------
function buildGenSelectors() {
  const m = $("genMonth");
  const now = new Date();
  MONTHS.forEach((name, i) => {
    const o = document.createElement("option");
    o.value = i + 1; o.textContent = name;
    if (i === now.getMonth()) o.selected = true;
    m.appendChild(o);
  });
  const y = $("genYear");
  for (let yr = now.getFullYear() - 2; yr <= now.getFullYear() + 2; yr++) {
    const o = document.createElement("option");
    o.value = yr; o.textContent = yr;
    if (yr === now.getFullYear()) o.selected = true;
    y.appendChild(o);
  }
}

async function generate() {
  const month = $("genMonth").value;
  const year = $("genYear").value;
  try {
    const res = await api("/api/generate", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ month, year }),
    });
    const monthName = MONTHS[month - 1];
    const link = `<a href="/api/download/${monthName}/${year}" download>Download ${res.filename}</a>`;
    toast(`Form created (${res.count} sessions).`, "success", link);
    if (res.logo_warning) {
      setTimeout(() => toast("Note: no logo image found — a text placeholder was used. Set it in Settings.", "error"), 600);
    }
    // trigger the download automatically
    window.location.href = `/api/download/${monthName}/${year}`;
  } catch (e) {
    toast(e.message, "error");
  }
}

// --- wiring ---------------------------------------------------------------
function init() {
  buildGenSelectors();
  $("addBtn").addEventListener("click", () => openSession(null));
  $("settingsBtn").addEventListener("click", openSettings);
  $("generateBtn").addEventListener("click", generate);

  $("sessionSave").addEventListener("click", saveSession);
  $("sessionCancel").addEventListener("click", () => ($("sessionModal").hidden = true));
  $("settingsSave").addEventListener("click", saveSettings);
  $("settingsCancel").addEventListener("click", () => ($("settingsModal").hidden = true));

  $("fStart").addEventListener("input", refreshAuto);
  $("fEnd").addEventListener("input", refreshAuto);
  $("fOverrideOn").addEventListener("change", (e) => {
    $("fOverrideVal").disabled = !e.target.checked;
    if (e.target.checked) $("fOverrideVal").focus();
  });

  // close modals on overlay click / Escape
  document.querySelectorAll(".modal-overlay").forEach((ov) =>
    ov.addEventListener("click", (e) => { if (e.target === ov) ov.hidden = true; }));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") document.querySelectorAll(".modal-overlay").forEach((o) => (o.hidden = true));
  });

  loadSettings().then(loadSessions);
}

document.addEventListener("DOMContentLoaded", init);
