// ═══════════════════════════════════════════════════════════════════════════
// IntelliTrack — SIH 26122  |  Frontend ↔ Backend Connection
// API Base: http://localhost:8000
// All pages fully wired to FastAPI backend
// ═══════════════════════════════════════════════════════════════════════════

const titles = {
  dashboard: 'Project Dashboard', projects: 'Projects', schedule: 'Schedule Import',
  reports: 'Progress Reports', matching: 'AI Activity Matching',
  tracking: 'Progress Tracking', settings: 'Settings'
};

const $ = id => document.getElementById(id);
let API = localStorage.getItem('projectbridge_api') || 'http://localhost:8000';
let CURRENT_PROJECT_ID = localStorage.getItem('projectbridge_project') || '';

// ─── Toast ───────────────────────────────────────────────────────────────────
function toast(s, type = 'info') {
  const t = $('toast');
  t.textContent = s;
  t.className = 'toast show' + (type === 'error' ? ' error' : type === 'ok' ? ' ok' : '');
  setTimeout(() => t.classList.remove('show'), 3200);
}

// ─── Navigation ──────────────────────────────────────────────────────────────
function go(page) {
  document.querySelectorAll('.page').forEach(x => x.classList.remove('active'));
  $(page)?.classList.add('active');
  document.querySelectorAll('.nav').forEach(x => x.classList.toggle('active', x.dataset.page === page));
  $('pageTitle').textContent = titles[page] || 'Dashboard';
  $('sidebar').classList.remove('open');
  if (page === 'dashboard') loadDashboard();
  if (page === 'projects') loadProjects();
  if (page === 'schedule') loadScheduleProjects();
  if (page === 'matching') loadMatching();
  if (page === 'tracking') loadTracking();
  if (page === 'reports') loadReportsPage();
  if (page === 'chat') loadChat();
}

document.querySelectorAll('[data-page]').forEach(x => x.addEventListener('click', () => go(x.dataset.page)));
$('menuBtn').onclick = () => $('sidebar').classList.toggle('open');
$('today').textContent = new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date());

// ─── API fetch helper ─────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const headers = isFormData ? {} : { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const r = await fetch(API + path, { ...options, headers });
  if (!r.ok) {
    let msg = `Request failed (${r.status})`;
    try { const e = await r.json(); msg = e.detail || msg; } catch {}
    throw new Error(msg);
  }
  if (r.status === 204) return null;
  return r.json();
}

// ─── Backend health check ─────────────────────────────────────────────────────
async function checkBackend() {
  try {
    const r = await fetch(API + '/api/health', { signal: AbortSignal.timeout(2000) });
    if (!r.ok) throw 0;
    $('apiStatus').textContent = 'Connected';
    $('apiStatus').style.color = '#63d49b';
  } catch {
    $('apiStatus').textContent = 'Offline';
    $('apiStatus').style.color = '#e0a020';
  }
}

// ─── Utility ──────────────────────────────────────────────────────────────────
function formatDate(v) {
  if (!v) return '—';
  const d = new Date(v);
  return Number.isNaN(d.getTime()) ? v : d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}
function escapeHtml(v) {
  return String(v ?? '').replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c]));
}
function riskBadge(level) {
  const map = { HIGH: 'danger', MEDIUM: 'warn', LOW: 'ok' };
  return `<label class="${map[level] || 'ok'}">${level || 'LOW'}</label>`;
}
function statusBadge(s) {
  const map = { matched: 'ok', flagged: 'warn', unmatched: 'danger' };
  return `<label class="${map[s] || 'warn'}">${(s || 'unmatched').toUpperCase()}</label>`;
}

// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD
// ═══════════════════════════════════════════════════════════════════════════
function drawChart(planned = [], actual = []) {
  const c = $('chart');
  if (!c) return;
  const w = c.clientWidth, h = c.clientHeight, d = devicePixelRatio || 1;
  c.width = w * d; c.height = h * d;
  const ctx = c.getContext('2d'); ctx.scale(d, d);
  const p = { l: 30, r: 8, t: 12, b: 15 }, cw = w - p.l - p.r, ch = h - p.t - p.b;
  ctx.font = '10px system-ui'; ctx.fillStyle = '#7b8694'; ctx.strokeStyle = '#edf0f3';
  for (let i = 0; i <= 4; i++) {
    let y = p.t + ch * i / 4;
    ctx.beginPath(); ctx.moveTo(p.l, y); ctx.lineTo(w - p.r, y); ctx.stroke();
    ctx.fillText((100 - i * 25) + '%', 2, y + 3);
  }
  function line(a, color) {
    if (!a.length) return;
    ctx.beginPath();
    a.forEach((v, i) => { let X = p.l + cw * i / (a.length - 1), Y = p.t + ch * (1 - v / 100); i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y); });
    ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke();
  }
  line(planned, '#a7b1bc');
  line(actual, '#1769e0');
}
window.onresize = () => drawChart();

async function loadDashboard() {
  try {
    const projects = await apiFetch('/api/projects');
    if (!projects || !projects.length) {
      $('dashboardProjectName').textContent = 'No project selected';
      $('dashboardProjectDescription').textContent = 'Create a project first, then import a schedule.';
      ['dashboardProgress', 'dashboardActivities', 'dashboardOnSchedule', 'dashboardAtRisk'].forEach(id => $(id).textContent = '—');
      drawChart();
      return;
    }
    const project = CURRENT_PROJECT_ID ? projects.find(p => p.id === CURRENT_PROJECT_ID) || projects[0] : projects[0];
    CURRENT_PROJECT_ID = project.id;
    const progress = Number(project.overall_progress || 0);
    $('dashboardProjectName').textContent = project.name || 'Unnamed Project';
    $('dashboardProjectDescription').textContent = `${project.location || '—'} · ${project.project_type || 'Infrastructure'}`;
    $('dashboardProgress').textContent = `${progress.toFixed(1).replace('.0', '')}%`;
    $('dashboardProgressNote').textContent = `Current progress of ${project.name}`;
    $('dashboardProgressBar').style.width = `${Math.max(0, Math.min(100, progress))}%`;

    // Load baseline activities count
    try {
      const activities = await apiFetch(`/api/projects/${encodeURIComponent(project.id)}/schedule/activities`);
      $('dashboardActivities').textContent = activities.length;
      $('dashboardActivitiesNote').textContent = activities.length ? `${activities.length} baseline activities` : 'No schedule imported';

      const disciplines = {};
      activities.forEach(a => {
        const disc = a.discipline || 'Other';
        if (!disciplines[disc]) disciplines[disc] = { total: 0, progress: 0 };
        disciplines[disc].total++;
        disciplines[disc].progress += Number(a.planned_progress || 0);
      });
      $('disciplineProgress').innerHTML = Object.entries(disciplines).map(([disc, data]) => {
        const avg = data.progress / data.total;
        return `<div class="discipline-row"><div><b>${escapeHtml(disc)}</b><small>${data.total} activities</small></div>
          <strong>${avg.toFixed(1).replace('.0', '')}%</strong>
          <div class="bar"><i style="width:${Math.max(0, Math.min(100, avg))}%"></i></div></div>`;
      }).join('') || '<p class="empty">No activity data yet.</p>';
    } catch {
      $('dashboardActivities').textContent = '—';
      $('dashboardActivitiesNote').textContent = 'No schedule imported';
      $('disciplineProgress').innerHTML = '<p class="empty">Import a schedule to see discipline progress.</p>';
    }

    // Load AI progress events for At-Risk / On Schedule
    try {
      const eventsRes = await apiFetch(`/api/v1/activities/?project_id=${encodeURIComponent(project.id)}&limit=200`);
      const events = eventsRes.activities || [];
      const atRisk = events.filter(e => e.prediction?.risk_level === 'HIGH').length;
      const matched = events.filter(e => e.status === 'matched').length;
      $('dashboardAtRisk').textContent = atRisk;
      $('dashboardAtRiskNote').textContent = atRisk ? `${atRisk} high-risk events` : 'No high-risk events';
      $('dashboardOnSchedule').textContent = matched;
      $('dashboardOnScheduleNote').textContent = matched ? `${matched} verified matches` : 'No verified matches yet';

      // Attention table — flagged events
      const flagged = events.filter(e => e.status === 'flagged' || e.prediction?.risk_level === 'HIGH').slice(0, 5);
      if (flagged.length) {
        $('attentionEmpty').style.display = 'none';
        const table = `<table><thead><tr><th>Activity</th><th>Discipline</th><th>Risk</th><th>Status</th><th>Variance</th></tr></thead><tbody>
          ${flagged.map(e => `<tr>
            <td>${escapeHtml(e.extracted_activity || '—')}</td>
            <td>${escapeHtml(e.discipline || '—')}</td>
            <td>${riskBadge(e.prediction?.risk_level)}</td>
            <td>${statusBadge(e.status)}</td>
            <td class="${(e.prediction?.variance_days || 0) > 0 ? 'red' : 'good'}">${e.prediction?.variance_days > 0 ? '+' : ''}${e.prediction?.variance_days?.toFixed(1) ?? '—'}d</td>
          </tr>`).join('')}
        </tbody></table>`;
        $('attentionEmpty').insertAdjacentHTML('afterend', table);
      }
    } catch {
      $('dashboardAtRisk').textContent = '—';
      $('dashboardOnSchedule').textContent = '—';
    }

    drawChart([18, 23, 29, 34, 39, 45, 50, 55, 60, 64, 68, Math.min(progress, 72)],
              [16, 20, 27, 31, 35, 41, 45, 49, 54, 58, 63, progress]);
  } catch (err) {
    console.error('Dashboard error:', err);
  }
}


// ═══════════════════════════════════════════════════════════════════════════
// PROJECTS
// ═══════════════════════════════════════════════════════════════════════════
function projectCard(p) {
  const progress = Number(p.overall_progress || 0);
  const status = (p.status || 'planned').toUpperCase().replace('_', ' ');
  const active = p.id === CURRENT_PROJECT_ID;
  return `<article class="project ${active ? 'selected' : ''}" data-project-id="${escapeHtml(p.id)}">
    <span class="pill ${active ? 'green' : ''}">${escapeHtml(status)}</span>
    <h3>${escapeHtml(p.name)}</h3>
    <p>${escapeHtml(p.location || '—')} · ${escapeHtml(p.project_type || 'Infrastructure')}</p>
    <div class="bar"><i style="width:${Math.max(0, Math.min(100, progress))}%"></i></div>
    <small>${formatDate(p.start_date)} → ${formatDate(p.finish_date)}</small>
    <strong>${progress.toFixed(1).replace('.0', '')}%</strong>
    <div class="project-actions">
      <button class="secondary select-project" data-id="${escapeHtml(p.id)}">Set Active</button>
      <button class="secondary edit-project" data-id="${escapeHtml(p.id)}">Edit</button>
      <button class="secondary delete-project" data-id="${escapeHtml(p.id)}">Delete</button>
    </div>
  </article>`;
}

async function loadProjects() {
  const grid = $('projectGrid'); if (!grid) return;
  grid.innerHTML = '<article class="project loading"><h3>Loading projects…</h3><p>Fetching from backend.</p></article>';
  try {
    const projects = await apiFetch('/api/projects');
    grid.innerHTML = projects.length ? projects.map(projectCard).join('') :
      '<article class="project empty"><h3>No projects yet</h3><p>Click + New Project to create one.</p></article>';
    grid.querySelectorAll('.delete-project').forEach(b => b.onclick = () => deleteProject(b.dataset.id));
    grid.querySelectorAll('.edit-project').forEach(b => b.onclick = () => editProject(b.dataset.id));
    grid.querySelectorAll('.select-project').forEach(b => b.onclick = () => {
      CURRENT_PROJECT_ID = b.dataset.id;
      localStorage.setItem('projectbridge_project', CURRENT_PROJECT_ID);
      toast('Active project updated', 'ok');
      loadProjects();
      updateProjectSelectors();
    });
    updateProjectSelectors(projects);
  } catch (e) {
    grid.innerHTML = `<article class="project empty"><h3>Could not load projects</h3><p>${escapeHtml(e.message)}</p></article>`;
  }
}

function updateProjectSelectors(projects) {
  ['scheduleProject', 'currentProject', 'reportProject'].forEach(id => {
    const sel = $(id); if (!sel) return;
    if (!projects) return;
    sel.innerHTML = '<option value="">Select project…</option>' +
      projects.map(p => `<option value="${escapeHtml(p.id)}" ${p.id === CURRENT_PROJECT_ID ? 'selected' : ''}>${escapeHtml(p.name)}</option>`).join('');
    if (id === 'reportProject') setReportUploadState();
    if (id === 'scheduleProject') setScheduleUploadState();
  });
}

function openProjectModal() { $('projectModal').classList.add('open'); $('projectName').focus(); }
function closeProjectModal() { $('projectModal').classList.remove('open'); $('projectForm').reset(); $('projectProgress').value = '0'; }
$('newProject').onclick = openProjectModal;
$('closeProject').onclick = closeProjectModal;
$('cancelProject').onclick = closeProjectModal;
$('projectModal').onclick = e => { if (e.target.id === 'projectModal') closeProjectModal(); };
$('projectForm').onsubmit = async e => {
  e.preventDefault();
  const payload = {
    name: $('projectName').value.trim(), location: $('projectLocation').value.trim(),
    project_type: $('projectType').value.trim(), start_date: $('projectStart').value || null,
    finish_date: $('projectFinish').value || null, overall_progress: Number($('projectProgress').value || 0),
    status: $('projectStatus').value
  };
  try {
    const created = await apiFetch('/api/projects', { method: 'POST', body: JSON.stringify(payload) });
    CURRENT_PROJECT_ID = created.id || '';
    localStorage.setItem('projectbridge_project', CURRENT_PROJECT_ID);
    closeProjectModal(); toast('Project created', 'ok'); loadProjects();
  } catch (err) { toast(err.message, 'error'); }
};
async function deleteProject(id) {
  if (!confirm('Delete this project?')) return;
  try { await apiFetch('/api/projects/' + encodeURIComponent(id), { method: 'DELETE' }); toast('Project deleted'); loadProjects(); }
  catch (e) { toast(e.message, 'error'); }
}
async function editProject(id) {
  try {
    const p = await apiFetch('/api/projects/' + encodeURIComponent(id));
    const name = prompt('Project name', p.name); if (name === null) return;
    const progress = prompt('Overall progress (0-100)', p.overall_progress); if (progress === null) return;
    await apiFetch('/api/projects/' + encodeURIComponent(id), { method: 'PATCH', body: JSON.stringify({ name: name.trim(), overall_progress: Number(progress) }) });
    toast('Project updated', 'ok'); loadProjects();
  } catch (e) { toast(e.message, 'error'); }
}


// ═══════════════════════════════════════════════════════════════════════════
// SCHEDULE IMPORT
// ═══════════════════════════════════════════════════════════════════════════
let scheduleProjectsCache = [];

function setScheduleUploadState() {
  const file = $('scheduleFile')?.files?.[0];
  const projectId = $('scheduleProject')?.value;
  if ($('scheduleUpload')) $('scheduleUpload').disabled = !(file && projectId);
}

async function loadScheduleProjects() {
  const select = $('scheduleProject'); if (!select) return;
  try {
    scheduleProjectsCache = await apiFetch('/api/projects');
    if (!scheduleProjectsCache.length) {
      select.innerHTML = '<option value="">Create a project first</option>';
      select.disabled = true; return;
    }
    select.disabled = false;
    select.innerHTML = '<option value="">Select project…</option>' +
      scheduleProjectsCache.map(p => `<option value="${escapeHtml(p.id)}" ${p.id === CURRENT_PROJECT_ID ? 'selected' : ''}>${escapeHtml(p.name)}</option>`).join('');
  } catch { select.innerHTML = '<option value="">Backend unavailable</option>'; }
  setScheduleUploadState();
}

function setupScheduleImport() {
  const fileInput = $('scheduleFile'), browse = $('scheduleBrowse'), drop = $('scheduleDrop');
  if (!fileInput || !browse || !drop) return;
  browse.onclick = () => fileInput.click();
  fileInput.onchange = () => { const f = fileInput.files[0]; if (f) { $('scheduleName').textContent = `Selected: ${f.name}`; toast('Schedule selected'); } setScheduleUploadState(); };
  drop.ondragover = e => { e.preventDefault(); drop.classList.add('dragover'); };
  drop.ondragleave = () => drop.classList.remove('dragover');
  drop.ondrop = e => {
    e.preventDefault(); drop.classList.remove('dragover');
    const f = e.dataTransfer.files[0]; if (!f) return;
    if (!/\.(csv|xlsx|xls)$/i.test(f.name)) { toast('Use CSV, XLSX or XLS'); return; }
    const dt = new DataTransfer(); dt.items.add(f); fileInput.files = dt.files;
    $('scheduleName').textContent = `Selected: ${f.name}`; setScheduleUploadState();
  };
  $('scheduleProject').onchange = setScheduleUploadState;
  $('scheduleUpload').onclick = importSchedule;
  $('loadActivities').onclick = loadImportedActivities;
}

async function importSchedule() {
  const projectId = $('scheduleProject').value, file = $('scheduleFile').files[0];
  if (!projectId || !file) return;
  const btn = $('scheduleUpload'); btn.disabled = true; btn.textContent = 'Importing…';
  try {
    const form = new FormData(); form.append('file', file);
    const res = await fetch(API + `/api/projects/${encodeURIComponent(projectId)}/schedule/import`, { method: 'POST', body: form });
    if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || `Import failed (${res.status})`); }
    const result = await res.json();
    $('scheduleResult').style.display = 'block';
    $('scheduleResult').innerHTML = `<div class="head"><div><h3>Import Complete</h3><p>${escapeHtml(result.filename)}</p></div></div>
      <div class="import-summary">
        <div><strong>${result.imported}</strong><small>Imported</small></div>
        <div><strong>${result.rows_read}</strong><small>Rows Read</small></div>
        <div><strong>${result.skipped}</strong><small>Skipped</small></div>
      </div>
      ${result.errors?.length ? `<p class="import-errors"><b>Parser notes:</b><br>${result.errors.map(escapeHtml).join('<br>')}</p>` : ''}`;
    toast(`${result.imported} activities imported`, 'ok');
    await loadImportedActivities();
  } catch (e) {
    $('scheduleResult').style.display = 'block';
    $('scheduleResult').innerHTML = `<div class="notice"><b>Import failed</b><span>${escapeHtml(e.message)}</span></div>`;
    toast(e.message, 'error');
  } finally { btn.textContent = 'Import Schedule'; setScheduleUploadState(); }
}

async function loadImportedActivities() {
  const projectId = $('scheduleProject').value;
  if (!projectId) { toast('Select a project first'); return; }
  const box = $('scheduleActivities'); box.style.display = 'block'; box.innerHTML = '<h3>Imported Activities</h3><p>Loading…</p>';
  try {
    const activities = await apiFetch(`/api/projects/${encodeURIComponent(projectId)}/schedule/activities`);
    if (!activities.length) { box.innerHTML = '<h3>Imported Activities</h3><p>No activities imported yet.</p>'; return; }
    box.innerHTML = `<div class="head"><div><h3>Imported Activities</h3><p>${activities.length} baseline activities</p></div></div>
      <div class="tablewrap"><table><thead><tr><th>Activity ID</th><th>Activity</th><th>WBS</th><th>Discipline</th><th>Planned Start</th><th>Planned Finish</th><th>Planned %</th></tr></thead><tbody>
        ${activities.map(a => `<tr>
          <td><b>${escapeHtml(a.activity_id)}</b></td><td>${escapeHtml(a.activity_name)}</td>
          <td>${escapeHtml(a.wbs_code || '—')}</td><td>${escapeHtml(a.discipline || '—')}</td>
          <td>${formatDate(a.planned_start)}</td><td>${formatDate(a.planned_end)}</td>
          <td>${Number(a.planned_progress || 0).toFixed(1).replace('.0', '')}%</td>
        </tr>`).join('')}
      </tbody></table></div>`;
  } catch (e) { box.innerHTML = `<div class="notice"><b>Could not load activities</b><span>${escapeHtml(e.message)}</span></div>`; }
}


// ═══════════════════════════════════════════════════════════════════════════
// PROGRESS REPORTS — Upload DPR → LLM extraction → match → save to progress_events
// ═══════════════════════════════════════════════════════════════════════════
function setReportUploadState() {
  const file = $('reportFile')?.files?.[0];
  const projectId = $('reportProject')?.value;
  const btn = $('reportUploadBtn');
  if (btn) btn.disabled = !(file && projectId);
}

function loadReportsPage() {
  // populate project selector
  apiFetch('/api/projects').then(projects => {
    const sel = $('reportProject'); if (!sel) return;
    sel.innerHTML = '<option value="">Select project…</option>' +
      projects.map(p => `<option value="${escapeHtml(p.id)}" ${p.id === CURRENT_PROJECT_ID ? 'selected' : ''}>${escapeHtml(p.name)}</option>`).join('');
    setReportUploadState();
  }).catch(() => {});
}

function setupReportUpload() {
  const fileInput = $('reportFile'), browse = $('reportBrowse'), drop = $('reportDrop');
  if (!fileInput || !browse || !drop) return;
  browse.onclick = () => fileInput.click();
  fileInput.onchange = () => {
    const f = fileInput.files[0];
    if (f) { $('reportName').textContent = `Selected: ${f.name}`; toast('Report selected'); }
    setReportUploadState();
  };
  drop.ondragover = e => { e.preventDefault(); drop.classList.add('dragover'); };
  drop.ondragleave = () => drop.classList.remove('dragover');
  drop.ondrop = e => {
    e.preventDefault(); drop.classList.remove('dragover');
    const f = e.dataTransfer.files[0]; if (!f) return;
    if (!/\.(pdf|docx|txt)$/i.test(f.name)) { toast('Use PDF, DOCX or TXT'); return; }
    const dt = new DataTransfer(); dt.items.add(f); fileInput.files = dt.files;
    $('reportName').textContent = `Selected: ${f.name}`; setReportUploadState();
  };
  if ($('reportProject')) $('reportProject').onchange = setReportUploadState;
  const btn = $('reportUploadBtn'); if (btn) btn.onclick = uploadReport;
}

async function uploadReport() {
  const projectId = $('reportProject')?.value, file = $('reportFile')?.files?.[0];
  if (!projectId || !file) { toast('Select a project and a report file first'); return; }
  const btn = $('reportUploadBtn');
  btn.disabled = true; btn.textContent = 'Extracting with AI…';
  const result_box = $('reportResult');
  if (result_box) { result_box.style.display = 'block'; result_box.innerHTML = '<p>⏳ Sending to Groq LLM for Oil & Gas activity extraction… This may take 10–20 seconds.</p>'; }

  try {
    const form = new FormData();
    form.append('file', file);
    form.append('project_id', projectId);
    form.append('uploaded_by', 'site_engineer');

    const res = await fetch(API + '/api/v1/ingest/upload', { method: 'POST', body: form });
    if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || `Upload failed (${res.status})`); }
    const data = await res.json();

    const activities = data.activities || [];
    toast(`Extracted ${activities.length} activities`, 'ok');

    if (result_box) {
      result_box.innerHTML = `
        <div class="head"><div><h3>Extraction Complete</h3><p>${escapeHtml(file.name)}</p></div></div>
        <div class="import-summary">
          <div><strong>${activities.length}</strong><small>Events Extracted</small></div>
          <div><strong>${data.total_matched ?? 0}</strong><small>Auto-Matched</small></div>
          <div><strong>${data.total_flagged ?? 0}</strong><small>Need Review</small></div>
        </div>
        ${data.report_summary ? `<p style="margin-top:12px;color:#566677;font-size:12px"><b>AI Summary:</b> ${escapeHtml(data.report_summary)}</p>` : ''}
        <div class="tablewrap" style="margin-top:16px">
        <table><thead><tr><th>Extracted Activity</th><th>Discipline</th><th>Status</th><th>Confidence</th><th>Risk</th><th>Predicted Days</th></tr></thead><tbody>
          ${activities.map(a => `<tr>
            <td>${escapeHtml(a.extracted_activity || '—')}</td>
            <td>${escapeHtml(a.discipline || '—')}</td>
            <td>${statusBadge(a.status)}</td>
            <td>${((a.confidence || 0) * 100).toFixed(0)}%</td>
            <td>${riskBadge(a.prediction?.risk_level)}</td>
            <td>${a.prediction?.predicted_actual_duration_days?.toFixed(1) ?? '—'}</td>
          </tr>`).join('')}
        </tbody></table></div>
        <div class="notice" style="margin-top:12px"><b>Next step:</b><span>Go to <a href="#" onclick="go('matching');return false">AI Matching</a> to confirm or reassign these matches.</span></div>
      `;
    }
  } catch (e) {
    toast(e.message, 'error');
    if (result_box) result_box.innerHTML = `<div class="notice"><b>Extraction failed</b><span>${escapeHtml(e.message)}</span></div>`;
  } finally {
    btn.disabled = false; btn.textContent = 'Upload & Extract';
  }
}


// ═══════════════════════════════════════════════════════════════════════════
// SUPERVISOR CHAT
// ═══════════════════════════════════════════════════════════════════════════
let chatHistory = [];
let chatProjectId = CURRENT_PROJECT_ID;

function loadChat() {
  apiFetch('/api/projects').then(projects => {
    const sel = $('chatProject'); if (!sel) return;
    sel.innerHTML = '<option value="">Select project…</option>' +
      projects.map(p => `<option value="${escapeHtml(p.id)}" ${p.id === CURRENT_PROJECT_ID ? 'selected' : ''}>${escapeHtml(p.name)}</option>`).join('');
  }).catch(() => {});
}

function setupChat() {
  const chatSend = $('chatSend'), chatInput = $('chatInput');
  if (!chatSend || !chatInput) return;
  chatSend.onclick = sendChat;
  chatInput.onkeydown = e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); } };
}

function appendChatMessage(role, text) {
  const box = $('chatMessages'); if (!box) return;
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  div.innerHTML = `<span>${escapeHtml(text)}</span>`;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

async function sendChat() {
  const input = $('chatInput'); if (!input) return;
  const msg = input.value.trim(); if (!msg) return;
  input.value = '';
  const pid = $('chatProject')?.value || CURRENT_PROJECT_ID;

  appendChatMessage('user', msg);
  chatHistory.push({ role: 'user', content: msg });

  try {
    const res = await apiFetch('/api/v1/ingest/chat', {
      method: 'POST',
      body: JSON.stringify({ message: msg, history: chatHistory, project_id: pid, supervisor: 'site_engineer' })
    });
    appendChatMessage('assistant', res.reply);
    chatHistory.push({ role: 'assistant', content: res.reply });

    if (res.activity_log) {
      toast('Activity logged from chat!', 'ok');
      const logDiv = $('chatLog'); if (logDiv) {
        logDiv.style.display = 'block';
        logDiv.innerHTML = `<b>Activity Captured:</b><br>
          <b>Activity:</b> ${escapeHtml(res.activity_log.extracted_activity || '—')}<br>
          <b>Discipline:</b> ${escapeHtml(res.activity_log.discipline || '—')}<br>
          <b>Start:</b> ${escapeHtml(res.activity_log.actual_start || '—')}<br>
          <b>End:</b> ${escapeHtml(res.activity_log.actual_end || 'Ongoing')}<br>
          <b>Event ID:</b> ${escapeHtml(res.event_id || '—')}`;
      }
    }
  } catch (e) {
    appendChatMessage('assistant', `Error: ${e.message}`);
  }
}


// ═══════════════════════════════════════════════════════════════════════════
// AI MATCHING — list progress_events, approve/reject/reassign
// ═══════════════════════════════════════════════════════════════════════════
async function loadMatching() {
  const box = document.querySelector('#matching .card.matches');
  if (!box) return;
  if (!CURRENT_PROJECT_ID) {
    box.innerHTML = '<p class="empty">No active project. Go to Settings and select a project.</p>'; return;
  }
  box.innerHTML = '<p class="empty">Loading AI matches…</p>';
  try {
    const res = await apiFetch(`/api/v1/activities/?project_id=${encodeURIComponent(CURRENT_PROJECT_ID)}&limit=50`);
    const events = res.activities || [];
    if (!events.length) { box.innerHTML = '<p class="empty">No progress events yet. Upload a DPR report first.</p>'; return; }

    box.innerHTML = events.map(e => `
      <div class="match" data-event-id="${escapeHtml(e.event_id || '')}">
        <div>
          <small>EXTRACTED FROM REPORT</small>
          <p>${escapeHtml(e.extracted_activity || e.filename || '—')}</p>
          <small style="margin-top:6px;display:block">${escapeHtml(e.discipline || '—')} · ${formatDate(e.actual_start)}</small>
          ${statusBadge(e.status)}
        </div>
        <b>→</b>
        <div class="target">
          <small>MATCHED BASELINE ACTIVITY</small>
          <strong>${escapeHtml(e.matched_description || e.matched_activity_id || 'No match found')}</strong>
          <span>Confidence: <b>${((e.confidence || 0) * 100).toFixed(0)}%</b></span><br>
          <span>Risk: ${riskBadge(e.prediction?.risk_level)}</span>
          ${e.prediction ? `<div style="margin-top:6px;font-size:10px;color:#566677">Predicted: ${e.prediction.predicted_actual_duration_days?.toFixed(1)}d (+${e.prediction.variance_days?.toFixed(1)}d)</div>` : ''}
        </div>
        <div style="display:flex;flex-direction:column;gap:6px">
          <button class="primary approve-match" data-id="${escapeHtml(e.event_id || '')}" style="font-size:11px;padding:7px 10px">Confirm</button>
          <button class="secondary reject-match" data-id="${escapeHtml(e.event_id || '')}" style="font-size:11px;padding:7px 10px">Reject</button>
        </div>
      </div>
    `).join('');

    box.querySelectorAll('.approve-match').forEach(b => b.onclick = () => reviewEvent(b.dataset.id, 'confirm', b));
    box.querySelectorAll('.reject-match').forEach(b => b.onclick = () => reviewEvent(b.dataset.id, 'reject', b));
  } catch (e) {
    box.innerHTML = `<p class="empty">Error: ${escapeHtml(e.message)}</p>`;
  }
}

async function reviewEvent(eventId, action, btn) {
  if (!eventId) { toast('Invalid event ID'); return; }
  btn.disabled = true; btn.textContent = action === 'confirm' ? 'Confirming…' : 'Rejecting…';
  try {
    await apiFetch(`/api/v1/activities/${encodeURIComponent(eventId)}/review`, {
      method: 'PUT',
      body: JSON.stringify({ action, reviewed_by: 'site_planner', notes: `${action} via frontend` })
    });
    toast(action === 'confirm' ? 'Match confirmed and audited' : 'Match rejected', 'ok');
    // Reload after short delay
    setTimeout(loadMatching, 600);
  } catch (e) {
    toast(e.message, 'error'); btn.disabled = false; btn.textContent = action === 'confirm' ? 'Confirm' : 'Reject';
  }
}

$('refresh').onclick = () => loadMatching();


// ═══════════════════════════════════════════════════════════════════════════
// PROGRESS TRACKING — compare baseline vs actual
// ═══════════════════════════════════════════════════════════════════════════
async function loadTracking() {
  const wrap = document.querySelector('#tracking .tablewrap');
  if (!wrap) return;
  if (!CURRENT_PROJECT_ID) {
    wrap.innerHTML = '<p class="empty">No active project. Go to Settings and select a project.</p>'; return;
  }
  wrap.innerHTML = '<p class="empty">Loading…</p>';
  try {
    const [eventsRes, disciplineRes] = await Promise.all([
      apiFetch(`/api/v1/activities/?project_id=${encodeURIComponent(CURRENT_PROJECT_ID)}&limit=200`),
      apiFetch(`/api/v1/analytics/discipline-summary?project_id=${encodeURIComponent(CURRENT_PROJECT_ID)}`).catch(() => ({ disciplines: [] }))
    ]);
    const events = eventsRes.activities || [];
    if (!events.length) { wrap.innerHTML = '<p class="empty">No execution data yet. Upload a DPR report to start tracking.</p>'; return; }

    wrap.innerHTML = `<table><thead><tr>
      <th>Extracted Activity</th><th>Discipline</th><th>Status</th>
      <th>Start</th><th>End</th><th>Risk</th><th>Predicted Duration</th><th>Variance</th>
    </tr></thead><tbody>
      ${events.map(e => {
        const variance = e.prediction?.variance_days || 0;
        return `<tr>
          <td>${escapeHtml(e.extracted_activity || '—')}</td>
          <td>${escapeHtml(e.discipline || '—')}</td>
          <td>${statusBadge(e.status)}</td>
          <td>${formatDate(e.actual_start)}</td>
          <td>${formatDate(e.actual_end) || '<em>Ongoing</em>'}</td>
          <td>${riskBadge(e.prediction?.risk_level)}</td>
          <td>${e.prediction?.predicted_actual_duration_days?.toFixed(1) ?? '—'}d</td>
          <td class="${variance > 0 ? 'red' : 'good'}">${variance > 0 ? '+' : ''}${variance.toFixed(1)}d</td>
        </tr>`;
      }).join('')}
    </tbody></table>`;

    // removed trackingEmpty line because it is overwritten by innerHTML
  } catch (e) {
    wrap.innerHTML = `<p class="empty">Error: ${escapeHtml(e.message)}</p>`;
  }
}

$('search').oninput = e => {
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('#tracking .tablewrap tbody tr').forEach(r =>
    r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none');
};


// ═══════════════════════════════════════════════════════════════════════════
// SETTINGS
// ═══════════════════════════════════════════════════════════════════════════
if ($('apiUrl')) $('apiUrl').value = API;
$('save').onclick = async () => {
  API = $('apiUrl').value.trim().replace(/\/$/, '');
  const pid = $('currentProject')?.value;
  if (pid) { CURRENT_PROJECT_ID = pid; localStorage.setItem('projectbridge_project', CURRENT_PROJECT_ID); }
  localStorage.setItem('projectbridge_api', API);
  $('saved').textContent = 'Saved: ' + API;
  toast('Settings saved', 'ok');
  await checkBackend();
};

// Populate currentProject selector in settings
apiFetch('/api/projects').then(projects => {
  const sel = $('currentProject'); if (!sel) return;
  sel.innerHTML = '<option value="">No project selected</option>' +
    projects.map(p => `<option value="${escapeHtml(p.id)}" ${p.id === CURRENT_PROJECT_ID ? 'selected' : ''}>${escapeHtml(p.name)}</option>`).join('');
}).catch(() => {});


// ═══════════════════════════════════════════════════════════════════════════
// NAVIGATION OVERRIDE — override go() to trigger page loaders
// ═══════════════════════════════════════════════════════════════════════════
const originalGo = go;
go = function (page) { originalGo(page); };

// ═══════════════════════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════════════════════
setupScheduleImport();
setupReportUpload();
setupChat();
checkBackend();
loadDashboard();
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => { loadProjects(); loadScheduleProjects(); });
} else {
  loadProjects(); loadScheduleProjects();
}
