const API = '';

const URGENCY = {
  baja:    { label: 'BAJA',    icon: '●', cls: 'baja',    bg: '#22c55e' },
  media:   { label: 'MEDIA',   icon: '●', cls: 'media',   bg: '#f59e0b' },
  alta:    { label: 'ALTA',    icon: '●', cls: 'alta',    bg: '#f97316' },
  crítica: { label: 'CRÍTICA', icon: '▲', cls: 'critica', bg: '#ef4444' },
};
const CATEGORIES = {
  acoso:            ['<i class="fa-solid fa-bullseye"></i>',            'Acoso'],
  violencia_fisica: ['<i class="fa-solid fa-bolt"></i>',                'Violencia Física'],
  agresion_verbal:  ['<i class="fa-solid fa-comment-slash"></i>',       'Agresión Verbal'],
  exclusion_social: ['<i class="fa-solid fa-user-slash"></i>',          'Exclusión Social'],
  sustancias:       ['<i class="fa-solid fa-flask"></i>',               'Sustancias'],
  autolesion:       ['<i class="fa-solid fa-triangle-exclamation"></i>','Autolesión'],
  otro:             ['<i class="fa-solid fa-clipboard-list"></i>',      'Otro'],
};
const DEPARTMENTS = {
  tutoria:            ['<i class="fa-solid fa-user"></i>',                  'Tutoría'],
  orientacion:        ['<i class="fa-solid fa-brain"></i>',                 'Orientación'],
  direccion:          ['<i class="fa-solid fa-landmark"></i>',              'Dirección'],
  servicios_externos: ['<i class="fa-solid fa-circle-exclamation"></i>',    'Servicios Externos'],
};

// ── Auth helpers ──────────────────────────────────────────
const token    = () => localStorage.getItem('token');
const userName = () => localStorage.getItem('user_name') || '';
const userRole = () => localStorage.getItem('user_role') || '';
const userDept = () => localStorage.getItem('user_dept') || '';
const tempPwd  = () => localStorage.getItem('temp_password') === '1';

function authHeaders() {
  return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token()}` };
}

async function apiFetch(url, options = {}) {
  options.headers = { ...authHeaders(), ...(options.headers || {}) };
  const res = await fetch(API + url, options);
  if (res.status === 401) { logout(); return null; }
  return res;
}

function logout() {
  localStorage.clear();
  window.location.href = '/login';
}

function rolLabel(role) {
  const map = { admin: 'Admin', profesor: 'Profesor', orientador: 'Orientador',
                tutor: 'Tutor', director: 'Director', externo: 'Ext.' };
  return map[role] || role;
}
function deptLabel(dept) {
  if (!dept) return 'Global';
  const map = { orientacion: 'Orientación', tutoria: 'Tutoría',
                direccion: 'Dirección', servicios_externos: 'Externos',
                profesorado: 'Profesorado' };
  return map[dept] || dept;
}

// ── Navigation ────────────────────────────────────────────
function goToProfile() {
  showPage('page-profile', 'Mi Perfil');

  const sec = document.getElementById('contacts-section');
  if (sec && (userRole() === 'externo' || userDept() === 'servicios_externos')) {
    sec.style.display = 'block';
    const head = sec.querySelector('.profile-section-head');
    const body = sec.querySelector('.profile-section-body');
    if (head) head.classList.add('open');
    if (body) body.classList.add('open');
    loadContacts();
  }

  loadProfile();
}


function showPage(id, title) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const page = document.getElementById(id);
  if (page) page.classList.add('active');
  const nav = document.querySelector(`.nav-item[data-page="${id}"]`);
  if (nav) nav.classList.add('active');
  document.getElementById('topbar-title').textContent = title;
}

// ── Init ──────────────────────────────────────────────────
(function init() {
  if (!token()) { window.location.href = '/login'; return; }

  const name = userName();
  const role = userRole();
  const dept = userDept();

  const savedIcon = localStorage.getItem('avatar_icon') || '';
  const avatarEl = document.getElementById('user-avatar');
  if (savedIcon) {
    avatarEl.innerHTML = `<i class="fa-solid ${savedIcon}"></i>`;
    avatarEl.classList.add('has-icon');
  } else {
    avatarEl.textContent = name.charAt(0).toUpperCase();
  }
  document.getElementById('u-name').textContent      = name;
  document.getElementById('u-role').textContent      = dept ? `${rolLabel(role)} · ${deptLabel(dept)}` : rolLabel(role);
  if (role !== 'admin') {
    document.getElementById('welcome-title').textContent = `Hola, ${name.split(' ')[0]}`;
    document.getElementById('wb-role-pill').textContent  = deptLabel(dept);
  }

  buildSidebar(role);
  if (role !== 'admin') loadDashboard();

  if (tempPwd()) {
    document.getElementById('first-login-modal').classList.remove('hidden');
  }

  // Contacts section: show only for servicios_externos / externo
  const contactsSec = document.getElementById('contacts-section');
  if (contactsSec) {
    if (role === 'externo' || dept === 'servicios_externos') {
      contactsSec.style.display = 'block';
    } else {
      contactsSec.style.display = 'none';
    }
  }
})();

// ── First-login popup ─────────────────────────────────────
function dismissFirstLogin() {
  document.getElementById('first-login-modal').classList.add('hidden');
}

async function modalChangePassword() {
  const cur  = document.getElementById('modal-cur-pwd').value;
  const nw   = document.getElementById('modal-new-pwd').value;
  const conf = document.getElementById('modal-conf-pwd').value;
  const alrt = document.getElementById('modal-alert');

  alrt.className = 'modal-alert';
  if (!cur || !nw || !conf) { alrt.textContent = 'Rellena todos los campos'; alrt.className = 'modal-alert show'; return; }
  if (nw.length < 8)        { alrt.textContent = 'La nueva contraseña debe tener al menos 8 caracteres'; alrt.className = 'modal-alert show'; return; }
  if (nw !== conf)          { alrt.textContent = 'Las contraseñas no coinciden'; alrt.className = 'modal-alert show'; return; }

  const res = await apiFetch('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ current_password: cur, new_password: nw }),
  });
  if (!res) return;
  const data = await res.json();
  if (res.ok) {
    localStorage.setItem('token',        data.access_token);
    localStorage.setItem('temp_password', '0');
    dismissFirstLogin();
  } else {
    alrt.textContent = data.detail ?? 'Error al cambiar contraseña';
    alrt.className   = 'modal-alert show';
  }
}

// ── Sidebar nav ───────────────────────────────────────────
function buildSidebar(role) {
  const nav = [];

  if (role === 'admin') {
    nav.push({ id: 'page-home',         icon: '<i class="fa-solid fa-house"></i>',         label: 'Inicio',        fn: loadAdminHome });
    nav.push({ id: 'page-admin',        icon: '<i class="fa-solid fa-school"></i>',        label: 'Instituciones', fn: _fetchAdminInsts });
    nav.push({ id: 'page-admin-users',  icon: '<i class="fa-solid fa-users"></i>',         label: 'Usuarios',      fn: _fetchAdminUsers });
    nav.push({ id: 'page-admin-invite', icon: '<i class="fa-solid fa-envelope"></i>',      label: 'Invitar Admin', fn: null });
  } else {
    nav.push({ id: 'page-home', icon: '<i class="fa-solid fa-house"></i>', label: 'Inicio', fn: loadDashboard });
  }

  if (role === 'profesor') {
    nav.push({ id: 'page-triage', icon: '<i class="fa-solid fa-file-pen"></i>', label: 'Nuevo Caso' });
  }
  if (role !== 'profesor' && role !== 'admin') {
    nav.push({ id: 'page-inbox', icon: '<i class="fa-solid fa-inbox"></i>', label: 'Bandeja', fn: loadInbox });
  }
  if (role !== 'admin') {
    nav.push({ id: 'page-incidents', icon: '<i class="fa-solid fa-clipboard-list"></i>', label: 'Incidencias', fn: loadIncidents });
  }
  if (role !== 'profesor' && role !== 'admin') {
    nav.push({ id: 'page-calendar', icon: '<i class="fa-solid fa-calendar-days"></i>', label: 'Agenda', fn: loadCalendar });
  }
  if (role === 'director' || role === 'admin') {
    nav.push({ id: 'page-students', icon: '<i class="fa-solid fa-user-graduate"></i>', label: 'Alumnos', fn: loadStudents });
  }
  const container = document.getElementById('sidebar-nav');
  container.innerHTML = nav.map(item => `
    <button class="nav-item" data-page="${item.id}">
      <span class="nav-icon">${item.icon}</span>
      <span>${item.label}</span>
    </button>
  `).join('');

  container.querySelectorAll('.nav-item').forEach((btn, i) => {
    const item = nav[i];
    btn.addEventListener('click', () => {
      showPage(item.id, item.label);
      if (item.fn) item.fn();
    });
  });

  if (role === 'admin') {
    showPage('page-home', 'Inicio');
    document.getElementById('page-home').innerHTML = '';
    loadAdminHome();
  } else {
    showPage('page-home', 'Inicio');
  }
}

// ── Provider selector ─────────────────────────────────────
document.addEventListener('click', e => {
  const opt = e.target.closest('.provider-option');
  if (!opt) return;
  opt.closest('.provider-row').querySelectorAll('.provider-option')
    .forEach(o => o.classList.remove('selected'));
  opt.classList.add('selected');
  opt.querySelector('input').checked = true;
});

// ── Status ────────────────────────────────────────────────
async function checkStatus() {
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-text');
  try {
    const r = await fetch(`${API}/health`);
    if (r.ok) { dot.className = 'status-dot online';  txt.textContent = 'Backend activo'; }
    else throw 0;
  } catch { dot.className = 'status-dot offline'; txt.textContent = 'Sin conexión'; }
}

// ── Students management (direccion / admin) ───────────────
async function loadStudents() {
  const body = document.getElementById('students-body');
  const alrt = document.getElementById('students-alert');
  const form = document.getElementById('add-student-form');
  if (!body) return;

  const render = async () => {
    const res = await apiFetch('/students');
    if (!res) return;
    const list = await res.json();
    if (!list.length) {
      body.innerHTML = '<tr><td colspan="2" style="text-align:center;padding:24px;color:var(--gray-400)">Sin alumnos registrados</td></tr>';
      return;
    }
    body.innerHTML = list.map(s => `
      <tr><td><code>${s.code}</code></td><td>${s.full_name}</td></tr>`).join('');
  };
  await render();

  if (form && !form.dataset.bound) {
    form.dataset.bound = '1';
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const code = document.getElementById('new-student-code').value.trim().toUpperCase();
      const name = document.getElementById('new-student-name').value.trim();
      if (!code || !name) return;
      const res = await apiFetch('/students', {
        method: 'POST',
        body: JSON.stringify({ code, full_name: name }),
      });
      if (!res) return;
      if (res.ok) {
        document.getElementById('new-student-code').value = '';
        document.getElementById('new-student-name').value = '';
        showToast(`Alumno ${name} añadido`);
        await render();
      } else {
        const err = await res.json();
        showAlert(alrt, err.detail ?? 'Error al añadir alumno');
      }
    });
  }
}

// ── Dashboard ─────────────────────────────────────────────
const ROLE_GUIDES = {
  profesor: {
    title: '<i class="fa-solid fa-file-pen"></i> Cómo registrar una incidencia',
    steps: [
      ['<i class="fa-solid fa-pen"></i> Nuevo Caso',    'Busca el código del alumno y describe qué ocurrió con el mayor detalle posible.'],
      ['<i class="fa-solid fa-robot"></i> Análisis IA', 'Dos modelos analizan el texto y proponen categoría, urgencia y departamento.'],
      ['<i class="fa-solid fa-check"></i> Confirma',    'Selecciona la clasificación más precisa. El caso pasa automáticamente a la Bandeja del departamento.'],
      ['<i class="fa-solid fa-eye"></i> Seguimiento',   'En "Incidencias" puedes ver el estado de todo lo que has reportado.'],
    ],
  },
  _nonProfesor: {
    steps: [
      ['<i class="fa-solid fa-inbox"></i> Bandeja',          'Revisa los casos asignados a tu departamento. Cuando estés listo, agenda una cita de seguimiento con fecha, hora y motivo.'],
      ['<i class="fa-solid fa-calendar-days"></i> Agenda',   'Vista mensual de todas tus citas. Puedes editar la fecha u hora de cualquiera y confirmarla tras atender al alumno.'],
      ['<i class="fa-solid fa-shuffle"></i> Redirigir',      'Si un caso supera tu ámbito, redirígeslo a otro departamento desde la Bandeja.'],
      ['<i class="fa-solid fa-clock-rotate-left"></i> Incidencias', 'Historial completo del centro. Detecta patrones de reincidencia y consulta el razonamiento de la IA.'],
    ],
  },
};

const ROLE_TITLES = {
  tutor:      '<i class="fa-solid fa-user"></i> Tu flujo de trabajo · Tutoría',
  orientador: '<i class="fa-solid fa-brain"></i> Tu flujo de trabajo · Orientación',
  director:   '<i class="fa-solid fa-landmark"></i> Tu flujo de trabajo · Dirección',
  externo:    '<i class="fa-solid fa-circle-exclamation"></i> Tu flujo de trabajo · Servicios Externos',
};

const ROLE_EXTRA = {
  director: ['<i class="fa-solid fa-user-graduate"></i> Alumnos', 'Solo dirección puede dar de alta nuevos alumnos y consultar su historial completo de incidencias.'],
  externo:  ['<i class="fa-solid fa-address-book"></i> Contactos', 'En tu perfil tienes el directorio de contactos de emergencia (policía, salud mental…) para actuar con rapidez.'],
};

function renderRoleGuide(role) {
  const guide = document.getElementById('role-guide');
  if (!guide) return;

  if (role === 'profesor') {
    const cfg = ROLE_GUIDES.profesor;
    document.getElementById('role-guide-title').innerHTML = cfg.title;
    document.getElementById('role-guide-steps').innerHTML = cfg.steps.map(([t, d]) =>
      `<div class="guide-step"><div class="gs-icon">${t}</div><div>${d}</div></div>`).join('');
    guide.style.display = 'block';
    return;
  }

  if (!ROLE_TITLES[role]) { guide.style.display = 'none'; return; }

  const steps = [...ROLE_GUIDES._nonProfesor.steps];
  if (ROLE_EXTRA[role]) steps.push(ROLE_EXTRA[role]);

  document.getElementById('role-guide-title').innerHTML = ROLE_TITLES[role];
  document.getElementById('role-guide-steps').innerHTML = steps.map(([t, d]) =>
    `<div class="guide-step"><div class="gs-icon">${t}</div><div>${d}</div></div>`).join('');
  guide.style.display = 'block';
}

async function loadDashboard() {
  const res = await apiFetch('/incidents');
  if (!res) return;
  const data = await res.json();

  document.getElementById('stat-total').textContent     = data.length;
  document.getElementById('stat-pending').textContent   = data.filter(i => !i.confirmed).length;
  document.getElementById('stat-confirmed').textContent = data.filter(i => i.confirmed).length;
  document.getElementById('stat-critical').textContent  = data.filter(i => i.urgency_level === 'crítica').length;

  // Guía de uso por rol
  renderRoleGuide(userRole());

  const recent = [...data].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 5);
  const recentList = document.getElementById('recent-list');
  if (!recent.length) {
    recentList.innerHTML = '<p style="color:var(--gray-400);font-size:.88rem">No hay incidencias registradas.</p>';
    return;
  }
  recentList.innerHTML = recent.map(i => {
    const u      = URGENCY[i.urgency_level] ?? URGENCY.baja;
    const [, cl] = CATEGORIES[i.category]  ?? ['', i.category];
    const date   = new Date(i.created_at).toLocaleDateString('es-ES');
    const badge  = i.confirmed
      ? '<span class="badge-confirmed">Confirmada</span>'
      : '<span class="badge-pending">Pendiente</span>';
    return `<div class="history-item">
      <span class="history-date">${date}</span>
      <span class="history-summary">${cl}</span>
      <span class="history-urgency" style="background:${u.bg}">${i.urgency_level}</span>
      ${badge}
    </div>`;
  }).join('');
}

// ── Analyze + side-by-side ────────────────────────────────
let _analyzeResults  = {};
let _analyzeCtx      = { student: '', text: '', studentCode: '' };

const triageForm       = document.getElementById('triage-form');
const triageResult     = document.getElementById('triage-result');
const triageSpinner    = document.getElementById('triage-spinner');
const triageAlert      = document.getElementById('triage-alert');
const triageBtn        = document.getElementById('triage-btn');
const triageText       = document.getElementById('triage-text');
const lookupBtn        = document.getElementById('lookup-btn');
const studentCodeInput = document.getElementById('student-code-input');
const studentsList     = document.getElementById('students-list');
const studentError     = document.getElementById('student-error');

let _students = []; // [{ code, full_name }]

function checkTriageBtn() {
  triageBtn.disabled = _students.length === 0 || triageText.value.trim().length < 10;
}

function incidentPill(count) {
  if (count === 0) return '<span class="repeat-pill new"><i class="fa-solid fa-check"></i> Sin antecedentes</span>';
  if (count === 1) return '<span class="repeat-pill warn"><i class="fa-solid fa-triangle-exclamation"></i> 1 incidencia previa</span>';
  return `<span class="repeat-pill danger"><i class="fa-solid fa-circle-exclamation"></i> ${count} incidencias previas</span>`;
}

function renderStudentBadges() {
  if (!studentsList) return;
  if (_students.length === 0) {
    studentsList.innerHTML = '';
    triageText.disabled = true;
  } else {
    studentsList.innerHTML = _students.map(s => `
      <div class="student-badge-ok">
        <i class="fa-solid fa-user-graduate"></i>
        <strong>${s.full_name}</strong>
        <span class="chip">${s.code}</span>
        ${incidentPill(s.incident_count ?? 0)}
        <button type="button" class="badge-remove" onclick="removeStudent('${s.code}')"><i class="fa-solid fa-xmark"></i></button>
      </div>`).join('');
    triageText.disabled = false;
  }
  checkTriageBtn();
}

function removeStudent(code) {
  _students = _students.filter(s => s.code !== code);
  renderStudentBadges();
}

async function lookupStudent() {
  const code = studentCodeInput.value.trim().toUpperCase();
  if (!code) return;
  if (studentError) { studentError.style.display = 'none'; studentError.innerHTML = ''; }

  if (_students.find(s => s.code === code)) {
    if (studentError) { studentError.style.display = 'block'; studentError.innerHTML = `<div class="student-badge-error"><i class="fa-solid fa-circle-exclamation"></i> ${code} ya está añadido</div>`; }
    return;
  }

  const res = await apiFetch(`/students/${code}`);
  if (!res) return;
  if (res.status === 404) {
    if (studentError) { studentError.style.display = 'block'; studentError.innerHTML = `<div class="student-badge-error"><i class="fa-solid fa-circle-xmark"></i> Código no encontrado</div>`; }
    return;
  }
  const student = await res.json();
  _students.push({ code: student.code, full_name: student.full_name, incident_count: student.incident_count ?? 0 });
  studentCodeInput.value = '';
  if (studentError) { studentError.style.display = 'none'; }
  renderStudentBadges();
  studentCodeInput.focus();
}

if (lookupBtn) {
  lookupBtn.addEventListener('click', lookupStudent);
  studentCodeInput.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); lookupStudent(); } });
  triageText.addEventListener('input', checkTriageBtn);

  triageForm.addEventListener('submit', async e => {
    e.preventDefault();
    const text = triageText.value.trim();
    if (_students.length === 0) return;

    const codes = _students.map(s => s.code).join(',');
    const names = _students.map(s => s.full_name).join(', ');

    _analyzeResults = {};
    _analyzeCtx     = { student: names, text, studentCode: codes };
    triageResult.innerHTML = '';
    triageAlert.className  = 'alert';
    triageSpinner.classList.add('visible');
    triageBtn.disabled = true;

    try {
      const res = await apiFetch('/analyze', {
        method: 'POST',
        body: JSON.stringify({ student_code: codes, student_name: names, report_text: text }),
      });
      if (!res) return;
      const data = await res.json();

      if (data.ollama_result) _analyzeResults['ollama'] = data.ollama_result;
      if (data.groq_result)   _analyzeResults['groq']   = data.groq_result;

      let html = '';
      if (data.is_repeat && data.student_history?.length) {
        html += buildHistoryPanel(data.student_history);
      }
      html += '<div class="compare-grid">';
      html += data.ollama_result
        ? buildAnalyzeCard(data.ollama_result, '<i class="fa-solid fa-desktop"></i> Local · 8B')
        : `<div class="alert alert-error visible">Modelo local no disponible: ${data.ollama_error ?? ''}</div>`;
      html += data.groq_result
        ? buildAnalyzeCard(data.groq_result, '<i class="fa-solid fa-cloud"></i> Groq · Qwen 27B')
        : `<div class="alert alert-error visible">Modelo nube no disponible: ${data.groq_error ?? ''}</div>`;
      html += '</div>';

      triageResult.innerHTML = html;
    } catch {
      showAlert(triageAlert, 'No se puede conectar con el backend.');
    } finally {
      triageSpinner.classList.remove('visible');
      triageBtn.disabled = false;
    }
  });
}

function buildAnalyzeCard(result, providerLabel) {
  const u        = URGENCY[result.urgency_level] ?? URGENCY.baja;
  const [ci, cl] = CATEGORIES[result.category]   ?? ['<i class="fa-solid fa-clipboard-list"></i>', result.category];
  const [di, dl] = DEPARTMENTS[result.department] ?? ['<i class="fa-solid fa-landmark"></i>', result.department];
  const chips = [
    `<i class="fa-solid fa-clock"></i> ${result.latency_ms.toFixed(0)} ms`,
    result.tokens_used            ? `<i class="fa-solid fa-hashtag"></i> ${result.tokens_used} tokens`            : null,
    result.estimated_cost_usd > 0 ? `<i class="fa-solid fa-dollar-sign"></i> $${result.estimated_cost_usd.toFixed(5)}` : null,
  ].filter(Boolean).map(c => `<span class="chip">${c}</span>`).join('');

  return `
  <div class="result-card u-${u.cls}">
    <div class="result-header">
      <span class="result-title">${providerLabel} · <code style="font-size:.8em">${result.model}</code></span>
      <span class="urgency-badge badge-${u.cls}">${u.icon} ${u.label}</span>
    </div>
    <div class="metrics-row">
      <div class="metric-box"><div class="metric-icon">${ci}</div><div class="metric-label">Categoría</div><div class="metric-value">${cl}</div></div>
      <div class="metric-box"><div class="metric-icon" style="color:var(--yellow)">●</div><div class="metric-label">Urgencia</div><div class="metric-value">${result.urgency_level}</div></div>
      <div class="metric-box"><div class="metric-icon">${di}</div><div class="metric-label">Derivar a</div><div class="metric-value">${dl}</div></div>
    </div>
    <div class="summary-box">"${result.summary}"</div>
    <button class="reasoning-toggle" onclick="toggleReasoning(this)"><i class="fa-solid fa-brain"></i> Ver razonamiento (CoT) <span>▼</span></button>
    <div class="reasoning-body">${result.reasoning}</div>
    <div class="chips-row">${chips}</div>
    <div style="margin-top:16px">
      <button class="btn btn-primary" style="width:100%;justify-content:center"
        onclick="saveChosenResult('${result.provider}')">
        <i class="fa-solid fa-check"></i> Usar esta clasificación
      </button>
    </div>
  </div>`;
}

async function saveChosenResult(provider) {
  const result = _analyzeResults[provider];
  if (!result) return;

  const res = await apiFetch('/incidents/save', {
    method: 'POST',
    body: JSON.stringify({
      student_code: _analyzeCtx.studentCode ?? '',
      student_name: _analyzeCtx.student ?? '',
      report_text: _analyzeCtx.text,
      result,
    }),
  });
  if (!res) return;
  const data = await res.json();
  if (data.success) {
    showToast('Incidencia registrada correctamente', 'success');

    // Reset form
    _students = [];
    renderStudentBadges();
    if (studentCodeInput) studentCodeInput.value = '';
    if (triageText)       triageText.value = '';
    if (studentError)   { studentError.style.display = 'none'; studentError.innerHTML = ''; }
    triageResult.innerHTML = '';
    triageAlert.className  = 'alert';
  }
}

// ── Build card (saved result) ─────────────────────────────
function repeatBadge(n) {
  if (n === 0) return '<span class="repeat-badge new"><i class="fa-solid fa-check"></i> Primera incidencia</span>';
  if (n <= 2)  return `<span class="repeat-badge repeat"><i class="fa-solid fa-triangle-exclamation"></i> Reincidente (${n} prev.)</span>`;
  return `<span class="repeat-badge multiple"><i class="fa-solid fa-circle-exclamation"></i> Múltiple reincidencia (${n} prev.)</span>`;
}

function buildHistoryPanel(history) {
  if (!history.length) return '';
  const items = history.map(h => {
    const u = URGENCY[h.urgency_level] ?? URGENCY.baja;
    const [, cat] = CATEGORIES[h.category] ?? ['', h.category];
    const date = new Date(h.created_at).toLocaleDateString('es-ES');
    return `<div class="history-item">
      <span class="history-date">${date}</span>
      <span class="history-summary">${h.summary}</span>
      <span class="history-urgency" style="background:${u.bg}">${cat}</span>
      ${h.confirmed ? '<i class="fa-solid fa-check" style="color:#22c55e;font-size:.7rem"></i>' : '<i class="fa-solid fa-clock" style="color:#f59e0b;font-size:.7rem"></i>'}
    </div>`;
  }).join('');
  return `<div class="history-panel"><h4><i class="fa-solid fa-scroll"></i> Historial del alumno ${repeatBadge(history.length)}</h4>${items}</div>`;
}

function buildCard(result, title, incidentId = null, history = []) {
  const u        = URGENCY[result.urgency_level] ?? URGENCY.baja;
  const [ci, cl] = CATEGORIES[result.category]   ?? ['<i class="fa-solid fa-clipboard-list"></i>', result.category];
  const [di, dl] = DEPARTMENTS[result.department] ?? ['<i class="fa-solid fa-landmark"></i>', result.department];
  const chips = [
    `<i class="fa-solid fa-gear"></i> ${result.provider} / ${result.model}`,
    `<i class="fa-solid fa-clock"></i> ${result.latency_ms.toFixed(0)} ms`,
    result.tokens_used            ? `<i class="fa-solid fa-hashtag"></i> ${result.tokens_used} tokens`             : null,
    result.estimated_cost_usd > 0 ? `<i class="fa-solid fa-dollar-sign"></i> $${result.estimated_cost_usd.toFixed(5)}` : null,
  ].filter(Boolean).map(c => `<span class="chip">${c}</span>`).join('');

  const canConfirm = incidentId && userRole() !== 'profesor';
  const confirmSection = canConfirm ? `
  <div class="validation-card">
    <h3><i class="fa-solid fa-user-check"></i> Validación humana</h3>
    <p>Revisa la clasificación propuesta por la IA y toma una acción.</p>
    <div class="validation-btns">
      <button class="btn btn-primary" onclick="confirmIncident(${incidentId}, this)"><i class="fa-solid fa-check"></i> Confirmar y derivar</button>
      <button class="btn btn-ghost"   onclick="this.innerHTML='<i class=\\'fa-solid fa-thumbtack\\'></i> Marcado';this.disabled=true"><i class="fa-solid fa-pen"></i> Marcar para revisión</button>
      <button class="btn btn-outline" onclick="openFollowupForm(${incidentId})"><i class="fa-solid fa-calendar-plus"></i> Agendar seguimiento</button>
      <button class="btn btn-outline" onclick="openCardRedirect(${incidentId})"><i class="fa-solid fa-shuffle"></i> Redirigir</button>
    </div>
    <div id="followup-form-${incidentId}" class="add-followup" style="display:none;margin-top:14px;">
      <h5>Agendar seguimiento</h5>
      <div class="form-row">
        <input type="date" id="fu-date-${incidentId}" min="${new Date().toISOString().split('T')[0]}" />
        <input type="text" id="fu-notes-${incidentId}" placeholder="Notas..." style="flex:1;min-width:160px;" />
        <button class="btn btn-primary" onclick="saveFollowup(${incidentId})">Guardar</button>
      </div>
    </div>
    <div id="card-redirect-${incidentId}" class="redirect-inline" style="display:none;margin-top:14px;border-radius:var(--radius-sm)">
      <div class="redirect-inline-title"><i class="fa-solid fa-shuffle"></i> Redirigir clasificación</div>
      <div class="redirect-row">
        <select class="redirect-select" id="cr-dept-${incidentId}">
          <option value="">- Mantener departamento -</option>
          <option value="tutoria">Tutoría</option>
          <option value="orientacion">Orientación</option>
          <option value="direccion">Dirección</option>
          <option value="servicios_externos">Servicios Externos</option>
        </select>
        <select class="redirect-select" id="cr-urg-${incidentId}">
          <option value="">- Mantener urgencia -</option>
          <option value="baja">● Baja</option>
          <option value="media">● Media</option>
          <option value="alta">● Alta</option>
          <option value="crítica">▲ Crítica</option>
        </select>
        <input class="redirect-select" id="cr-reason-${incidentId}" type="text"
          placeholder="Motivo..." style="flex:1;min-width:150px;" />
        <button class="btn btn-primary" style="padding:8px 16px;font-size:.82rem"
          onclick="submitCardRedirect(${incidentId})">Guardar</button>
      </div>
    </div>
  </div>` : '';

  return `
  ${buildHistoryPanel(history)}
  <div class="result-card u-${u.cls}">
    <div class="result-header">
      <span class="result-title">${title}</span>
      <span class="urgency-badge badge-${u.cls}">${u.icon} ${u.label}</span>
    </div>
    <div class="metrics-row">
      <div class="metric-box"><div class="metric-icon">${ci}</div><div class="metric-label">Categoría</div><div class="metric-value">${cl}</div></div>
      <div class="metric-box"><div class="metric-icon" style="color:var(--yellow)">●</div><div class="metric-label">Urgencia</div><div class="metric-value">${result.urgency_level}</div></div>
      <div class="metric-box"><div class="metric-icon">${di}</div><div class="metric-label">Derivar a</div><div class="metric-value">${dl}</div></div>
    </div>
    <div class="summary-box">"${result.summary}"</div>
    <button class="reasoning-toggle" onclick="toggleReasoning(this)"><i class="fa-solid fa-brain"></i> Ver razonamiento (CoT) <span>▼</span></button>
    <div class="reasoning-body">${result.reasoning}</div>
    <div class="chips-row">${chips}</div>
  </div>
  ${confirmSection}`;
}

function toggleReasoning(btn) {
  const body = btn.nextElementSibling;
  body.classList.toggle('open');
  btn.querySelector('span').textContent = body.classList.contains('open') ? '▲' : '▼';
}

function openFollowupForm(id) {
  const el = document.getElementById(`followup-form-${id}`);
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

function openCardRedirect(id) {
  const el = document.getElementById(`card-redirect-${id}`);
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

async function submitCardRedirect(id) {
  const dept    = document.getElementById(`cr-dept-${id}`).value;
  const urgency = document.getElementById(`cr-urg-${id}`).value;
  const reason  = document.getElementById(`cr-reason-${id}`).value.trim();
  if (!dept && !urgency) { showToast('Selecciona al menos un departamento o urgencia', 'error'); return; }

  const body = { redirect_reason: reason };
  if (dept)    body.department    = dept;
  if (urgency) body.urgency_level = urgency;

  const res = await apiFetch(`/incidents/${id}/redirect`, {
    method: 'PATCH', body: JSON.stringify(body),
  });
  if (!res) return;
  const data = await res.json();
  if (data.success) {
    document.getElementById(`card-redirect-${id}`).style.display = 'none';
    const [, dl] = DEPARTMENTS[data.department] ?? ['', data.department];
    const u      = URGENCY[data.urgency_level]  ?? URGENCY.baja;
    showToast(`Redirigida → ${dl} · Urgencia: ${u.label}`);
  } else showToast(data.message ?? 'Error al redirigir', 'error');
}

// ── Confirm incident ──────────────────────────────────────
async function confirmIncident(id, btn) {
  btn.disabled = true; btn.textContent = 'Guardando...';
  const res = await apiFetch(`/incidents/${id}/confirm`, { method: 'PATCH' });
  if (!res) return;
  const d = await res.json();
  btn.innerHTML = d.success ? '<i class="fa-solid fa-check"></i> Confirmado' : '<i class="fa-solid fa-xmark"></i> Error';
}

// ── Save follow-up ────────────────────────────────────────
async function saveFollowup(incidentId) {
  const date  = document.getElementById(`fu-date-${incidentId}`).value;
  const notes = document.getElementById(`fu-notes-${incidentId}`).value;
  if (!date) { showToast('Selecciona una fecha', 'error'); return; }

  const res = await apiFetch('/calendar', {
    method: 'POST',
    body: JSON.stringify({ incident_id: incidentId, scheduled_date: date + 'T09:00:00', notes }),
  });
  if (!res) return;
  if (res.ok) {
    document.getElementById(`followup-form-${incidentId}`).style.display = 'none';
    showToast('Seguimiento agendado correctamente');
  }
}

// ── Inbox ─────────────────────────────────────────────────
async function loadInbox() {
  const container = document.getElementById('inbox-container');
  container.innerHTML = '<p style="color:var(--gray-400)">Cargando...</p>';
  const res = await apiFetch('/incidents');
  if (!res) return;
  const all = await res.json();

  const dept = userDept();
  const data = all.filter(i => !i.confirmed && (!dept || i.department === dept));

  if (!data.length) {
    container.innerHTML = '<div class="inbox-empty"><i class="fa-solid fa-inbox"></i> No hay incidencias pendientes en tu bandeja.</div>';
    return;
  }

  container.innerHTML = `<div class="inbox-grid">${data.map(i => buildInboxCard(i)).join('')}</div>`;
}

function buildInboxCard(i) {
  const u      = URGENCY[i.urgency_level] ?? URGENCY.baja;
  const [ci, cl] = CATEGORIES[i.category]   ?? ['<i class="fa-solid fa-clipboard-list"></i>', i.category];
  const [di, dl] = DEPARTMENTS[i.department] ?? ['<i class="fa-solid fa-landmark"></i>', i.department];
  const date   = new Date(i.created_at).toLocaleDateString('es-ES');

  return `
  <div class="inbox-card u-${u.cls}" id="ic-${i.id}">
    <div class="inbox-card-head">
      <div>
        <div class="inbox-card-name"><i class="fa-solid fa-file-lines"></i> Incidencia #${i.id}</div>
        <div class="inbox-card-meta">${cl} · ${date} · por ${i.reported_by ?? '-'}</div>
      </div>
      <span class="urgency-badge badge-${u.cls}" style="font-size:.7rem">${u.icon} ${u.label}</span>
    </div>
    <div class="inbox-card-body">${i.summary}</div>
    <div class="inbox-card-foot">
      <button class="btn-redirect" onclick="toggleInboxDetail(${i.id})">Ver detalles ▼</button>
      ${i.redirected_by ? '<span class="badge-redirected">Redirigida</span>' : ''}
    </div>
    <div class="inbox-detail" id="icd-${i.id}">
      <div class="inbox-detail-label">Departamento asignado</div>
      <div class="inbox-detail-text" id="icd-dept-${i.id}">${dl}</div>
      <div class="inbox-detail-label">Razonamiento IA</div>
      <div class="inbox-detail-text">${i.reasoning ?? '-'}</div>
      <div class="inbox-detail-actions">
        <button class="btn btn-primary btn-sm" onclick="toggleInboxFollowup(${i.id})"><i class="fa-solid fa-calendar-plus"></i> Agendar cita</button>
        <button class="btn btn-outline btn-sm" onclick="toggleInboxRedirect(${i.id})"><i class="fa-solid fa-shuffle"></i> Redirigir</button>
      </div>
      <div id="inbox-redirect-${i.id}" class="redirect-inline" style="display:none;margin-top:10px;border-radius:var(--radius-sm)">
        <div class="redirect-inline-title"><i class="fa-solid fa-shuffle"></i> Redirigir a otro departamento</div>
        <div class="redirect-row">
          <select class="redirect-select" id="ir-dept-${i.id}">
            <option value="">- Nuevo departamento -</option>
            <option value="tutoria">Tutoría</option>
            <option value="orientacion">Orientación</option>
            <option value="direccion">Dirección</option>
            <option value="servicios_externos">Servicios Externos</option>
          </select>
          <select class="redirect-select" id="ir-urg-${i.id}">
            <option value="">- Mantener urgencia -</option>
            <option value="baja">● Baja</option>
            <option value="media">● Media</option>
            <option value="alta">● Alta</option>
            <option value="crítica">▲ Crítica</option>
          </select>
          <input class="redirect-select" id="ir-reason-${i.id}" type="text"
            placeholder="Motivo de redirección..." style="flex:1;min-width:140px" />
          <button class="btn btn-primary" style="padding:7px 14px;font-size:.8rem"
            onclick="submitInboxRedirect(${i.id})">Guardar</button>
        </div>
      </div>
      <div id="inbox-followup-${i.id}" class="add-followup" style="display:none;margin-top:10px">
        <h5>Agendar cita</h5>
        <div class="form-row">
          <input type="date" id="if-date-${i.id}" min="${new Date().toISOString().split('T')[0]}" />
          <input type="time" id="if-time-${i.id}" value="09:00" />
          <input type="text" id="if-notes-${i.id}" placeholder="Motivo de la cita..." style="flex:1;min-width:140px" />
          <button class="btn btn-primary" onclick="saveFollowupFromInbox(${i.id})">Guardar</button>
        </div>
      </div>
    </div>
  </div>`;
}

function toggleInboxDetail(id) {
  const el = document.getElementById(`icd-${id}`);
  el.classList.toggle('open');
  const btn = el.previousElementSibling.querySelector('button');
  if (btn) btn.textContent = el.classList.contains('open') ? 'Ocultar ▲' : 'Ver detalles ▼';
}

function toggleInboxRedirect(id) {
  const el = document.getElementById(`inbox-redirect-${id}`);
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

function toggleInboxFollowup(id) {
  const el = document.getElementById(`inbox-followup-${id}`);
  el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

async function submitInboxRedirect(id) {
  const dept    = document.getElementById(`ir-dept-${id}`).value;
  const urgency = document.getElementById(`ir-urg-${id}`).value;
  const reason  = document.getElementById(`ir-reason-${id}`).value.trim();
  if (!dept && !urgency) { showToast('Selecciona al menos un departamento o urgencia', 'error'); return; }

  const body = { redirect_reason: reason };
  if (dept)    body.department    = dept;
  if (urgency) body.urgency_level = urgency;

  const res = await apiFetch(`/incidents/${id}/redirect`, {
    method: 'PATCH', body: JSON.stringify(body),
  });
  if (!res) return;
  const data = await res.json();
  if (data.success) {
    const [, dl] = DEPARTMENTS[data.department] ?? ['', data.department];
    document.getElementById(`icd-dept-${id}`).textContent = dl;
    document.getElementById(`inbox-redirect-${id}`).style.display = 'none';
    const card = document.getElementById(`ic-${id}`);
    if (card) card.style.opacity = '.5';
  } else showToast(data.message ?? 'Error al redirigir', 'error');
}

async function saveFollowupFromInbox(incidentId) {
  const date  = document.getElementById(`if-date-${incidentId}`).value;
  const time  = document.getElementById(`if-time-${incidentId}`).value || '09:00';
  const notes = document.getElementById(`if-notes-${incidentId}`).value;
  if (!date) { showToast('Selecciona una fecha', 'error'); return; }

  const res = await apiFetch('/calendar', {
    method: 'POST',
    body: JSON.stringify({ incident_id: incidentId, scheduled_date: `${date}T${time}:00`, notes }),
  });
  if (!res) return;
  if (res.ok) {
    document.getElementById(`inbox-followup-${incidentId}`).style.display = 'none';
    showToast('Cita agendada. Aparecerá en la Agenda para confirmar.');
    const card = document.getElementById(`ic-${incidentId}`);
    if (card) card.style.opacity = '.6';
  }
}

// ── Incidents table ───────────────────────────────────────
async function loadIncidents() {
  const tbody  = document.getElementById('incidents-body');
  const canAct = userRole() !== 'profesor';
  tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:24px;color:var(--gray-400)">Cargando...</td></tr>';
  const res = await apiFetch('/incidents');
  if (!res) return;
  const data = await res.json();
  if (!data.length) {
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:24px;color:var(--gray-400)">No hay incidencias registradas.</td></tr>';
    return;
  }

  const rows = [];
  data.forEach(i => {
    const u      = URGENCY[i.urgency_level] ?? URGENCY.baja;
    const [, cl] = CATEGORIES[i.category]   ?? ['', i.category];
    const [, dl] = DEPARTMENTS[i.department] ?? ['', i.department];
    const date   = new Date(i.created_at).toLocaleDateString('es-ES');
    let badge    = i.confirmed
      ? '<span class="badge-confirmed">Confirmada</span>'
      : '<span class="badge-pending">Pendiente</span>';
    if (i.redirected_by) badge += ' <span class="badge-redirected">Redirigida</span>';

    const actionBtn = canAct
      ? `<button class="btn-redirect" onclick="toggleRedirect(${i.id})"><i class="fa-solid fa-shuffle"></i></button>`
      : '-';

    rows.push(`<tr id="inc-row-${i.id}">
      <td>${i.id}</td>
      <td>${cl}</td>
      <td><span class="history-urgency" style="background:${u.bg}">${i.urgency_level}</span></td>
      <td id="inc-dept-${i.id}">${dl}</td>
      <td style="max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${i.summary}">${i.summary}</td>
      <td>${i.reported_by ?? '-'}</td>
      <td>${date}</td>
      <td id="inc-badge-${i.id}">${badge}</td>
      <td>${actionBtn}</td>
    </tr>`);

    if (canAct) {
      rows.push(`<tr id="redirect-row-${i.id}" style="display:none">
        <td colspan="9" style="padding:0">
          <div class="redirect-inline">
            <div class="redirect-inline-title"><i class="fa-solid fa-shuffle"></i> Redirigir incidencia #${i.id}</div>
            <div class="redirect-row">
              <select class="redirect-select" id="rd-dept-${i.id}">
                <option value="">- Mantener departamento -</option>
                <option value="tutoria">Tutoría</option>
                <option value="orientacion">Orientación</option>
                <option value="direccion">Dirección</option>
                <option value="servicios_externos">Servicios Externos</option>
              </select>
              <select class="redirect-select" id="rd-urg-${i.id}">
                <option value="">- Mantener urgencia -</option>
                <option value="baja">● Baja</option>
                <option value="media">● Media</option>
                <option value="alta">● Alta</option>
                <option value="crítica">▲ Crítica</option>
              </select>
              <input class="redirect-select" id="rd-reason-${i.id}" type="text"
                placeholder="Motivo..." style="flex:1;min-width:160px;" />
              <button class="btn btn-primary" style="padding:8px 16px;font-size:.82rem"
                onclick="submitRedirect(${i.id})">Guardar</button>
              <button class="btn btn-ghost" style="padding:8px 14px;font-size:.82rem"
                onclick="toggleRedirect(${i.id})">Cancelar</button>
            </div>
          </div>
        </td>
      </tr>`);
    }
  });

  tbody.innerHTML = rows.join('');
}

function toggleRedirect(id) {
  const row = document.getElementById(`redirect-row-${id}`);
  row.style.display = row.style.display === 'none' ? 'table-row' : 'none';
}

async function submitRedirect(id) {
  const dept    = document.getElementById(`rd-dept-${id}`).value;
  const urgency = document.getElementById(`rd-urg-${id}`).value;
  const reason  = document.getElementById(`rd-reason-${id}`).value.trim();
  if (!dept && !urgency) { showToast('Selecciona al menos un departamento o urgencia', 'error'); return; }

  const body = { redirect_reason: reason };
  if (dept)    body.department    = dept;
  if (urgency) body.urgency_level = urgency;

  const res = await apiFetch(`/incidents/${id}/redirect`, {
    method: 'PATCH', body: JSON.stringify(body),
  });
  if (!res) return;
  const data = await res.json();
  if (data.success) {
    const [, dl] = DEPARTMENTS[data.department] ?? ['', data.department];
    document.getElementById(`inc-dept-${id}`).textContent = dl;
    document.getElementById(`inc-badge-${id}`).innerHTML += ' <span class="badge-redirected">Redirigida</span>';
    toggleRedirect(id);
  } else showToast(data.message ?? 'Error al redirigir', 'error');
}

// ── Calendar ──────────────────────────────────────────────
let _calYear  = new Date().getFullYear();
let _calMonth = new Date().getMonth();
let _calData  = [];

async function loadCalendar() {
  const list = document.getElementById('calendar-list');
  list.innerHTML = '<p style="color:var(--gray-400)">Cargando...</p>';
  const res = await apiFetch('/calendar');
  if (!res) return;
  _calData = await res.json();
  renderCalendar();
}

function calPrevMonth() { _calMonth--; if (_calMonth < 0) { _calMonth = 11; _calYear--; } renderCalendar(); }
function calNextMonth() { _calMonth++; if (_calMonth > 11) { _calMonth = 0;  _calYear++; } renderCalendar(); }

function renderCalendar() {
  const label = document.getElementById('cal-month-label');
  if (label) {
    const name = new Date(_calYear, _calMonth, 1).toLocaleString('es-ES', { month: 'long', year: 'numeric' });
    label.textContent = name.charAt(0).toUpperCase() + name.slice(1);
  }

  const firstDow = (new Date(_calYear, _calMonth, 1).getDay() + 6) % 7; // Mon=0
  const daysInMonth = new Date(_calYear, _calMonth + 1, 0).getDate();
  const today = new Date();

  // Build day → events map
  const dayMap = {};
  _calData.forEach(f => {
    const d = new Date(f.scheduled_date);
    if (d.getFullYear() === _calYear && d.getMonth() === _calMonth) {
      const day = d.getDate();
      if (!dayMap[day]) dayMap[day] = [];
      dayMap[day].push(f);
    }
  });

  const days = ['L','M','X','J','V','S','D'];
  let html = '<div class="cal-grid">';
  days.forEach(d => { html += `<div class="cal-dow">${d}</div>`; });

  for (let i = 0; i < firstDow; i++) html += '<div class="cal-cell cal-empty"></div>';

  for (let d = 1; d <= daysInMonth; d++) {
    const isToday = today.getFullYear() === _calYear && today.getMonth() === _calMonth && today.getDate() === d;
    const events  = dayMap[d] || [];
    html += `<div class="cal-cell${isToday ? ' cal-today' : ''}">
      <div class="cal-day-num">${d}</div>
      ${events.map(f => buildCalEvent(f)).join('')}
    </div>`;
  }
  html += '</div>';

  const list = document.getElementById('calendar-list');
  if (list) list.innerHTML = html;
}

function buildCalEvent(f) {
  const u    = URGENCY[f.urgency_level] ?? URGENCY.baja;
  const dt   = new Date(f.scheduled_date);
  const time = dt.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
  const dateVal = dt.toISOString().slice(0, 10);
  const timeVal = dt.toTimeString().slice(0, 5);
  const name = f.student_name ? `<span style="font-weight:600">${f.student_name.split(',')[0]}</span> · ` : '';
  const confirmBtn = !f.incident_confirmed
    ? `<button class="cal-confirm-btn" onclick="calConfirm(${f.incident_id}, this)"><i class="fa-solid fa-check"></i> Confirmar</button>`
    : `<span class="cal-confirmed-tag"><i class="fa-solid fa-check-circle"></i> Confirmada por ${f.confirmed_by || f.created_by || '-'}</span>`;
  return `<div class="cal-event u-${u.cls}" id="calevent-${f.id}">
    <div class="cal-event-time">
      ${time} ${u.icon}
      <button class="cal-edit-btn" onclick="toggleCalEdit(${f.id})" title="Editar cita"><i class="fa-solid fa-pencil"></i></button>
    </div>
    <div class="cal-event-body">${name}${f.notes || 'Sin motivo'}</div>
    ${confirmBtn}
    <div class="cal-edit-form" id="caledit-${f.id}" style="display:none">
      <input type="date" id="caledit-date-${f.id}" value="${dateVal}" />
      <input type="time" id="caledit-time-${f.id}" value="${timeVal}" />
      <input type="text" id="caledit-notes-${f.id}" value="${(f.notes || '').replace(/"/g, '&quot;')}" placeholder="Motivo..." />
      <div class="cal-edit-actions">
        <button class="cal-edit-save" onclick="saveCalEdit(${f.id})"><i class="fa-solid fa-floppy-disk"></i> Guardar</button>
        <button class="cal-edit-cancel" onclick="toggleCalEdit(${f.id})">Cancelar</button>
      </div>
    </div>
  </div>`;
}

function toggleCalEdit(fid) {
  const el = document.getElementById(`caledit-${fid}`);
  if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
}

async function saveCalEdit(fid) {
  const date  = document.getElementById(`caledit-date-${fid}`).value;
  const time  = document.getElementById(`caledit-time-${fid}`).value || '09:00';
  const notes = document.getElementById(`caledit-notes-${fid}`).value;
  if (!date) { showToast('Selecciona una fecha', 'error'); return; }

  const res = await apiFetch(`/calendar/${fid}`, {
    method: 'PATCH',
    body: JSON.stringify({ scheduled_date: `${date}T${time}:00`, notes }),
  });
  if (!res) return;
  if (res.ok) {
    const updated = await res.json();
    const idx = _calData.findIndex(f => f.id === fid);
    if (idx !== -1) _calData[idx] = updated;
    renderCalendar();
    showToast('Cita actualizada');
  } else {
    showToast('Error al guardar', 'error');
  }
}

async function calConfirm(incidentId, btn) {
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
  const res = await apiFetch(`/incidents/${incidentId}/confirm`, { method: 'PATCH' });
  if (!res) { btn.disabled = false; return; }
  const data = await res.json();
  if (data.success) {
    showToast('Incidencia confirmada');
    const who = userName();
    _calData = _calData.map(f =>
      f.incident_id === incidentId ? { ...f, incident_confirmed: true, confirmed_by: who } : f
    );
    renderCalendar();
  }
}

// ── Avatar picker ──────────────────────────────────────────
const AVATAR_ICONS = [
  'fa-book-open', 'fa-graduation-cap', 'fa-chalkboard', 'fa-pencil',
  'fa-globe', 'fa-microscope', 'fa-school', 'fa-bus', 'fa-trophy',
  'fa-calculator', 'fa-medal', 'fa-ruler', 'fa-flask', 'fa-music',
  'fa-palette', 'fa-atom', 'fa-compass', 'fa-apple-whole',
];

function renderAvatarPicker(current) {
  const picker = document.getElementById('avatar-picker');
  if (!picker) return;
  picker.innerHTML = AVATAR_ICONS.map(icon => `
    <button class="avatar-opt${current === icon ? ' selected' : ''}" onclick="selectAvatar('${icon}')" title="${icon}">
      <i class="fa-solid ${icon}"></i>
    </button>`).join('');
}

async function selectAvatar(icon) {
  const res = await apiFetch('/profile/avatar', {
    method: 'PATCH',
    body: JSON.stringify({ avatar_icon: icon }),
  });
  if (!res || !res.ok) { showToast('Error al guardar avatar', 'error'); return; }

  localStorage.setItem('avatar_icon', icon);

  // Update sidebar
  const avatarEl = document.getElementById('user-avatar');
  avatarEl.innerHTML = `<i class="fa-solid ${icon}"></i>`;
  avatarEl.classList.add('has-icon');

  // Update profile large avatar
  const lgEl = document.getElementById('profile-avatar-lg');
  if (lgEl) {
    lgEl.innerHTML = `<i class="fa-solid ${icon}"></i>`;
    lgEl.classList.add('has-icon');
  }

  // Update picker selected state
  document.querySelectorAll('.avatar-opt').forEach(btn => btn.classList.remove('selected'));
  document.querySelectorAll('.avatar-opt').forEach(btn => {
    if (btn.querySelector('i')?.classList.contains(icon)) btn.classList.add('selected');
  });

  showToast('Avatar actualizado');
}

// ── Profile ───────────────────────────────────────────────
async function loadProfile() {
  const res = await apiFetch('/profile');
  if (!res) return;
  const p = await res.json();

  const initials = ((p.first_name || p.name || '?').charAt(0)).toUpperCase();
  document.getElementById('profile-avatar-lg').textContent = initials;
  document.getElementById('profile-name').textContent       = p.name || `${p.first_name} ${p.last_name}`.trim();
  document.getElementById('profile-email').textContent      = p.email;
  document.getElementById('profile-role-badge').textContent = rolLabel(p.role);

  const instBadge = document.getElementById('profile-inst-badge');
  if (p.institution_name) {
    instBadge.innerHTML    = `<i class="fa-solid fa-school"></i> ${p.institution_name}`;
    instBadge.style.display = '';
  }

  // Pre-fill name edit fields
  const fnEl = document.getElementById('ps-first-name');
  const lnEl = document.getElementById('ps-last-name');
  if (fnEl) fnEl.value = p.first_name || '';
  if (lnEl) lnEl.value = p.last_name  || '';

  // Load avatar
  localStorage.setItem('avatar_icon', p.avatar_icon || '');
  renderAvatarPicker(p.avatar_icon || '');
  const lgEl = document.getElementById('profile-avatar-lg');
  if (p.avatar_icon) {
    lgEl.innerHTML = `<i class="fa-solid ${p.avatar_icon}"></i>`;
    lgEl.classList.add('has-icon');
  }

  // Show contacts section for servicios_externos
  const contactsSection = document.getElementById('contacts-section');
  if (contactsSection && (p.department === 'servicios_externos' || p.role === 'externo')) {
    contactsSection.style.display = '';
    const head = contactsSection.querySelector('.profile-section-head');
    const body = contactsSection.querySelector('.profile-section-body');
    if (head) head.classList.add('open');
    if (body) body.classList.add('open');
    loadContacts();
  }
}

// ── External Contacts ─────────────────────────────────────

const QUICK_CONTACTS = [
  { label: 'Policía Nacional',      phone: '091' },
  { label: 'Policía Local',         phone: '092' },
  { label: 'Emergencias',           phone: '112' },
  { label: 'Servicios Sociales',    phone: '900 20 11 20' },
  { label: 'Salud Mental Infanto-Juvenil', phone: '024' },
  { label: 'Línea de Atención a Menores',  phone: '116 111' },
];

async function loadContacts() {
  const res = await apiFetch('/contacts');
  if (!res) return;
  const data = await res.json();
  renderContacts(data);
}

function renderContacts(contacts) {
  const list = document.getElementById('contacts-list');
  if (!contacts.length) {
    list.innerHTML = '<p style="font-size:.83rem;color:var(--gray-400);margin-bottom:12px">No hay contactos guardados aún.</p>';
  } else {
    list.innerHTML = contacts.map(c => `
      <div class="contact-card" id="contact-${c.id}">
        <div class="contact-icon"><i class="fa-solid fa-phone"></i></div>
        <div class="contact-info">
          <div class="contact-label">${c.label}</div>
          ${c.notes ? `<div class="contact-notes">${c.notes}</div>` : ''}
        </div>
        <a class="contact-call" href="tel:${c.phone}"><i class="fa-solid fa-phone-volume"></i> ${c.phone}</a>
        <button class="contact-del" onclick="deleteContact(${c.id})" title="Eliminar"><i class="fa-solid fa-trash"></i></button>
      </div>`).join('');
  }

  // Show quick-add suggestions for contacts not yet saved
  const saved = contacts.map(c => c.label.toLowerCase());
  const missing = QUICK_CONTACTS.filter(q => !saved.includes(q.label.toLowerCase()));
  const sug = document.getElementById('contacts-quick-suggestions');
  if (missing.length) {
    sug.innerHTML = `<div class="contacts-quick-title">Sugerencias rápidas</div>` +
      missing.map(q =>
        `<button class="contact-quick-btn" onclick="quickAddContact('${q.label.replace(/'/g,"\\'")}','${q.phone}')">
          <i class="fa-solid fa-plus"></i> ${q.label} <span>${q.phone}</span>
        </button>`
      ).join('');
  } else {
    sug.innerHTML = '';
  }
}

async function addContact() {
  const label = document.getElementById('ct-label').value.trim();
  const phone = document.getElementById('ct-phone').value.trim();
  const notes = document.getElementById('ct-notes').value.trim();
  if (!label || !phone) { showToast('Nombre y teléfono son obligatorios', 'error'); return; }
  const res = await apiFetch('/contacts', {
    method: 'POST',
    body: JSON.stringify({ label, phone, notes }),
  });
  if (!res) return;
  if (res.ok) {
    document.getElementById('ct-label').value = '';
    document.getElementById('ct-phone').value = '';
    document.getElementById('ct-notes').value = '';
    loadContacts();
    showToast('Contacto añadido');
  } else {
    const err = await res.json();
    showToast(err.detail || 'Error al añadir contacto', 'error');
  }
}

async function quickAddContact(label, phone) {
  const res = await apiFetch('/contacts', {
    method: 'POST',
    body: JSON.stringify({ label, phone, notes: '' }),
  });
  if (!res) return;
  if (res.ok) { loadContacts(); showToast(`${label} añadido`); }
}

async function deleteContact(id) {
  const res = await apiFetch(`/contacts/${id}`, { method: 'DELETE' });
  if (!res) return;
  if (res.status === 204 || res.ok) {
    document.getElementById(`contact-${id}`)?.remove();
    loadContacts();
    showToast('Contacto eliminado');
  }
}

async function submitChangeName() {
  const fn   = document.getElementById('ps-first-name').value.trim();
  const ln   = document.getElementById('ps-last-name').value.trim();
  const alrt = document.getElementById('ps-name-alert');
  alrt.className = 'modal-alert';
  if (fn.length < 2) { alrt.textContent = 'El nombre debe tener al menos 2 caracteres'; alrt.className = 'modal-alert show'; return; }

  const res = await apiFetch('/profile/name', {
    method: 'PATCH',
    body: JSON.stringify({ first_name: fn, last_name: ln }),
  });
  if (!res) return;
  const data = await res.json();
  if (res.ok) {
    localStorage.setItem('user_name', data.name);
    document.getElementById('profile-name').textContent    = data.name;
    document.getElementById('u-name').textContent          = data.name;
    document.getElementById('user-avatar').textContent     = data.name.charAt(0).toUpperCase();
    document.getElementById('profile-avatar-lg').textContent = data.name.charAt(0).toUpperCase();
    alrt.innerHTML = '<i class="fa-solid fa-check"></i> Nombre actualizado';
    alrt.style.cssText = 'background:#f0fdf4;border-color:#86efac;color:#166534;display:block';
  } else {
    alrt.textContent = data.detail ?? 'Error al actualizar nombre';
    alrt.className   = 'modal-alert show';
  }
}

function toggleProfileSection(head) {
  head.classList.toggle('open');
  const body = head.nextElementSibling;
  body.classList.toggle('open');
}

async function submitChangePassword() {
  const cur  = document.getElementById('ps-cur-pwd').value;
  const nw   = document.getElementById('ps-new-pwd').value;
  const conf = document.getElementById('ps-conf-pwd').value;
  const alrt = document.getElementById('ps-alert');

  alrt.className = 'modal-alert';
  if (!cur || !nw || !conf) { alrt.textContent = 'Rellena todos los campos'; alrt.className = 'modal-alert show'; return; }
  if (nw.length < 8)        { alrt.textContent = 'Mínimo 8 caracteres'; alrt.className = 'modal-alert show'; return; }
  if (nw !== conf)          { alrt.textContent = 'Las contraseñas no coinciden'; alrt.className = 'modal-alert show'; return; }

  const res = await apiFetch('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({ current_password: cur, new_password: nw }),
  });
  if (!res) return;
  const data = await res.json();
  if (res.ok) {
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('temp_password', '0');
    alrt.innerHTML = '<i class="fa-solid fa-check"></i> Contraseña cambiada correctamente';
    alrt.style.background = '#f0fdf4'; alrt.style.borderColor = '#86efac'; alrt.style.color = '#166534';
    alrt.className = 'modal-alert show';
    document.getElementById('ps-cur-pwd').value  = '';
    document.getElementById('ps-new-pwd').value  = '';
    document.getElementById('ps-conf-pwd').value = '';
  } else {
    alrt.textContent = data.detail ?? 'Error al cambiar contraseña';
    alrt.className   = 'modal-alert show';
  }
}

function showDeleteConfirm() {
  document.getElementById('delete-confirm-wrap').style.display  = 'none';
  document.getElementById('delete-confirm-step2').style.display = 'block';
}

function cancelDeleteConfirm() {
  document.getElementById('delete-confirm-wrap').style.display  = 'block';
  document.getElementById('delete-confirm-step2').style.display = 'none';
}

async function confirmDeleteAccount() {
  const res = await apiFetch('/profile', { method: 'DELETE' });
  if (!res) return;
  const data = await res.json();
  if (res.ok) { logout(); }
  else showToast(data.detail ?? 'Error al eliminar cuenta', 'error');
}

// ── Admin home ────────────────────────────────────────────
async function loadAdminHome() {
  if (!_adminUsers.length || !_adminInsts.length) {
    await Promise.all([_fetchAdminInsts(), _fetchAdminUsers()]);
  }
  const page = document.getElementById('page-home');

  const roleCounts = {};
  _adminUsers.forEach(u => { roleCounts[u.role] = (roleCounts[u.role] || 0) + 1; });
  const maxRole = Math.max(...Object.values(roleCounts), 1);
  const roleLabels = { admin:'Admin', profesor:'Profesor', orientador:'Orientador',
                       tutor:'Tutor', director:'Director', externo:'Externo' };
  const roleRows = Object.entries(roleCounts).map(([role, n]) => `
    <div class="chart-row">
      <div class="chart-label">${roleLabels[role] || role}</div>
      <div class="chart-bar-wrap"><div class="chart-bar" style="width:${(n/maxRole*100).toFixed(0)}%"></div></div>
      <div class="chart-count">${n}</div>
    </div>`).join('');

  const instCounts = {};
  _adminInsts.forEach(i => { instCounts[i.code] = { name: i.name, n: _adminUsers.filter(u => u.institution_code === i.code).length }; });
  const maxInst = Math.max(...Object.values(instCounts).map(v => v.n), 1);
  const instRows = Object.values(instCounts).map(({name, n}) => `
    <div class="chart-row">
      <div class="chart-label">${name}</div>
      <div class="chart-bar-wrap"><div class="chart-bar" style="width:${(n/maxInst*100).toFixed(0)}%;background:var(--yellow-dk)"></div></div>
      <div class="chart-count">${n}</div>
    </div>`).join('') || '<p style="color:var(--gray-400);font-size:.85rem">Sin instituciones</p>';

  page.innerHTML = `
    <div class="stats-grid" style="grid-template-columns:repeat(2,1fr);max-width:460px;margin-bottom:24px">
      <div class="stat-card"><div class="sc-icon sc-blue"><i class="fa-solid fa-users"></i></div><div class="sc-num">${_adminUsers.length}</div><div class="sc-label">Usuarios totales</div></div>
      <div class="stat-card"><div class="sc-icon sc-yellow"><i class="fa-solid fa-school"></i></div><div class="sc-num">${_adminInsts.length}</div><div class="sc-label">Instituciones</div></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
      <div class="card"><div class="card-title"><i class="fa-solid fa-user"></i> Usuarios por rol</div><div class="admin-chart">${roleRows}</div></div>
      <div class="card"><div class="card-title"><i class="fa-solid fa-school"></i> Usuarios por institución</div><div class="admin-chart">${instRows}</div></div>
    </div>`;
}

// ── Admin panel ───────────────────────────────────────────
let _adminInsts = [];
let _adminUsers = [];

async function loadAdmin() {
  await _fetchAdminInsts();
}

async function _fetchAdminInsts() {
  const res = await apiFetch('/institutions');
  if (!res) return;
  _adminInsts = await res.json();
  renderAdminInstitutions();
}

async function _fetchAdminUsers() {
  const res = await apiFetch('/admin/users');
  if (!res) return;
  _adminUsers = await res.json();
  renderAdminUsers();
}

function renderAdminInstitutions() {
  const tbody = document.getElementById('institutions-tbody');
  if (!tbody) return;
  if (!_adminInsts.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--gray-400)">No hay instituciones registradas.</td></tr>';
    return;
  }
  tbody.innerHTML = _adminInsts.map(inst => {
    const count = _adminUsers.filter(u => u.institution_code === inst.code).length;
    const date  = new Date(inst.created_at).toLocaleDateString('es-ES');
    return `<tr id="inst-row-${inst.id}">
      <td>${inst.id}</td>
      <td class="td-name">${inst.name}</td>
      <td>
        <code class="admin-code">${inst.code}</code>
        <button class="btn-copy" title="Copiar código" onclick="copyInstCode('${inst.code}', this)"><i class="fa-solid fa-copy"></i></button>
      </td>
      <td>${count}</td>
      <td>${date}</td>
      <td id="inst-act-${inst.id}">
        <button class="btn btn-danger btn-sm" onclick="confirmDeleteInst(${inst.id})"><i class="fa-solid fa-trash"></i> Eliminar</button>
      </td>
    </tr>`;
  }).join('');
}

function renderAdminUsers() {
  const tbody = document.getElementById('users-tbody');
  if (!tbody) return;
  if (!_adminUsers.length) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--gray-400)">No hay usuarios registrados.</td></tr>';
    return;
  }
  tbody.innerHTML = _adminUsers.map(u => {
    const date    = u.created_at ? new Date(u.created_at).toLocaleDateString('es-ES') : '-';
    const actions = u.role === 'admin'
      ? '<span style="color:var(--gray-400);font-size:.75rem">Admin</span>'
      : `<button class="btn btn-danger btn-sm" onclick="confirmDeleteUser(${u.id}, '${(u.name || '').replace(/'/g, "\\'")}')"><i class="fa-solid fa-trash"></i> Eliminar</button>`;
    return `<tr id="user-row-${u.id}">
      <td>${u.id}</td>
      <td class="td-name">${u.name || '-'}</td>
      <td style="font-size:.8rem">${u.email || '-'}</td>
      <td><span class="pi-badge">${rolLabel(u.role)}</span></td>
      <td>${deptLabel(u.department)}</td>
      <td>${u.institution_name ?? '-'}</td>
      <td style="font-size:.75rem;color:var(--gray-400)">${date}</td>
      <td id="user-act-${u.id}">${actions}</td>
    </tr>`;
  }).join('');
}

function confirmDeleteInst(id) {
  document.getElementById(`inst-act-${id}`).innerHTML = `
    <span style="font-size:.75rem;color:#991b1b;margin-right:6px">¿Seguro?</span>
    <button class="btn btn-danger btn-sm" onclick="executeDeleteInst(${id})">Sí, eliminar</button>
    <button class="btn btn-ghost btn-sm" style="margin-left:4px" onclick="renderAdminInstitutions()">Cancelar</button>
  `;
}

async function executeDeleteInst(id) {
  const res = await apiFetch(`/institutions/${id}`, { method: 'DELETE' });
  if (!res) return;
  if (res.ok) {
    _adminInsts = _adminInsts.filter(i => i.id !== id);
    renderAdminInstitutions();
    renderAdminUsers();
  } else {
    const data = await res.json();
    showToast(data.detail ?? 'Error al eliminar institución', 'error');
    renderAdminInstitutions();
  }
}

function confirmDeleteUser(id, name) {
  document.getElementById(`user-act-${id}`).innerHTML = `
    <span style="font-size:.75rem;color:#991b1b;margin-right:4px">¿Eliminar a ${name}?</span>
    <button class="btn btn-danger btn-sm" onclick="executeDeleteUser(${id})">Sí</button>
    <button class="btn btn-ghost btn-sm" style="margin-left:4px" onclick="renderAdminUsers()">No</button>
  `;
}

async function executeDeleteUser(id) {
  const res = await apiFetch(`/admin/users/${id}`, { method: 'DELETE' });
  if (!res) return;
  if (res.ok) {
    _adminUsers = _adminUsers.filter(u => u.id !== id);
    renderAdminUsers();
    renderAdminInstitutions();
  } else {
    const data = await res.json();
    showToast(data.detail ?? 'Error al eliminar usuario', 'error');
    renderAdminUsers();
  }
}

function showInviteAdminForm() {
  document.getElementById('invite-admin-form').style.display = 'block';
  document.getElementById('inv-first').focus();
}

function hideInviteAdminForm() {
  document.getElementById('invite-admin-form').style.display = 'none';
  ['inv-first','inv-last','inv-email'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('invite-admin-alert').className = 'modal-alert';
}

async function submitInviteAdmin() {
  const first = document.getElementById('inv-first').value.trim();
  const last  = document.getElementById('inv-last').value.trim();
  const email = document.getElementById('inv-email').value.trim();
  const alrt  = document.getElementById('invite-admin-alert');
  alrt.className = 'modal-alert';

  if (first.length < 2) { alrt.textContent = 'Introduce el nombre'; alrt.className = 'modal-alert show'; return; }
  if (!email.includes('@')) { alrt.textContent = 'Correo no válido'; alrt.className = 'modal-alert show'; return; }

  const res = await apiFetch('/admin/create-admin', {
    method: 'POST',
    body: JSON.stringify({ first_name: first, last_name: last, email }),
  });
  if (!res) return;
  const data = await res.json();
  if (res.ok) {
    showToast(`Administrador creado - invitación enviada a ${email}`);
    document.getElementById('inv-first').value = '';
    document.getElementById('inv-last').value  = '';
    document.getElementById('inv-email').value = '';
    _fetchAdminUsers();
  } else {
    alrt.textContent = data.detail ?? 'Error al enviar invitación';
    alrt.className   = 'modal-alert show';
  }
}

function showCreateInstForm() {
  document.getElementById('create-inst-form').style.display = 'block';
  document.getElementById('new-inst-name').focus();
}

function hideCreateInstForm() {
  document.getElementById('create-inst-form').style.display = 'none';
  document.getElementById('new-inst-name').value = '';
  document.getElementById('create-inst-alert').className = 'modal-alert';
}

async function submitCreateInst() {
  const name = document.getElementById('new-inst-name').value.trim();
  const alrt = document.getElementById('create-inst-alert');
  alrt.className = 'modal-alert';
  if (name.length < 3) {
    alrt.textContent = 'El nombre debe tener al menos 3 caracteres';
    alrt.className   = 'modal-alert show';
    return;
  }
  const res = await apiFetch('/institutions', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
  if (!res) return;
  const data = await res.json();
  if (res.ok) {
    _adminInsts.push(data);
    renderAdminInstitutions();
    hideCreateInstForm();
  } else {
    alrt.textContent = data.detail ?? 'Error al crear institución';
    alrt.className   = 'modal-alert show';
  }
}

function copyInstCode(code, btn) {
  navigator.clipboard.writeText(code).then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-check"></i>';
    setTimeout(() => btn.innerHTML = orig, 1200);
  }).catch(() => {});
}

// ── Util ──────────────────────────────────────────────────
function showAlert(el, msg) {
  el.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> ' + msg;
  el.className   = 'alert alert-error visible';
}

let _toastTimer = null;
function showToast(msg, type = 'success') {
  const el = document.getElementById('toast');
  el.style.background = type === 'success' ? '#166534' : '#991b1b';
  el.innerHTML = `<i class="fa-solid fa-${type === 'success' ? 'circle-check' : 'circle-xmark'}"></i> ${msg}`;
  el.classList.add('show');
  if (_toastTimer) clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove('show'), 3500);
}
