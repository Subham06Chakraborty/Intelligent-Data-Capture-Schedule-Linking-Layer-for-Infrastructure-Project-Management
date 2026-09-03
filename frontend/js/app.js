const titles={dashboard:'Project Dashboard',projects:'Projects',schedule:'Schedule Import',reports:'Progress Reports',matching:'AI Activity Matching',tracking:'Progress Tracking',settings:'Settings'};

const $=id=>document.getElementById(id); let API=localStorage.getItem('projectbridge_api')||'http://localhost:8000';

function toast(s){const t=$('toast');t.textContent=s;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2400)}

function go(page){document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));$(page)?.classList.add('active');document.querySelectorAll('.nav').forEach(x=>x.classList.toggle('active',x.dataset.page===page));$('pageTitle').textContent=titles[page]||'Project Dashboard';$('sidebar').classList.remove('open');if(page==='dashboard')drawChart()}
document.querySelectorAll('[data-page]').forEach(x=>x.addEventListener('click',()=>go(x.dataset.page)));

$('menuBtn').onclick=()=>$('sidebar').classList.toggle('open');

$('today').textContent=new Intl.DateTimeFormat('en-IN',{day:'2-digit',month:'short',year:'numeric'}).format(new Date());

function fileSetup(file,browse,name,drop){const f=$(file),d=$(drop);$(browse).onclick=()=>f.click();f.onchange=()=>{if(f.files[0]){$(name).textContent='Selected: '+f.files[0].name;toast('File selected')}};d.ondragover=e=>{e.preventDefault()};d.ondrop=e=>{e.preventDefault();if(e.dataTransfer.files[0]){$(name).textContent='Selected: '+e.dataTransfer.files[0].name;toast('File selected')}}}
fileSetup('scheduleFile','scheduleBrowse','scheduleName','scheduleDrop');fileSetup('reportFile','reportBrowse','reportName','reportDrop');
document.querySelectorAll('.approve').forEach(b=>b.onclick=()=>{b.textContent='Approved';b.disabled=true;toast('Match approved — ready for progress commit')});
document.querySelectorAll('.review').forEach(b=>b.onclick=()=>toast('Sent to supervisor review'));
$('refresh').onclick=()=>toast('Match suggestions refreshed (demo data)');
$('newProject').onclick=()=>toast('Project creation will connect to POST /api/projects');
$('search').oninput=e=>{const q=e.target.value.toLowerCase();document.querySelectorAll('#activityTable tbody tr').forEach(r=>r.style.display=r.textContent.toLowerCase().includes(q)?'':'none')};
$('save').onclick=()=>{API=$('apiUrl').value.trim().replace(/\/$/,'');localStorage.setItem('projectbridge_api',API);$('saved').textContent='Saved: '+API;toast('Settings saved');checkBackend()};
async function checkBackend(){try{const r=await fetch(API+'/api/health',{signal:AbortSignal.timeout(1800)});if(!r.ok)throw 0;$('apiStatus').textContent='Connected';$('apiStatus').style.color='#63d49b'}catch{$('apiStatus').textContent='Offline';$('apiStatus').style.color='#e0a020'}}
function drawChart(){const c=$('chart');if(!c)return;const w=c.clientWidth,h=c.clientHeight,d=devicePixelRatio||1;c.width=w*d;c.height=h*d;const x=c.getContext('2d');x.scale(d,d);const planned=[18,23,29,34,39,45,50,55,60,64,68,72],actual=[16,20,27,31,35,41,45,49,54,58,63,67],p={l:30,r:8,t:12,b:15},cw=w-p.l-p.r,ch=h-p.t-p.b;x.font='10px system-ui';x.fillStyle='#7b8694';x.strokeStyle='#edf0f3';for(let i=0;i<=4;i++){let y=p.t+ch*i/4;x.beginPath();x.moveTo(p.l,y);x.lineTo(w-p.r,y);x.stroke();x.fillText((100-i*25)+'%',2,y+3)}function line(a,dot){x.beginPath();a.forEach((v,i)=>{let X=p.l+cw*i/(a.length-1),Y=p.t+ch*(1-v/100);i?x.lineTo(X,Y):x.moveTo(X,Y)});x.strokeStyle=dot?'#1769e0':'#a7b1bc';x.lineWidth=2;x.stroke()}line(planned,false);line(actual,true)}
window.onresize=drawChart;drawChart();checkBackend();
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

    const total = projects.length;

    const active = projects.filter(
      p => (p.status || '').toLowerCase() === 'active'
    ).length;

    const completed = projects.filter(
      p => (p.status || '').toLowerCase() === 'completed'
    ).length;

    const average = total
      ? projects.reduce(
          (sum, p) => sum + Number(p.overall_progress || 0),
          0
        ) / total
      : 0;

    $('totalProjects').textContent = total;
    $('activeProjects').textContent = active;
    $('completedProjects').textContent = completed;
    $('averageProgress').textContent = average.toFixed(1) + '%';

    const container = $('dashboardProjects');

    if (!projects.length) {
      $('dashboardProjectName').textContent = 'No project selected';
      $('dashboardProjectInfo').textContent =
        'Create a project to begin tracking infrastructure execution.';

      container.innerHTML = `
        <div class="empty-state" style="padding:30px;text-align:center;">
          <h3>No projects available</h3>
          <p>Create your first project from the Projects page.</p>
        </div>
      `;

      return;
    }

    // Show the most recently returned project as the overview project
    const current = projects[0];

    $('dashboardProjectName').textContent =
      current.name || 'Unnamed Project';

    $('dashboardProjectInfo').textContent =
      `${current.location || 'Location not specified'} · ${
        current.project_type || 'Infrastructure'
      }`;

    container.innerHTML = projects.map(p => {

      const progress = Math.max(
        0,
        Math.min(100, Number(p.overall_progress || 0))
      );

      const status = (p.status || 'planned')
        .replace('_', ' ')
        .toUpperCase();

      return `
        <div style="margin-bottom:22px;">
          <div style="
            display:flex;
            justify-content:space-between;
            gap:15px;
            margin-bottom:7px;
          ">
            <strong>${escapeHtml(p.name)}</strong>
            <span>${progress.toFixed(1).replace('.0','')}%</span>
          </div>

          <div class="bar">
            <i style="width:${progress}%"></i>
          </div>

          <small>
            ${escapeHtml(status)}
            ${p.location ? ' · ' + escapeHtml(p.location) : ''}
          </small>
        </div>
      `;

    }).join('');

  } catch (error) {

    $('totalProjects').textContent = '—';
    $('activeProjects').textContent = '—';
    $('completedProjects').textContent = '—';
    $('averageProgress').textContent = '—';

    $('dashboardProjectName').textContent =
      'Unable to load projects';

    $('dashboardProjectInfo').textContent =
      error.message;

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

const originalGo = go;

go = function(page) {
  originalGo(page);

  if (page === 'projects') {
    loadProjects();
  }

  if (page === 'dashboard') {
    loadDashboard();
  }
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    loadProjects();
    loadDashboard();
  });
} else {
  loadProjects();
  loadDashboard();
}