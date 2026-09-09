const titles={dashboard:'Project Dashboard',projects:'Projects',schedule:'Schedule Import',reports:'Progress Reports',matching:'AI Activity Matching',tracking:'Progress Tracking',settings:'Settings'};
const $=id=>document.getElementById(id); let API=localStorage.getItem('projectbridge_api')||'http://localhost:8000';
function toast(s){const t=$('toast');t.textContent=s;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2400)}
function go(page){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));$(page)?.classList.add('active');document.querySelectorAll('.nav').forEach(x=>x.classList.toggle('active',x.dataset.page===page));$('pageTitle').textContent=titles[page]||'Project Dashboard';$('sidebar').classList.remove('open');if(page==='dashboard')loadDashboard()}
document.querySelectorAll('[data-page]').forEach(x=>x.addEventListener('click',()=>go(x.dataset.page)));
$('menuBtn').onclick=()=>$('sidebar').classList.toggle('open');
$('today').textContent=new Intl.DateTimeFormat('en-IN',{day:'2-digit',month:'short',year:'numeric'}).format(new Date());
function fileSetup(file,browse,name,drop){const f=$(file),d=$(drop);$(browse).onclick=()=>f.click();f.onchange=()=>{if(f.files[0]){$(name).textContent='Selected: '+f.files[0].name;toast('File selected')}};d.ondragover=e=>{e.preventDefault()};d.ondrop=e=>{e.preventDefault();if(e.dataTransfer.files[0]){$(name).textContent='Selected: '+e.dataTransfer.files[0].name;toast('File selected')}}}
fileSetup('reportFile','reportBrowse','reportName','reportDrop');
document.querySelectorAll('.approve').forEach(b=>b.onclick=()=>{b.textContent='Approved';b.disabled=true;toast('Match approved — ready for progress commit')});
document.querySelectorAll('.review').forEach(b=>b.onclick=()=>toast('Sent to supervisor review'));
$('refresh').onclick=()=>toast('Match suggestions refreshed (demo data)');
$('newProject').onclick=()=>toast('Project creation will connect to POST /api/projects');
$('search').oninput=e=>{const q=e.target.value.toLowerCase();document.querySelectorAll('#activityTable tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(q)?'':'none')};
$('save').onclick=()=>{API=$('apiUrl').value.trim().replace(/\/$/,'');localStorage.setItem('projectbridge_api',API);$('saved').textContent='Saved: '+API;toast('Settings saved');checkBackend()};
async function checkBackend(){try{const r=await fetch(API+'/api/health',{signal:AbortSignal.timeout(1800)});if(!r.ok)throw 0;$('apiStatus').textContent='Connected';$('apiStatus').style.color='#63d49b'}catch{$('apiStatus').textContent='Offline';$('apiStatus').style.color='#e0a020'}}
function drawChart(){const c=$('chart');if(!c)return;const w=c.clientWidth,h=c.clientHeight,d=devicePixelRatio||1;c.width=w*d;c.height=h*d;const x=c.getContext('2d');x.scale(d,d);const planned=[18,23,29,34,39,45,50,55,60,64,68,72],actual=[16,20,27,31,35,41,45,49,54,58,63,67],p={l:30,r:8,t:12,b:15},cw=w-p.l-p.r,ch=h-p.t-p.b;x.font='10px system-ui';x.fillStyle='#7b8694';x.strokeStyle='#edf0f3';for(let i=0;i<=4;i++){let y=p.t+ch*i/4;x.beginPath();x.moveTo(p.l,y);x.lineTo(w-p.r,y);x.stroke();x.fillText((100-i*25)+'%',2,y+3)}function line(a,dot){x.beginPath();a.forEach((v,i)=>{let X=p.l+cw*i/(a.length-1),Y=p.t+ch*(1-v/100);i?x.lineTo(X,Y):x.moveTo(X,Y)});x.strokeStyle=dot?'#1769e0':'#a7b1bc';x.lineWidth=2;x.stroke()}line(planned,false);line(actual,true)}
window.onresize=drawChart;
loadDashboard();
checkBackend();
// ---------------- Milestone 2: Projects + Firestore CRUD ----------------
function formatDate(v){if(!v)return '—';const d=new Date(v);return Number.isNaN(d.getTime())?v:d.toLocaleDateString('en-IN',{day:'2-digit',month:'short',year:'numeric'})}
function escapeHtml(v){return String(v??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}
function projectCard(p){
  const progress=Number(p.overall_progress||0);
  const status=(p.status||'planned').toUpperCase().replace('_',' ');
  const active=status==='ACTIVE';
  return `<article class="project ${active?'selected':''}" data-project-id="${escapeHtml(p.id)}">
    <span class="pill ${active?'green':''}">${escapeHtml(status)}</span>
    <h3>${escapeHtml(p.name)}</h3>
    <p>${escapeHtml(p.location||'—')} · ${escapeHtml(p.project_type||'Infrastructure')}</p>
    <div class="bar"><i style="width:${Math.max(0,Math.min(100,progress))}%"></i></div>
    <small>${formatDate(p.start_date)} → ${formatDate(p.finish_date)}</small>
    <strong>${progress.toFixed(1).replace('.0','')}%</strong>
    <div class="project-actions"><button class="secondary edit-project" data-id="${escapeHtml(p.id)}">Edit</button><button class="secondary delete-project" data-id="${escapeHtml(p.id)}">Delete</button></div>
  </article>`;
}
async function apiFetch(path,options={}){
  const headers={'Content-Type':'application/json',...(options.headers||{})};
  const r=await fetch(API+path,{...options,headers});
  if(!r.ok){let msg=`Request failed (${r.status})`;try{const e=await r.json();msg=e.detail||msg}catch{}throw new Error(msg)}
  if(r.status===204)return null;return r.json();
}

async function loadDashboard() {
  try {
    const projects = await apiFetch('/api/projects');

    if (!projects || projects.length === 0) {
      $('dashboardProjectName').textContent = 'No project selected';
      $('dashboardProjectDescription').textContent =
        'Project information will appear here when a project is available.';

      $('dashboardProgress').textContent = '—';
      $('dashboardProgressNote').textContent = 'No project data';
      $('dashboardProgressBar').style.width = '0%';

      $('dashboardActivities').textContent = '—';
      $('dashboardOnSchedule').textContent = '—';
      $('dashboardAtRisk').textContent = '—';

      return;
    }

    // Use the first project for now
    const project = projects[0];

    // -----------------------------
    // PROJECT INFORMATION
    // -----------------------------

    const progress = Number(project.overall_progress || 0);

    $('dashboardProjectName').textContent =
      project.name || 'Unnamed Project';

    $('dashboardProjectDescription').textContent =
      `${project.location || 'Location not available'} · ${
        project.project_type || 'Infrastructure'
      }`;

    // -----------------------------
    // OVERALL PROGRESS
    // -----------------------------

    $('dashboardProgress').textContent =
      `${progress.toFixed(1).replace('.0', '')}%`;

    $('dashboardProgressNote').textContent =
      `Current progress of ${project.name || 'project'}`;

    $('dashboardProgressBar').style.width =
      `${Math.max(0, Math.min(100, progress))}%`;

    // -----------------------------
    // LOAD ACTIVITIES
    // -----------------------------

    try {
      const activities = await apiFetch(
        `/api/projects/${encodeURIComponent(project.id)}/schedule/activities`
      );

      console.log('Dashboard activities:', activities);

      const totalActivities = activities.length;

      $('dashboardActivities').textContent =
        totalActivities;

      $('dashboardActivitiesNote').textContent =
        totalActivities === 0
          ? 'No schedule imported'
          : `${totalActivities} imported activities`;

      // --------------------------------
      // BASIC ACTIVITY STATUS CALCULATION
      // --------------------------------

      if (!totalActivities) {
        $('dashboardOnSchedule').textContent = '—';
        $('dashboardAtRisk').textContent = '—';

        $('dashboardOnScheduleNote').textContent =
          'No activity data';

        $('dashboardAtRiskNote').textContent =
          'No activity data';

        $('disciplineProgress').innerHTML =
          '<p class="empty">No activity data available yet.</p>';

        $('attentionEmpty').textContent =
          'No execution variance data available yet.';

        return;
      }

      /*
       * For now we use planned_progress.
       * Later, when actual progress is available from
       * Progress Reports, this calculation should compare
       * planned vs actual progress.
       */

      let onSchedule = 0;
      let atRisk = 0;

      activities.forEach(activity => {
        const planned = Number(activity.planned_progress || 0);
        const actual = Number(
          activity.actual_progress ?? planned
        );

        const variance = actual - planned;

        if (variance >= -5) {
          onSchedule++;
        } else {
          atRisk++;
        }
      });

      $('dashboardOnSchedule').textContent =
        onSchedule;

      $('dashboardAtRisk').textContent =
        atRisk;

      $('dashboardOnScheduleNote').textContent =
        `${Math.round((onSchedule / totalActivities) * 100)}% of activities`;

      $('dashboardAtRiskNote').textContent =
        `${Math.round((atRisk / totalActivities) * 100)}% of activities`;

      // -----------------------------
      // DISCIPLINE PROGRESS
      // -----------------------------

      const disciplines = {};

      activities.forEach(activity => {
        const discipline =
          activity.discipline || 'Other';

        if (!disciplines[discipline]) {
          disciplines[discipline] = {
            total: 0,
            progress: 0
          };
        }

        disciplines[discipline].total++;

        disciplines[discipline].progress +=
          Number(activity.planned_progress || 0);
      });

      const disciplineBox = $('disciplineProgress');

      disciplineBox.innerHTML =
        Object.entries(disciplines)
          .map(([discipline, data]) => {
            const avg =
              data.progress / data.total;

            return `
              <div class="discipline-row">
                <div>
                  <b>${escapeHtml(discipline)}</b>
                  <small>${data.total} activities</small>
                </div>

                <strong>
                  ${avg.toFixed(1).replace('.0', '')}%
                </strong>

                <div class="bar">
                  <i style="width:${Math.max(
                    0,
                    Math.min(100, avg)
                  )}%"></i>
                </div>
              </div>
            `;
          })
          .join('');

    } catch (error) {
      console.log(
        'No schedule activities imported yet.',
        error
      );

      $('dashboardActivities').textContent = '—';
      $('dashboardActivitiesNote').textContent =
        'No schedule imported';

      $('dashboardOnSchedule').textContent = '—';
      $('dashboardAtRisk').textContent = '—';

      $('dashboardOnScheduleNote').textContent =
        'No activity data';

      $('dashboardAtRiskNote').textContent =
        'No activity data';
    }

  } catch (error) {
    console.error(
      'Dashboard loading failed:',
      error
    );
  }
}

async function loadProjects(){
  const grid=$('projectGrid'); if(!grid)return;
  grid.innerHTML='<article class="project loading"><h3>Loading projects…</h3><p>Fetching projects from Firestore through FastAPI.</p></article>';
  try{
    const projects=await apiFetch('/api/projects');
    grid.innerHTML=projects.length?projects.map(projectCard).join(''):'<article class="project empty"><h3>No projects yet</h3><p>Create your first project to add it to Firestore.</p></article>';
    grid.querySelectorAll('.delete-project').forEach(b=>b.onclick=()=>deleteProject(b.dataset.id));
    grid.querySelectorAll('.edit-project').forEach(b=>b.onclick=()=>editProject(b.dataset.id));
  }catch(e){grid.innerHTML=`<article class="project empty"><h3>Could not load projects</h3><p>${escapeHtml(e.message)}. Check Firestore credentials and the backend.</p></article>`;}
}
function openProjectModal(){ $('projectModal').classList.add('open'); $('projectName').focus(); }
function closeProjectModal(){ $('projectModal').classList.remove('open'); $('projectForm').reset(); $('projectProgress').value='0'; }
$('newProject').onclick=openProjectModal;
$('closeProject').onclick=closeProjectModal;$('cancelProject').onclick=closeProjectModal;
$('projectModal').onclick=e=>{if(e.target.id==='projectModal')closeProjectModal()};
$('projectForm').onsubmit=async e=>{
  e.preventDefault();
  const payload={name:$('projectName').value.trim(),location:$('projectLocation').value.trim(),project_type:$('projectType').value.trim(),start_date:$('projectStart').value||null,finish_date:$('projectFinish').value||null,overall_progress:Number($('projectProgress').value||0),status:$('projectStatus').value};
  try{await apiFetch('/api/projects',{method:'POST',body:JSON.stringify(payload)});closeProjectModal();toast('Project created in Firestore');loadProjects();}
  catch(err){toast(err.message)}
};
async function deleteProject(id){if(!confirm('Delete this project from Firestore?'))return;try{await apiFetch('/api/projects/'+encodeURIComponent(id),{method:'DELETE'});toast('Project deleted');loadProjects()}catch(e){toast(e.message)}}
async function editProject(id){
  try{
    const p=await apiFetch('/api/projects/'+encodeURIComponent(id));
    const name=prompt('Project name',p.name); if(name===null)return;
    const progress=prompt('Overall progress (0-100)',p.overall_progress); if(progress===null)return;
    await apiFetch('/api/projects/'+encodeURIComponent(id),{method:'PATCH',body:JSON.stringify({name:name.trim(),overall_progress:Number(progress)})});
    toast('Project updated');loadProjects();
  }catch(e){toast(e.message)}
}

// Replace the Milestone 1 demo handler with the real Projects loader.
$('newProject').onclick=openProjectModal;
const originalGo=go;
go=function(page){originalGo(page);if(page==='projects')loadProjects();if(page==='schedule')loadScheduleProjects()};
setupScheduleImport();
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{loadProjects();loadScheduleProjects()});else {loadProjects();loadScheduleProjects();}


// ---------------- Milestone 3: Schedule Import ----------------
let scheduleProjectsCache = [];

function setScheduleUploadState() {
  const file = $('scheduleFile')?.files?.[0];
  const projectId = $('scheduleProject')?.value;
  if ($('scheduleUpload')) $('scheduleUpload').disabled = !(file && projectId);
}

async function loadScheduleProjects() {
  const select = $('scheduleProject');
  if (!select) return;
  try {
    scheduleProjectsCache = await apiFetch('/api/projects');
    if (!scheduleProjectsCache.length) {
      select.innerHTML = '<option value="">Create a project first</option>';
      select.disabled = true;
      return;
    }
    select.disabled = false;
    select.innerHTML = '<option value="">Select project…</option>' +
      scheduleProjectsCache.map(p =>
        `<option value="${escapeHtml(p.id)}">${escapeHtml(p.name)}</option>`
      ).join('');
  } catch (e) {
    select.innerHTML = '<option value="">Backend unavailable</option>';
  }
  setScheduleUploadState();
}

function setupScheduleImport() {
  const fileInput = $('scheduleFile');
  const browse = $('scheduleBrowse');
  const drop = $('scheduleDrop');
  if (!fileInput || !browse || !drop) return;

  browse.onclick = () => fileInput.click();
  fileInput.onchange = () => {
    const file = fileInput.files[0];
    if (file) {
      $('scheduleName').textContent = `Selected: ${file.name}`;
      toast('Schedule selected');
    }
    setScheduleUploadState();
  };

  drop.ondragover = e => {
    e.preventDefault();
    drop.classList.add('dragover');
  };
  drop.ondragleave = () => drop.classList.remove('dragover');
  drop.ondrop = e => {
    e.preventDefault();
    drop.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (!file) return;
    const allowed = /\.(csv|xlsx|xls)$/i.test(file.name);
    if (!allowed) {
      toast('Use CSV, XLSX or XLS');
      return;
    }
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;
    $('scheduleName').textContent = `Selected: ${file.name}`;
    setScheduleUploadState();
  };

  $('scheduleProject').onchange = setScheduleUploadState;
  $('scheduleUpload').onclick = importSchedule;
  $('loadActivities').onclick = loadImportedActivities;
}

async function importSchedule() {
  const projectId = $('scheduleProject').value;
  const file = $('scheduleFile').files[0];
  if (!projectId || !file) return;

  const button = $('scheduleUpload');
  button.disabled = true;
  button.textContent = 'Importing…';

  try {
    const form = new FormData();
    form.append('file', file);

    const response = await fetch(
      API + `/api/projects/${encodeURIComponent(projectId)}/schedule/import`,
      { method: 'POST', body: form }
    );
    if (!response.ok) {
      let message = `Import failed (${response.status})`;
      try {
        const data = await response.json();
        message = data.detail || message;
      } catch {}
      throw new Error(message);
    }

    const result = await response.json();
    $('scheduleResult').style.display = 'block';
    $('scheduleResult').innerHTML = `
      <div class="head"><div><h3>Import Complete</h3><p>${escapeHtml(result.filename)}</p></div></div>
      <div class="import-summary">
        <div><strong>${result.imported}</strong><small>Imported</small></div>
        <div><strong>${result.rows_read}</strong><small>Rows Read</small></div>
        <div><strong>${result.skipped}</strong><small>Skipped</small></div>
      </div>
      ${result.errors?.length ? `<p class="import-errors"><b>Parser notes:</b><br>${result.errors.map(escapeHtml).join('<br>')}</p>` : ''}
    `;
    toast(`${result.imported} activities imported`);
    await loadImportedActivities();
  } catch (e) {
    $('scheduleResult').style.display = 'block';
    $('scheduleResult').innerHTML = `<div class="notice"><b>Import failed</b><span>${escapeHtml(e.message)}</span></div>`;
    toast(e.message);
  } finally {
    button.textContent = 'Import Schedule';
    setScheduleUploadState();
  }
}

async function loadImportedActivities() {
  const projectId = $('scheduleProject').value;
  if (!projectId) {
    toast('Select a project first');
    return;
  }

  const box = $('scheduleActivities');
  box.style.display = 'block';
  box.innerHTML = '<h3>Imported Activities</h3><p>Loading…</p>';

  try {
    const activities = await apiFetch(
      `/api/projects/${encodeURIComponent(projectId)}/schedule/activities`
    );

    if (!activities.length) {
      box.innerHTML = '<h3>Imported Activities</h3><p>No activities have been imported for this project yet.</p>';
      return;
    }

    box.innerHTML = `
      <div class="head"><div><h3>Imported Activities</h3><p>${activities.length} activities linked to this project</p></div></div>
      <div class="tablewrap">
        <table>
          <thead><tr>
            <th>Activity ID</th><th>Activity</th><th>WBS</th><th>Discipline</th>
            <th>Planned Start</th><th>Planned Finish</th><th>Planned %</th>
          </tr></thead>
          <tbody>
            ${activities.map(a => `
              <tr>
                <td><b>${escapeHtml(a.activity_id)}</b></td>
                <td>${escapeHtml(a.activity_name)}</td>
                <td>${escapeHtml(a.wbs_code || '—')}</td>
                <td>${escapeHtml(a.discipline || '—')}</td>
                <td>${formatDate(a.planned_start)}</td>
                <td>${formatDate(a.planned_end)}</td>
                <td>${Number(a.planned_progress || 0).toFixed(1).replace('.0','')}%</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  } catch (e) {
    box.innerHTML = `<div class="notice"><b>Could not load activities</b><span>${escapeHtml(e.message)}</span></div>`;
  }
}
