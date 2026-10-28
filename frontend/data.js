// ═══════════════════════════════════════════════════════
// CAMPUS PLACEMENT PORTAL — REAL-TIME REACTIVE DATA STORE
// Unified Relational & Graph State Synchronized via LocalStorage
// ═══════════════════════════════════════════════════════

const STORAGE_KEY = 'CPP_DATABASE';

const INITIAL_DATA = {
  students: [
    { roll: 'CS21001', name: 'Aditya Sharma',   dept: 'CSE', cgpa: 9.4, skills: ['Python','ML','React'],        status: 'hired',       offer: '₹42 LPA', company: 'Google' },
    { roll: 'CS21002', name: 'Priya Gupta',      dept: 'CSE', cgpa: 9.1, skills: ['Java','DSA','Spring'],       status: 'hired',       offer: '₹32 LPA', company: 'Microsoft' },
    { roll: 'EC21010', name: 'Rohan Mehra',      dept: 'ECE', cgpa: 8.7, skills: ['VLSI','Embedded','C++'],    status: 'shortlisted', offer: null,        company: 'Samsung' },
    { roll: 'CS21005', name: 'Sneha Verma',      dept: 'CSE', cgpa: 8.9, skills: ['React','Node','AWS'],        status: 'hired',       offer: '₹28 LPA', company: 'Amazon' },
    { roll: 'ME21003', name: 'Arjun Singh',      dept: 'ME',  cgpa: 7.8, skills: ['AutoCAD','MATLAB'],          status: 'pending',     offer: null,        company: null },
    { roll: 'CS21007', name: 'Kavya Reddy',      dept: 'CSE', cgpa: 9.2, skills: ['ML','TensorFlow','SQL'],     status: 'hired',       offer: '₹35 LPA', company: 'Adobe' },
    { roll: 'EC21015', name: 'Nikhil Joshi',     dept: 'ECE', cgpa: 8.2, skills: ['IoT','Python','Linux'],      status: 'shortlisted', offer: null,        company: 'Qualcomm' },
    { roll: 'CS21012', name: 'Divya Nair',       dept: 'CSE', cgpa: 8.6, skills: ['Go','Docker','K8s'],         status: 'hired',       offer: '₹26 LPA', company: 'Infosys' },
    { roll: 'IT21004', name: 'Rahul Khanna',     dept: 'IT',  cgpa: 8.0, skills: ['SQL','PHP','Laravel'],       status: 'rejected',    offer: null,        company: null },
    { roll: 'CS21020', name: 'Ananya Iyer',      dept: 'CSE', cgpa: 9.5, skills: ['Rust','Algo','Python'],      status: 'hired',       offer: '₹38 LPA', company: 'Goldman Sachs' },
    { roll: 'ME21008', name: 'Varun Tiwari',     dept: 'ME',  cgpa: 7.5, skills: ['SolidWorks','FEA'],          status: 'pending',     offer: null,        company: null },
    { roll: 'CS21018', name: 'Simran Kapoor',    dept: 'CSE', cgpa: 8.8, skills: ['Flutter','Dart','Firebase'], status: 'shortlisted', offer: null,        company: 'Deloitte' },
  ],

  drives: [
    {
      id: 1, company: 'Google', role: 'Software Engineer', ctc: '₹42 LPA',
      type: 'Full-Time', minCgpa: 8.5, depts: ['CSE','IT'],
      deadline: '05 Nov 2026', applicants: 84, capacity: 12,
      description: 'SWE L3/L4 role — Systems & ML team. 3 rounds: DSA + System Design + Behavioural.',
      skills: ['Python','C++','DSA','System Design'],
      status: 'open'
    },
    {
      id: 2, company: 'Microsoft', role: 'SDE II', ctc: '₹32 LPA',
      type: 'Full-Time', minCgpa: 8.0, depts: ['CSE','IT','EC'],
      deadline: '10 Nov 2026', applicants: 120, capacity: 20,
      description: 'Product engineering roles in Azure & Office 365. Strong DSA required.',
      skills: ['Java','C#','Azure','DSA'],
      status: 'open'
    },
    {
      id: 3, company: 'Goldman Sachs', role: 'Technology Analyst', ctc: '₹38 LPA',
      type: 'Full-Time', minCgpa: 8.5, depts: ['CSE','IT','ME'],
      deadline: '08 Nov 2026', applicants: 67, capacity: 8,
      description: 'FinTech engineering — Strats & Quant division. Quantitative aptitude required.',
      skills: ['Python','Quant Finance','SQL'],
      status: 'open'
    },
    {
      id: 4, company: 'Adobe', role: 'MTS — Experience Cloud', ctc: '₹35 LPA',
      type: 'Full-Time', minCgpa: 8.0, depts: ['CSE','IT'],
      deadline: '12 Nov 2026', applicants: 55, capacity: 10,
      description: 'Full-stack engineering on Experience Cloud platform. React & distributed systems.',
      skills: ['React','Node.js','AWS','System Design'],
      status: 'open'
    },
    {
      id: 5, company: 'Samsung R&D', role: 'Staff Engineer', ctc: '₹24 LPA',
      type: 'Full-Time', minCgpa: 7.5, depts: ['ECE','EEE','CSE'],
      deadline: '15 Nov 2026', applicants: 98, capacity: 25,
      description: 'Embedded systems and SoC design. Roles in Bangalore & Noida R&D centres.',
      skills: ['VLSI','Embedded C','Linux'],
      status: 'open'
    },
    {
      id: 6, company: 'McKinsey Digital', role: 'Business Technology Analyst', ctc: '₹18 LPA',
      type: 'Full-Time', minCgpa: 8.0, depts: ['CSE','ME','CE'],
      deadline: '20 Nov 2026', applicants: 40, capacity: 5,
      description: 'Consulting + technology hybrid role. Strong analytical and communication skills.',
      skills: ['Analytics','SQL','Communication'],
      status: 'open'
    },
    {
      id: 7, company: 'Qualcomm', role: 'ASIC Design Engineer', ctc: '₹20 LPA',
      type: 'Full-Time', minCgpa: 7.5, depts: ['ECE','EEE'],
      deadline: '18 Nov 2026', applicants: 62, capacity: 15,
      description: 'Chip design and verification. Focus on 5G baseband and Snapdragon platforms.',
      skills: ['Verilog','SystemVerilog','VLSI'],
      status: 'open'
    },
    {
      id: 8, company: 'Deloitte', role: 'Analyst — USI Tech', ctc: '₹10.5 LPA',
      type: 'Full-Time', minCgpa: 7.0, depts: ['CSE','IT','ME','CE'],
      deadline: '25 Nov 2026', applicants: 210, capacity: 50,
      description: 'Technology consulting and implementation. Business analyst & developer roles.',
      skills: ['SQL','SAP','Communication'],
      status: 'open'
    },
    {
      id: 9, company: 'Amazon', role: 'SDE I', ctc: '₹28 LPA',
      type: 'Full-Time', minCgpa: 8.0, depts: ['CSE','IT'],
      deadline: '03 Nov 2026', applicants: 145, capacity: 18,
      description: 'Core engineering and AWS platform. LP heavy interviews — prepare STAR stories.',
      skills: ['Java','DSA','AWS','System Design'],
      status: 'open'
    },
    {
      id: 10, company: 'Infosys', role: 'Systems Engineer', ctc: '₹8 LPA',
      type: 'Full-Time', minCgpa: 6.5, depts: ['CSE','IT','ME','CE','ECE'],
      deadline: '30 Nov 2026', applicants: 380, capacity: 100,
      description: 'Mass hiring. Service line rotation — Java, .NET, Testing, and Infra tracks.',
      skills: ['Java','.NET','Communication'],
      status: 'open'
    },
    {
      id: 11, company: 'Microsoft', role: 'Research Intern', ctc: '₹2.5L/mo',
      type: 'Internship', minCgpa: 8.5, depts: ['CSE','IT'],
      deadline: '01 Nov 2026', applicants: 32, capacity: 3,
      description: '6-month research internship at MSRI Bangalore. ML systems and AI safety tracks.',
      skills: ['ML','Python','Research'],
      status: 'open'
    },
    {
      id: 12, company: 'Tata Consultancy Services', role: 'Software Developer', ctc: '₹7.5 LPA',
      type: 'Full-Time', minCgpa: 6.0, depts: ['CSE','IT','ME','CE','ECE'],
      deadline: '28 Nov 2026', applicants: 450, capacity: 120,
      description: 'Mass recruiter. Digital and Cloud tracks. Strong aptitude test performance needed.',
      skills: ['Java','SQL','Communication'],
      status: 'open'
    },
  ],

  applications: [
    { app_id: 'APP001', roll_no: 'CS21001', student_name: 'Aditya Sharma', dept: 'CSE', cgpa: 9.4, job_id: 'JOB001', company: 'Google', role: 'Software Engineer', applied_on: '2026-10-20 10:14:00', status: 'hired', package_offered: '₹42 LPA' },
    { app_id: 'APP002', roll_no: 'CS21002', student_name: 'Priya Gupta',   dept: 'CSE', cgpa: 9.1, job_id: 'JOB002', company: 'Microsoft', role: 'SDE II', applied_on: '2026-10-21 11:30:15', status: 'hired', package_offered: '₹32 LPA' },
    { app_id: 'APP003', roll_no: 'CS21005', student_name: 'Sneha Verma',   dept: 'CSE', cgpa: 8.9, job_id: 'JOB009', company: 'Amazon', role: 'SDE I', applied_on: '2026-10-22 09:20:00', status: 'hired', package_offered: '₹28 LPA' },
    { app_id: 'APP004', roll_no: 'EC21010', student_name: 'Rohan Mehra',   dept: 'ECE', cgpa: 8.7, job_id: 'JOB005', company: 'Samsung R&D', role: 'Staff Engineer', applied_on: '2026-10-22 14:05:22', status: 'shortlisted', package_offered: null },
    { app_id: 'APP005', roll_no: 'CS21007', student_name: 'Kavya Reddy',   dept: 'CSE', cgpa: 9.2, job_id: 'JOB004', company: 'Adobe', role: 'MTS — Experience Cloud', applied_on: '2026-10-23 16:40:10', status: 'hired', package_offered: '₹35 LPA' },
    { app_id: 'APP006', roll_no: 'EC21015', student_name: 'Nikhil Joshi',  dept: 'ECE', cgpa: 8.2, job_id: 'JOB007', company: 'Qualcomm', role: 'ASIC Design Engineer', applied_on: '2026-10-24 10:12:30', status: 'shortlisted', package_offered: null },
    { app_id: 'APP007', roll_no: 'CS21012', student_name: 'Divya Nair',    dept: 'CSE', cgpa: 8.6, job_id: 'JOB010', company: 'Infosys', role: 'Systems Engineer', applied_on: '2026-10-24 13:50:00', status: 'hired', package_offered: '₹26 LPA' },
    { app_id: 'APP008', roll_no: 'CS21020', student_name: 'Ananya Iyer',   dept: 'CSE', cgpa: 9.5, job_id: 'JOB003', company: 'Goldman Sachs', role: 'Technology Analyst', applied_on: '2026-10-25 15:10:44', status: 'hired', package_offered: '₹38 LPA' },
    { app_id: 'APP009', roll_no: 'CS21018', student_name: 'Simran Kapoor', dept: 'CSE', cgpa: 8.8, job_id: 'JOB008', company: 'Deloitte', role: 'Analyst — USI Tech', applied_on: '2026-10-25 17:35:12', status: 'shortlisted', package_offered: null },
    { app_id: 'APP010', roll_no: 'IT21004', student_name: 'Rahul Khanna',  dept: 'IT',  cgpa: 8.0, job_id: 'JOB006', company: 'McKinsey Digital', role: 'Business Technology Analyst', applied_on: '2026-10-26 11:00:00', status: 'rejected', package_offered: null },
  ],

  audit_logs: [
    { log_id: 'LOG010', log_timestamp: '2026-10-26 11:30:00', app_id: 'APP010', student_name: 'Rahul Khanna',   action_type: 'UPDATE', old_status: 'Pending',     new_status: 'rejected',    changed_by: 'recruiter_mckinsey' },
    { log_id: 'LOG009', log_timestamp: '2026-10-26 11:00:00', app_id: 'APP010', student_name: 'Rahul Khanna',   action_type: 'INSERT', old_status: 'NULL',        new_status: 'Pending',     changed_by: 'student_portal' },
    { log_id: 'LOG008', log_timestamp: '2026-10-25 18:00:00', app_id: 'APP009', student_name: 'Simran Kapoor',  action_type: 'UPDATE', old_status: 'Pending',     new_status: 'shortlisted', changed_by: 'recruiter_deloitte' },
    { log_id: 'LOG007', log_timestamp: '2026-10-25 16:00:00', app_id: 'APP008', student_name: 'Ananya Iyer',    action_type: 'UPDATE', old_status: 'Interviewing',new_status: 'hired',       changed_by: 'recruiter_gs' },
    { log_id: 'LOG006', log_timestamp: '2026-10-24 16:45:00', app_id: 'APP007', student_name: 'Divya Nair',     action_type: 'UPDATE', old_status: 'Pending',     new_status: 'hired',       changed_by: 'recruiter_infosys' },
    { log_id: 'LOG005', log_timestamp: '2026-10-24 11:15:00', app_id: 'APP006', student_name: 'Nikhil Joshi',   action_type: 'UPDATE', old_status: 'Pending',     new_status: 'shortlisted', changed_by: 'recruiter_qualcomm' },
    { log_id: 'LOG004', log_timestamp: '2026-10-23 18:20:00', app_id: 'APP005', student_name: 'Kavya Reddy',    action_type: 'UPDATE', old_status: 'Shortlisted', new_status: 'hired',       changed_by: 'recruiter_adobe' },
    { log_id: 'LOG003', log_timestamp: '2026-10-22 17:00:00', app_id: 'APP003', student_name: 'Sneha Verma',    action_type: 'UPDATE', old_status: 'Interviewing',new_status: 'hired',       changed_by: 'recruiter_amazon' },
    { log_id: 'LOG002', log_timestamp: '2026-10-21 16:00:00', app_id: 'APP002', student_name: 'Priya Gupta',    action_type: 'UPDATE', old_status: 'Shortlisted', new_status: 'hired',       changed_by: 'recruiter_msft' },
    { log_id: 'LOG001', log_timestamp: '2026-10-20 16:45:00', app_id: 'APP001', student_name: 'Aditya Sharma',  action_type: 'UPDATE', old_status: 'Interviewing',new_status: 'hired',       changed_by: 'recruiter_google' },
  ],

  stats: {
    totalStudents: 847,
    eligible: 712,
    placed: 634,
    offers: 312,
    companies: 47,
    openJobs: 128,
    highestCtc: '₹42 LPA',
    avgCtc: '₹18.4 LPA',
    placementRate: 89,
    topRecruiter: 'Google'
  },

  notifications: [
    { id: 1, date: '27 Oct', title: 'Google Drive Open', desc: 'Applications now open. Deadline: 05 Nov.', type: 'drive' },
    { id: 2, date: '26 Oct', title: 'Shortlist Released', desc: 'Amazon SDE I — 42 students shortlisted for Round 2.', type: 'update' },
    { id: 3, date: '25 Oct', title: 'Offer Letter', desc: 'Congratulations! Aditya Sharma — Google offer confirmed ₹42 LPA.', type: 'offer' },
    { id: 4, date: '24 Oct', title: 'Interview Scheduled', desc: 'Goldman Sachs Tech Interview — 28 Oct, 10:00 AM.', type: 'interview' },
    { id: 5, date: '23 Oct', title: 'New Drive: McKinsey', desc: 'McKinsey Digital — BTA role. Deadline: 20 Nov.', type: 'drive' },
  ]
};

// ═══════════════════════════════════════════════════════
// DB OBJECT DEFINITION
// ═══════════════════════════════════════════════════════
const DB = {
  students:      [],
  drives:        [],
  applications:  [],
  audit_logs:    [],
  stats:         {},
  notifications: [],
  lastUpdated:   0,

  // Save current in-memory state to localStorage
  save() {
    this.lastUpdated = Date.now();
    const payload = {
      students:      this.students,
      drives:        this.drives,
      applications:  this.applications,
      audit_logs:    this.audit_logs,
      stats:         this.stats,
      notifications: this.notifications,
      lastUpdated:   this.lastUpdated
    };
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch(e) {
      console.warn('Storage quota exceeded or unavailable', e);
    }
    // Dispatch local event for same-window subscribers
    window.dispatchEvent(new CustomEvent('cpp-db-change', { detail: { timestamp: this.lastUpdated } }));
  },

  // Load from localStorage or initialize with seed data
  load() {
    let raw = null;
    try {
      raw = localStorage.getItem(STORAGE_KEY);
    } catch(e) {}

    if (raw) {
      try {
        const parsed = JSON.parse(raw);
        this.students      = parsed.students      || JSON.parse(JSON.stringify(INITIAL_DATA.students));
        this.drives        = parsed.drives        || JSON.parse(JSON.stringify(INITIAL_DATA.drives));
        this.applications  = parsed.applications  || JSON.parse(JSON.stringify(INITIAL_DATA.applications));
        this.audit_logs    = parsed.audit_logs    || JSON.parse(JSON.stringify(INITIAL_DATA.audit_logs));
        this.stats         = parsed.stats         || JSON.parse(JSON.stringify(INITIAL_DATA.stats));
        this.notifications = parsed.notifications || JSON.parse(JSON.stringify(INITIAL_DATA.notifications));
        this.lastUpdated   = parsed.lastUpdated   || Date.now();
        return;
      } catch(err) {
        console.error('Failed to parse CPP_DATABASE from storage, resetting', err);
      }
    }

    // Default initialization
    this.reset();
  },

  // Reset to clean seed data
  reset() {
    this.students      = JSON.parse(JSON.stringify(INITIAL_DATA.students));
    this.drives        = JSON.parse(JSON.stringify(INITIAL_DATA.drives));
    this.applications  = JSON.parse(JSON.stringify(INITIAL_DATA.applications));
    this.audit_logs    = JSON.parse(JSON.stringify(INITIAL_DATA.audit_logs));
    this.stats         = JSON.parse(JSON.stringify(INITIAL_DATA.stats));
    this.notifications = JSON.parse(JSON.stringify(INITIAL_DATA.notifications));
    this.save();
  },

  // ── CORE TRANSACTION: Apply for a job drive ──
  // Simulates stored procedure: CALL sp_apply_for_job(...)
  // Automatically fires trigger: trg_application_status -> application_audit_logs
  applyForJob({ jobId, rollNo, studentName, dept, cgpa }) {
    const drive = this.drives.find(d => d.id === Number(jobId));
    if (!drive) {
      return { success: false, message: 'Drive not found' };
    }

    // Find student details or fallback
    let stu = this.students.find(s => s.roll === rollNo);
    if (!stu) {
      stu = {
        roll: rollNo || 'CS21099',
        name: studentName || 'Applicant Student',
        dept: dept || (drive.depts && drive.depts[0]) || 'CSE',
        cgpa: cgpa || 9.0,
        skills: ['Python', 'DSA', 'SQL'],
        status: 'pending',
        offer: null,
        company: null
      };
      this.students.push(stu);
    }

    // Generate unique sequential APP ID
    const maxAppNum = this.applications.reduce((max, a) => {
      const num = parseInt(a.app_id.replace(/\D/g, ''), 10);
      return !isNaN(num) && num > max ? num : max;
    }, 0);
    const newAppId = `APP${String(maxAppNum + 1).padStart(3, '0')}`;

    const now = new Date();
    const ts = now.toISOString().replace('T', ' ').substring(0, 19);

    // 1. Insert into applications relation
    const newApp = {
      app_id: newAppId,
      roll_no: stu.roll,
      student_name: stu.name,
      dept: stu.dept,
      cgpa: stu.cgpa,
      job_id: `JOB${String(drive.id).padStart(3, '0')}`,
      company: drive.company,
      role: drive.role,
      applied_on: ts,
      status: 'pending',
      package_offered: null
    };
    this.applications.unshift(newApp);

    // 2. Increment drive applicant count (OLTP update)
    drive.applicants = (drive.applicants || 0) + 1;

    // 3. Fire trigger: trg_application_status (INSERT audit log)
    const maxLogNum = this.audit_logs.reduce((max, l) => {
      const num = parseInt(l.log_id.replace(/\D/g, ''), 10);
      return !isNaN(num) && num > max ? num : max;
    }, 0);
    const newLogId = `LOG${String(maxLogNum + 1).padStart(3, '0')}`;

    const newLog = {
      log_id: newLogId,
      log_timestamp: ts,
      app_id: newAppId,
      student_name: stu.name,
      action_type: 'INSERT',
      old_status: 'NULL',
      new_status: 'Pending',
      changed_by: 'student_portal'
    };
    this.audit_logs.unshift(newLog);

    // 4. Prepend notification
    this.notifications.unshift({
      id: Date.now(),
      date: 'Just now',
      title: `Applied: ${drive.company}`,
      desc: `${stu.name} (${stu.roll}) applied for ${drive.role} [${newAppId}]`,
      type: 'drive'
    });

    // 5. Update student status if unplaced
    if (!stu.company) {
      stu.status = 'pending';
    }

    // Persist immediately to localStorage
    this.save();

    return {
      success: true,
      application: newApp,
      auditLog: newLog,
      drive: drive
    };
  },

  // ── CORE TRANSACTION: Update Application Status ──
  // Simulates recruiter decision or admin override
  // Automatically fires trigger: trg_application_status (UPDATE audit log)
  updateApplicationStatus(appId, newStatus, changedBy = 'recruiter_db') {
    const app = this.applications.find(a => a.app_id === appId);
    if (!app) return { success: false, message: 'Application not found' };

    const oldStatus = app.status;
    if (oldStatus.toLowerCase() === newStatus.toLowerCase()) return { success: true };

    app.status = newStatus;
    const now = new Date();
    const ts = now.toISOString().replace('T', ' ').substring(0, 19);

    // If Hired, link offer and update student relation
    if (newStatus.toLowerCase() === 'hired') {
      const drive = this.drives.find(d => d.company === app.company && d.role === app.role);
      app.package_offered = drive ? drive.ctc : '₹25 LPA';

      const stu = this.students.find(s => s.roll === app.roll_no);
      if (stu) {
        stu.status = 'hired';
        stu.company = app.company;
        stu.offer = app.package_offered;
      }
      this.stats.placed = (this.stats.placed || 634) + 1;
      this.stats.offers = (this.stats.offers || 312) + 1;
    } else if (newStatus.toLowerCase() === 'shortlisted') {
      const stu = this.students.find(s => s.roll === app.roll_no);
      if (stu && stu.status !== 'hired') {
        stu.status = 'shortlisted';
        stu.company = app.company;
      }
    }

    // Fire audit trigger
    const maxLogNum = this.audit_logs.reduce((max, l) => {
      const num = parseInt(l.log_id.replace(/\D/g, ''), 10);
      return !isNaN(num) && num > max ? num : max;
    }, 0);
    const newLogId = `LOG${String(maxLogNum + 1).padStart(3, '0')}`;

    const newLog = {
      log_id: newLogId,
      log_timestamp: ts,
      app_id: appId,
      student_name: app.student_name,
      action_type: 'UPDATE',
      old_status: oldStatus,
      new_status: newStatus,
      changed_by: changedBy
    };
    this.audit_logs.unshift(newLog);

    this.save();
    return { success: true, application: app, auditLog: newLog };
  },

  // Check if rollNo has applied to a specific drive
  hasStudentApplied(rollNo, jobId) {
    const jobKey = typeof jobId === 'number' ? `JOB${String(jobId).padStart(3, '0')}` : jobId;
    return this.applications.find(a => a.roll_no === rollNo && (a.job_id === jobKey || a.job_id === `JOB00${jobId}` || a.job_id === `JOB0${jobId}`));
  }
};

// Initialize database immediately on script execution
DB.load();

// Cross-tab synchronization listener
window.addEventListener('storage', (e) => {
  if (e.key === STORAGE_KEY) {
    DB.load();
    window.dispatchEvent(new CustomEvent('cpp-db-change', { detail: { fromStorage: true } }));
  }
});
