// Akademie Trutnov - Frontend Application Logic
const API_BASE = '/api/v1';

const app = {
  data: {
    courses: [],
    terms: [],
    students: [],
    lecturers: [],
    selectedTermId: null
  },

  async init() {
    try {
      await Promise.all([
        this.loadCourses(),
        this.loadTerms(),
        this.loadStudents(),
        this.loadLecturers()
      ]);
      this.updateKPIs();
      this.populateTermDropdowns();
      this.populateStudentDropdown();
      if (this.data.terms.length > 0) {
        this.data.selectedTermId = this.data.terms[0].id;
        document.getElementById('filter-term').value = this.data.selectedTermId;
        this.loadRegistrationsForSelectedTerm();
      }
    } catch (err) {
      this.showToast('Chyba při načítání dat: ' + err.message, 'error');
    }
  },

  async fetchJson(url, options = {}) {
    const res = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options
    });
    if (!res.ok) {
      let errorMsg = 'Chyba serveru';
      try {
        const data = await res.json();
        errorMsg = data.detail || JSON.stringify(data);
      } catch (e) {
        errorMsg = res.statusText;
      }
      throw new Error(errorMsg);
    }
    return res.json();
  },

  // Přepínání záložek
  switchTab(tabName) {
    document.querySelectorAll('.nav-tab').forEach(t => {
      t.classList.toggle('active', t.getAttribute('data-tab') === tabName);
    });
    document.querySelectorAll('.tab-content').forEach(c => {
      c.style.display = 'none';
    });
    const target = document.getElementById(`tab-${tabName}`);
    if (target) target.style.display = 'block';

    if (tabName === 'terms') {
      this.renderTerms();
    } else if (tabName === 'registrations') {
      this.loadRegistrationsForSelectedTerm();
    } else if (tabName === 'attendance_certs') {
      this.loadAttendanceView();
    } else if (tabName === 'reports') {
      this.loadReports();
    }
  },

  // KPI metriky
  updateKPIs() {
    document.getElementById('kpi-courses').textContent = this.data.courses.length;
    document.getElementById('kpi-terms').textContent = this.data.terms.length;
    document.getElementById('kpi-students').textContent = this.data.students.length;
  },

  // Načtení dat
  async loadCourses() {
    this.data.courses = await this.fetchJson(`${API_BASE}/courses`);
    this.renderCourses();
  },

  async loadTerms() {
    this.data.terms = await this.fetchJson(`${API_BASE}/terms`);
    this.renderTerms();
  },

  async loadStudents() {
    this.data.students = await this.fetchJson(`${API_BASE}/students`);
  },

  async loadLecturers() {
    this.data.lecturers = await this.fetchJson(`${API_BASE}/lecturers`);
  },

  // Vykreslení kurzů
  renderCourses() {
    const grid = document.getElementById('courses-grid');
    if (!grid) return;
    grid.innerHTML = this.data.courses.map(course => `
      <div class="card" id="course-${course.id}">
        <div class="card-top">
          <div class="card-title">${course.name}</div>
          <span class="badge ${course.is_accredited ? 'badge-accredited' : 'badge-standard'}">
            ${course.is_accredited ? 'Akreditováno' : 'Firemní kurz'}
          </span>
        </div>
        <p class="card-desc">${course.annotation || 'Bez detailního popisu.'}</p>
        <div class="card-meta">
          <div>
            <span>Délka: <strong>${course.hours_duration} hod.</strong></span>
          </div>
          <div class="card-price">
            ${new Intl.NumberFormat('cs-CZ', { style: 'currency', currency: 'CZK', maximumFractionDigits: 0 }).format(course.price)}
          </div>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="app.openRegisterModalForCourse(${course.id})">
          Zapsat se na termín
        </button>
      </div>
    `).join('');
  },

  // Vykreslení termínů
  renderTerms() {
    const grid = document.getElementById('terms-grid');
    if (!grid) return;
    grid.innerHTML = this.data.terms.map(term => {
      const course = this.data.courses.find(c => c.id === term.course_id) || { name: 'Kurz' };
      const pct = term.capacity > 0 ? Math.min(100, Math.round((term.occupied_count / term.capacity) * 100)) : 0;
      let progClass = 'progress-normal';
      if (pct >= 100) progClass = 'progress-full';
      else if (pct >= 80) progClass = 'progress-warning';

      return `
        <div class="card" id="term-${term.id}">
          <div class="card-top">
            <div>
              <div class="card-title">${course.name}</div>
              <div style="font-size: 0.8rem; color: var(--accent); margin-top: 0.2rem;">
                ${term.location}, ${term.classroom}
              </div>
            </div>
            <span class="badge ${term.occupied_count >= term.capacity ? 'badge-waiting' : 'badge-confirmed'}">
              ${term.occupied_count >= term.capacity ? 'Kapacita plná' : 'Volná místa'}
            </span>
          </div>

          <div style="font-size: 0.85rem; color: var(--text-muted);">
            Termín: <strong>${new Date(term.date_from).toLocaleDateString('cs-CZ')}</strong> – <strong>${new Date(term.date_to).toLocaleDateString('cs-CZ')}</strong>
          </div>

          <div>
            <div style="display: flex; justify-content: space-between; font-size: 0.825rem; margin-bottom: 0.2rem;">
              <span>Obsazenost: <strong>${term.occupied_count} / ${term.capacity}</strong></span>
              <span>${pct} %</span>
            </div>
            <div class="progress-bar-container">
              <div class="progress-bar-fill ${progClass}" style="width: ${pct}%"></div>
            </div>
            ${term.waiting_count > 0 ? `
              <div style="font-size: 0.8rem; color: #fbbf24; margin-top: 0.4rem;">
                V FIFO pořadníku čeká: <strong>${term.waiting_count} zájemců</strong>
              </div>
            ` : ''}
          </div>

          <div class="card-meta">
            <button class="btn btn-secondary btn-sm" onclick="app.viewTermQueue(${term.id})">
              Zobrazit účastníky
            </button>
            <button class="btn btn-primary btn-sm" onclick="app.openRegisterModal(${term.id})">
              Přihlásit se
            </button>
          </div>
        </div>
      `;
    }).join('');
  },

  // Dropdowny
  populateTermDropdowns() {
    const filterSelect = document.getElementById('filter-term');
    const modalSelect = document.getElementById('reg-term-id');
    const options = this.data.terms.map(t => {
      const course = this.data.courses.find(c => c.id === t.course_id) || { name: 'Kurz' };
      return `<option value="${t.id}">#${t.id}: ${course.name} (${t.location}, kap. ${t.occupied_count}/${t.capacity})</option>`;
    }).join('');

    if (filterSelect) filterSelect.innerHTML = options;
    if (modalSelect) modalSelect.innerHTML = options;
  },

  populateStudentDropdown() {
    const studentSelect = document.getElementById('reg-student-id');
    if (!studentSelect) return;
    studentSelect.innerHTML = this.data.students.map(s => `
      <option value="${s.id}">${s.first_name} ${s.last_name} (${s.email})</option>
    `).join('');
  },

  updateSelectedTermCapacityInfo() {
    const termId = parseInt(document.getElementById('reg-term-id').value);
    const term = this.data.terms.find(t => t.id === termId);
    const info = document.getElementById('reg-term-info');
    if (term && info) {
      if (term.occupied_count >= term.capacity) {
        info.innerHTML = `<strong style="color: #fbbf24;">Kapacita ${term.capacity} míst je plně obsazena.</strong> Student bude automaticky zařazen do <strong>FIFO pořadníku náhradníků</strong> na pozici #${term.waiting_count + 1}.`;
      } else {
        info.innerHTML = `Volná místa: <strong>${term.capacity - term.occupied_count}</strong> z ${term.capacity}. Student získá potvrzenou registraci.`;
      }
    }
  },

  viewTermQueue(termId) {
    this.data.selectedTermId = termId;
    document.getElementById('filter-term').value = termId;
    this.switchTab('registrations');
  },

  // Načtení přihlášek vybraného termínu (FIFO Pořadník)
  async loadRegistrationsForSelectedTerm() {
    const termId = parseInt(document.getElementById('filter-term').value);
    if (!termId) return;
    this.data.selectedTermId = termId;

    try {
      const regs = await this.fetchJson(`${API_BASE}/registrations/term/${termId}`);
      const tbody = document.getElementById('registrations-tbody');
      const waitingCallout = document.getElementById('waiting-list-info');
      const waitingText = document.getElementById('waiting-list-text');

      const waitingCount = regs.filter(r => r.status === 'WAITING_LIST').length;
      if (waitingCount > 0) {
        waitingCallout.style.display = 'flex';
        waitingText.innerHTML = `V pořadníku náhradníků čeká <strong>${waitingCount} studentů</strong>. Při odhlášení zapsaného studenta se první náhradník (č. 1) automaticky posune na potvrzené místo.`;
      } else {
        waitingCallout.style.display = 'none';
      }

      if (regs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">Zatím žádné přihlášky na tento termín.</td></tr>`;
        return;
      }

      tbody.innerHTML = regs.map(reg => {
        let badgeClass = 'badge-confirmed';
        let statusText = 'Zapsán (Potvrzeno)';
        if (reg.status === 'WAITING_LIST') {
          badgeClass = 'badge-waiting';
          statusText = 'Čeká v pořadníku';
        } else if (reg.status === 'CANCELLED') {
          badgeClass = 'badge-cancelled';
          statusText = 'Zrušeno (Auditováno)';
        }

        const canCancel = reg.status === 'CONFIRMED' || reg.status === 'WAITING_LIST';

        return `
          <tr id="reg-row-${reg.id}">
            <td>#${reg.id}</td>
            <td><strong>${reg.student_name}</strong></td>
            <td>${reg.student_email || '—'}</td>
            <td>${new Date(reg.registration_date).toLocaleDateString('cs-CZ')}</td>
            <td><span class="badge ${badgeClass}">${statusText}</span></td>
            <td>${reg.queue_position ? `<strong style="color: #fbbf24;">#${reg.queue_position}</strong> (FIFO)` : '—'}</td>
            <td>
              ${canCancel ? `
                <button class="btn btn-danger btn-sm" onclick="app.cancelRegistration(${reg.id}, '${reg.student_name}')">
                  Odhlásit studenta
                </button>
              ` : '<span style="color: var(--text-dim); font-size: 0.8rem;">Neměnné</span>'}
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      this.showToast('Chyba načítání přihlášek: ' + err.message, 'error');
    }
  },

  // Zrušení přihlášky a demonstrace automatického posunu FIFO
  async cancelRegistration(regId, studentName) {
    if (!confirm(`Opravdu chcete zrušit registraci studenta ${studentName}?`)) return;

    try {
      const result = await this.fetchJson(`${API_BASE}/registrations/${regId}/cancel`, {
        method: 'POST'
      });

      if (result.promoted_registration_id) {
        this.showToast(`Přihláška zrušena. Uvolněné místo automaticky obsadil náhradník #${result.promoted_registration_id} z FIFO pořadníku.`, 'success');
      } else {
        this.showToast(`Přihláška #${regId} byla zrušena a zaevidována pro audit.`, 'info');
      }

      await this.loadTerms();
      this.populateTermDropdowns();
      await this.loadRegistrationsForSelectedTerm();
      this.updateKPIs();
    } catch (err) {
      this.showToast('Chyba při rušení registrace: ' + err.message, 'error');
    }
  },

  // Zápis nové přihlášky
  openRegisterModal(termId = null) {
    if (termId) {
      document.getElementById('reg-term-id').value = termId;
    }
    this.updateSelectedTermCapacityInfo();
    document.getElementById('modal-register').classList.add('open');
  },

  openRegisterModalForCourse(courseId) {
    const term = this.data.terms.find(t => t.course_id === courseId);
    this.openRegisterModal(term ? term.id : null);
  },

  async submitRegistration(event) {
    event.preventDefault();
    const studentId = parseInt(document.getElementById('reg-student-id').value);
    const termId = parseInt(document.getElementById('reg-term-id').value);
    const isLate = document.getElementById('reg-force-late').checked;
    const reason = document.getElementById('reg-exception-reason').value;

    const payload = {
      student_id: studentId,
      term_id: termId,
      allow_late_registration: isLate,
      late_registration_reason: isLate ? reason : null
    };

    try {
      const res = await this.fetchJson(`${API_BASE}/registrations`, {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      if (res.status === 'WAITING_LIST') {
        this.showToast(`Kapacita byla plná. Student byl zařazen do FIFO pořadníku jako náhradník č. ${res.queue_position}.`, 'warning');
      } else {
        this.showToast('Student byl úspěšně zapsán do termínu kurzu.', 'success');
      }

      this.closeModal('modal-register');
      await this.loadTerms();
      this.populateTermDropdowns();
      if (this.data.selectedTermId === termId) {
        await this.loadRegistrationsForSelectedTerm();
      }
      this.updateKPIs();
    } catch (err) {
      this.showToast('Chyba registrace: ' + err.message, 'error');
    }
  },

  // Nový kurz
  openNewCourseModal() {
    document.getElementById('modal-course').classList.add('open');
  },

  async submitNewCourse(event) {
    event.preventDefault();
    const payload = {
      name: document.getElementById('new-course-name').value,
      annotation: document.getElementById('new-course-annotation').value,
      hours_duration: parseInt(document.getElementById('new-course-hours').value),
      price: parseFloat(document.getElementById('new-course-price').value),
      is_accredited: document.getElementById('new-course-accredited').checked
    };

    try {
      await this.fetchJson(`${API_BASE}/courses`, {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      this.showToast('Nový kurz byl úspěšně vytvořen.', 'success');
      this.closeModal('modal-course');
      await this.loadCourses();
      this.updateKPIs();
    } catch (err) {
      this.showToast('Chyba vytvoření kurzu: ' + err.message, 'error');
    }
  },

  // Nový termín
  openNewTermModal() {
    const courseSelect = document.getElementById('new-term-course-id');
    courseSelect.innerHTML = this.data.courses.map(c => `
      <option value="${c.id}">${c.name} (${c.hours_duration} hod., ${c.is_accredited ? 'Akreditovaný' : 'Neakreditovaný'})</option>
    `).join('');

    const lecList = document.getElementById('new-term-lecturers-list');
    lecList.innerHTML = this.data.lecturers.map(l => `
      <div style="display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;">
        <label style="display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; cursor: pointer; flex: 1;">
          <input type="checkbox" class="term-lecturer-check" data-lecturer-id="${l.id}" onchange="document.getElementById('term-lec-hours-${l.id}').disabled = !this.checked">
          <span><strong>${l.first_name} ${l.last_name}</strong> <small style="color: var(--text-dim);">(${l.email})</small></span>
        </label>
        <div style="display: flex; align-items: center; gap: 0.35rem;">
          <input type="number" id="term-lec-hours-${l.id}" class="form-control" style="width: 75px; padding: 0.25rem 0.5rem; font-size: 0.85rem;" min="1" value="20" disabled>
          <span style="font-size: 0.8rem; color: var(--text-dim);">hod.</span>
        </div>
      </div>
    `).join('');

    // Nastavit výchozí datum (za 14 dní)
    const dFrom = new Date();
    dFrom.setDate(dFrom.getDate() + 14);
    const dTo = new Date();
    dTo.setDate(dTo.getDate() + 18);
    document.getElementById('new-term-date-from').value = dFrom.toISOString().split('T')[0];
    document.getElementById('new-term-date-to').value = dTo.toISOString().split('T')[0];

    document.getElementById('modal-term').classList.add('open');
  },

  async submitNewTerm(event) {
    event.preventDefault();
    const courseId = parseInt(document.getElementById('new-term-course-id').value);
    const dateFrom = document.getElementById('new-term-date-from').value;
    const dateTo = document.getElementById('new-term-date-to').value;
    const location = document.getElementById('new-term-location').value;
    const classroom = document.getElementById('new-term-classroom').value;
    const capacity = parseInt(document.getElementById('new-term-capacity').value);

    const lecturers = [];
    document.querySelectorAll('.term-lecturer-check:checked').forEach(cb => {
      const lid = parseInt(cb.getAttribute('data-lecturer-id'));
      const hours = parseInt(document.getElementById(`term-lec-hours-${lid}`).value) || 0;
      lecturers.push({ lecturer_id: lid, taught_hours: hours });
    });

    const payload = {
      course_id: courseId,
      date_from: dateFrom,
      date_to: dateTo,
      location: location,
      classroom: classroom,
      capacity: capacity,
      lecturers: lecturers
    };

    try {
      await this.fetchJson(`${API_BASE}/terms`, {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      this.showToast('Nový termín byl úspěšně vytvořen.', 'success');
      this.closeModal('modal-term');
      await this.loadTerms();
      this.populateTermDropdowns();
      this.updateKPIs();
    } catch (err) {
      this.showToast('Chyba vytvoření termínu: ' + err.message, 'error');
    }
  },

  // Nový student
  openNewStudentModal() {
    document.getElementById('modal-student').classList.add('open');
  },

  async submitNewStudent(event) {
    event.preventDefault();
    const payload = {
      first_name: document.getElementById('new-student-first-name').value,
      last_name: document.getElementById('new-student-last-name').value,
      email: document.getElementById('new-student-email').value,
      phone: document.getElementById('new-student-phone').value || null
    };

    try {
      const newStudent = await this.fetchJson(`${API_BASE}/students`, {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      this.showToast(`Student ${newStudent.first_name} ${newStudent.last_name} byl úspěšně zaregistrován.`, 'success');
      this.closeModal('modal-student');
      await this.loadStudents();
      this.populateStudentDropdown();
      const sel = document.getElementById('reg-student-id');
      if (sel) sel.value = newStudent.id;
      this.updateKPIs();
    } catch (err) {
      this.showToast('Chyba registrace studenta: ' + err.message, 'error');
    }
  },

  // Záložka Docházka a Osvědčení
  async loadAttendanceView() {
    const tbody = document.getElementById('attendance-tbody');
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center;">Načítám docházku a certifikáty...</td></tr>`;

    try {
      let allRows = [];
      for (const term of this.data.terms) {
        const regs = await this.fetchJson(`${API_BASE}/registrations/term/${term.id}`);
        for (const reg of regs) {
          if (reg.status === 'CONFIRMED') {
            const summary = await this.fetchJson(`${API_BASE}/attendance/summary/${reg.id}`);
            allRows.push({ term, reg, summary });
          }
        }
      }

      if (allRows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">Zatím žádní zapsaní studenti s evidovanou docházkou.</td></tr>`;
        return;
      }

      tbody.innerHTML = allRows.map(({ term, reg, summary }) => {
        const course = this.data.courses.find(c => c.id === term.course_id) || { name: 'Kurz' };
        const pct = summary.attendance_percentage || 0;
        const qualifies = summary.qualifies_for_certificate;

        return `
          <tr>
            <td><strong>${reg.student_name}</strong></td>
            <td>${course.name} <br><small style="color: var(--text-dim);">${term.location}</small></td>
            <td><span class="badge badge-confirmed">Zapsán</span></td>
            <td>
              <strong>${pct.toFixed(1)} %</strong>
              <div style="font-size: 0.75rem; color: ${qualifies ? '#34d399' : '#f87171'};">
                ${qualifies ? 'Splňuje limit (≥70%)' : 'Nesplňuje limit (≥70%)'}
              </div>
            </td>
            <td>
              <span class="badge ${summary.lecturer_approved ? 'badge-confirmed' : 'badge-standard'}">
                ${summary.lecturer_approved ? 'Schváleno' : 'Čeká na lektora'}
              </span>
            </td>
            <td>
              ${summary.certificate_number ? `
                <strong style="color: #fbbf24;">${summary.certificate_number}</strong>
              ` : '<span style="color: var(--text-dim);">Nevydáno</span>'}
            </td>
            <td>
              <div style="display: flex; gap: 0.4rem;">
                ${pct < 70 ? `
                  <button class="btn btn-secondary btn-sm" onclick="app.recordDemoAttendance(${reg.id})">
                    Zapsat docházku (100%)
                  </button>
                ` : ''}
                ${!summary.certificate_number ? `
                  <button class="btn btn-primary btn-sm" onclick="app.issueCertificate(${reg.id}, '${reg.student_name}')">
                    Vydat osvědčení
                  </button>
                ` : `
                  <button class="btn btn-secondary btn-sm" onclick="app.viewCertificate('${summary.certificate_number}')">
                    Zobrazit
                  </button>
                `}
              </div>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      this.showToast('Chyba načítání docházky: ' + err.message, 'error');
    }
  },

  async recordDemoAttendance(regId) {
    const today = new Date().toISOString().split('T')[0];
    try {
      await this.fetchJson(`${API_BASE}/attendance`, {
        method: 'POST',
        body: JSON.stringify({
          registration_id: regId,
          records: [
            { lesson_date: today, hours_attended: 40, is_present: true }
          ]
        })
      });
      this.showToast('Docházka studenta byla zapsána.', 'success');
      this.loadAttendanceView();
    } catch (err) {
      this.showToast('Chyba zápisu docházky: ' + err.message, 'error');
    }
  },

  async issueCertificate(regId, studentName) {
    try {
      const res = await this.fetchJson(`${API_BASE}/certificates/issue`, {
        method: 'POST',
        body: JSON.stringify({
          registration_id: regId,
          lecturer_approved: true
        })
      });
      this.showToast(`Osvědčení ${res.certificate_number} bylo úspěšně vystaveno pro studenta ${studentName}.`, 'success');
      this.viewCertificate(res.certificate_number);
      this.loadAttendanceView();
      this.updateKPIs();
    } catch (err) {
      this.showToast('Nelze vydat osvědčení: ' + err.message, 'error');
    }
  },

  async viewCertificate(certNumber) {
    try {
      const cert = await this.fetchJson(`${API_BASE}/certificates/${certNumber}`);
      document.getElementById('cert-view-number').textContent = cert.certificate_number;
      document.getElementById('cert-view-student').textContent = cert.student_name;
      document.getElementById('cert-view-course').textContent = cert.course_name;
      document.getElementById('cert-view-date').textContent = new Date(cert.issue_date).toLocaleDateString('cs-CZ');
      document.getElementById('modal-certificate').classList.add('open');
    } catch (err) {
      this.showToast('Chyba načítání osvědčení: ' + err.message, 'error');
    }
  },

  // Manažerské reporty
  async loadReports() {
    try {
      // 1. Occupancy report
      const occ = await this.fetchJson(`${API_BASE}/reports/occupancy`);
      const occTbody = document.getElementById('report-occupancy-tbody');
      occTbody.innerHTML = occ.map(item => `
        <tr>
          <td><strong>${item.course_name}</strong><br><small style="color: var(--text-dim);">${item.location}</small></td>
          <td>${item.capacity}</td>
          <td><strong style="color: #34d399;">${item.confirmed_count}</strong></td>
          <td><strong style="color: #fbbf24;">${item.waiting_count}</strong></td>
          <td>${item.occupancy_percentage.toFixed(1)} %</td>
        </tr>
      `).join('');

      // 2. Lecturer hours report
      const lecs = await this.fetchJson(`${API_BASE}/reports/lecturer-hours`);
      const lecTbody = document.getElementById('report-lecturers-tbody');
      lecTbody.innerHTML = lecs.map(item => `
        <tr>
          <td><strong>${item.lecturer_name}</strong><br><small style="color: var(--text-dim);">${item.email}</small></td>
          <td>${item.total_terms}</td>
          <td><strong style="color: var(--accent);">${item.total_hours} hod.</strong></td>
        </tr>
      `).join('');

      // 3. Multi-course students report
      const multi = await this.fetchJson(`${API_BASE}/reports/multi-course-students?year=2026`);
      const multiTbody = document.getElementById('report-students-tbody');
      if (multi.length === 0) {
        multiTbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 1rem;">Žádný student se v tomto roce nepřihlásil na více než 1 kurz.</td></tr>`;
      } else {
        multiTbody.innerHTML = multi.map(item => `
          <tr>
            <td><strong>${item.student_name}</strong></td>
            <td>${item.email}</td>
            <td><strong style="color: #34d399;">${item.course_count}</strong></td>
            <td>${item.courses.join(', ')}</td>
          </tr>
        `).join('');
      }
    } catch (err) {
      this.showToast('Chyba načítání reportů: ' + err.message, 'error');
    }
  },

  // CSV Exporty
  downloadCSV(filename, csvContent) {
    const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },

  async exportOccupancyCSV() {
    try {
      const occ = await this.fetchJson(`${API_BASE}/reports/occupancy`);
      let csv = 'Termín ID;Kurz;Lokalita;Kapacita;Potvrzeno (zapsáno);Čekající (FIFO);Obsazenost (%)\n';
      occ.forEach(item => {
        csv += `${item.term_id};"${item.course_name}";"${item.location}";${item.capacity};${item.confirmed_count};${item.waiting_count};${item.occupancy_percentage.toFixed(1)}\n`;
      });
      this.downloadCSV('akademie_trutnov_obsazenost_terminu.csv', csv);
      this.showToast('CSV export obsazenosti byl stažen.', 'success');
    } catch (err) {
      this.showToast('Chyba při exportu: ' + err.message, 'error');
    }
  },

  async exportLecturersCSV() {
    try {
      const lecs = await this.fetchJson(`${API_BASE}/reports/lecturer-hours`);
      let csv = 'Lektor;E-mail;Počet termínů;Odučené hodiny celkem\n';
      lecs.forEach(item => {
        csv += `"${item.lecturer_name}";"${item.email}";${item.total_terms};${item.total_hours}\n`;
      });
      this.downloadCSV('akademie_trutnov_hodiny_lektoru.csv', csv);
      this.showToast('CSV export hodin lektorů byl stažen.', 'success');
    } catch (err) {
      this.showToast('Chyba při exportu: ' + err.message, 'error');
    }
  },

  // Modal a Toast utility
  closeModal(modalId) {
    document.getElementById(modalId).classList.remove('open');
  },

  showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<div>${message}</div>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
};

// Spustit aplikaci po načtení DOMu
document.addEventListener('DOMContentLoaded', () => {
  app.init();
});
