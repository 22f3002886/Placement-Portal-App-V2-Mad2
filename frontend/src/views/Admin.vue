<template>
  <div class="main-box">
    <h2>Admin Dashboard</h2>

    <!-- ===== STATS ===== -->
    <div class="stats-box">
      <div class="stat">Companies: {{ stats.companies }}</div>
      <div class="stat">Students: {{ stats.students }}</div>
      <div class="stat">Jobs: {{ stats.jobs }}</div>
      <div class="stat">Applications: {{ stats.applications }}</div>
    </div>

    <!-- ===== REPORTS ===== -->
    <h3>Reports</h3>
    <div class="info-card">
      <button
        class="view-btn"
        @click="runDailyReminders"
        :disabled="dailyReminderLoading"
      >{{ dailyReminderLoading ? "Sending..." : "Send Daily Reminders Now" }}</button>
      <p v-if="dailyReminderMessage">{{ dailyReminderMessage }}</p>
    </div>
    <div class="info-card">
      <button
        class="view-btn"
        @click="runMonthlyReport"
        :disabled="monthlyReportLoading"
      >{{ monthlyReportLoading ? "Sending..." : "Send Monthly Report Now" }}</button>
      <p v-if="monthlyReportMessage">{{ monthlyReportMessage }}</p>
      <a v-if="monthlyReportUrl" :href="monthlyReportUrl" target="_blank" class="link-btn">View Report</a>
    </div>

    <!-- ===== PENDING COMPANIES ===== -->
    <h3>Pending Companies</h3>
    <div v-if="pendingCompanies.length === 0">No pending companies</div>

    <div v-for="c in pendingCompanies" :key="c.id" class="info-card">
      <p>
        <b>{{ c.name }}</b>
      </p>
      <p>{{ c.email }}</p>

      <button class="approve-btn" @click="approveCompany(c.id)">Approve</button>
      <button class="danger-btn" @click="rejectCompany(c.id)">Reject</button>
    </div>

    <!-- ===== APPROVED COMPANIES ===== -->
    <h3>Companies</h3>

    <input
      v-model="companySearch"
      @input="searchCompanies"
      placeholder="Search by name or industry..."
    />
    <div v-for="c in companies" :key="c.user_id" class="info-card">
      <p>
        <b>{{ c.company_name }}</b>
        <span v-if="!c.profile_complete" class="incomplete-badge">Profile Incomplete</span>
      </p>
      <p>Jobs: {{ c.jobs_count }}</p>

      <button
        v-if="c.profile_complete"
        class="view-btn"
        @click="viewCompany(c.user_id)"
      >View</button>
      <button
        class="danger-btn"
        @click="blockCompany(c.user_id)"
      >{{ c.is_blocked ? "Unblock" : "Block" }}</button>
    </div>

    <!-- ===== STUDENTS ===== -->
    <h3>Students</h3>

    <input
      v-model="studentSearch"
      @input="searchStudents"
      placeholder="Search by name, ID, email, or phone..."
    />
    <div v-for="s in students" :key="s.user_id" class="info-card">
      <p>
        <b>{{ s.name }}</b>
        <span v-if="!s.profile_complete" class="incomplete-badge">Profile Incomplete</span>
      </p>
      <p>Phone: {{ s.phone }}</p>
      <p>Applications: {{ s.applications }}</p>

      <button class="view-btn" @click="viewStudent(s.user_id)">View</button>

      <button
        class="danger-btn"
        @click="toggleStudent(s.user_id)"
      >{{ s.is_active ? "Block" : "Unblock" }}</button>
    </div>

    <!-- ===== PENDING JOBS ===== -->
    <h3>Pending Drives</h3>
    <div v-if="pendingJobs.length === 0">No pending jobs</div>

    <div v-for="j in pendingJobs" :key="j.id" class="info-card">
      <p>
        <b>{{ j.title }}</b>
      </p>
      <p>{{ j.company }}</p>
      <p v-if="j.application_deadline">Deadline: {{ j.application_deadline }}</p>

      <button class="approve-btn" @click="approveJob(j.id)">Approve</button>
      <button class="danger-btn" @click="rejectJob(j.id)">Reject</button>
    </div>

    <!-- ===== ALL JOBS ===== -->
    <h3>All Drives</h3>
    <input
      v-model="jobSearch"
      @input="searchJobs"
      placeholder="Search by drive, company, skills, or location..."
    />
    <div v-for="j in jobs" :key="j.id" class="info-card">
      <p>
        <b>{{ j.title }}</b>
        <span v-if="j.is_closed" class="incomplete-badge">Closed</span>
      </p>
      <p>{{ j.company }}</p>
      <p v-if="j.application_deadline">Deadline: {{ j.application_deadline }}</p>
      <p>Applications: {{ j.applications_count }}</p>
      <button class="view-btn" @click="viewJob(j.id)">View</button>
      <button
        class="danger-btn"
        @click="blockJob(j.id)"
      >{{ j.is_blacklisted ? "Unblock" : "Block" }}</button>
    </div>

    <!-- ===== ALL APPLICATIONS ===== -->
    <h3>All Applications</h3>
    <div v-if="applications.length === 0">No applications yet</div>

    <div v-for="a in applications" :key="a.id" class="info-card">
      <p><b>{{ a.student_name }}</b> applied to <b>{{ a.job_title }}</b> at {{ a.company_name }}</p>
      <p>Status: {{ a.status }}</p>
      <p>Applied: {{ a.applied_at }}</p>
    </div>
  </div>
</template>

<script>
// This is the admin's home page: approve/reject companies and drives,
// search students and companies, block accounts, and kick off the two
// scheduled report jobs by hand instead of waiting for their Celery timer.
import api from "../services/api";

export default {
  data() {
    return {
      stats: {},
      pendingCompanies: [],
      companies: [],
      students: [],
      pendingJobs: [],
      jobs: [],
      applications: [],
      jobSearch: "",
      companySearch: "",
      studentSearch: "",
      dailyReminderLoading: false,
      dailyReminderMessage: "",
      dailyReminderTaskId: "",
      dailyReminderPoller: null,
      monthlyReportLoading: false,
      monthlyReportMessage: "",
      monthlyReportUrl: "",
      monthlyReportTaskId: "",
      monthlyReportPoller: null
    };
  },

  methods: {
    // ===== REPORTS =====

    runDailyReminders() {
      const token = localStorage.getItem("token");

      this.dailyReminderLoading = true;
      this.dailyReminderMessage = "Daily reminders started. Please wait...";

      api
        .post(
          "/admin/run_daily_reminders",
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        )
        .then(res => {
          this.dailyReminderTaskId = res.data.task_id;
          this.watchDailyReminderStatus();
        })
        .catch(() => {
          this.dailyReminderLoading = false;
          this.dailyReminderMessage = "Could not start daily reminders.";
        });
    },

    // the reminder job runs in the background on Celery, so we don't get
    // an answer straight away — this just asks "is it done yet?" every
    // 2 seconds until the backend says SUCCESS or FAILURE
    watchDailyReminderStatus() {
      const token = localStorage.getItem("token");

      if (this.dailyReminderPoller) {
        clearInterval(this.dailyReminderPoller);
      }

      this.dailyReminderPoller = setInterval(() => {
        api
          .get(`/admin/task_status/${this.dailyReminderTaskId}`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          .then(res => {
            if (res.data.state === "SUCCESS") {
              clearInterval(this.dailyReminderPoller);
              this.dailyReminderPoller = null;
              this.dailyReminderLoading = false;
              this.dailyReminderMessage =
                res.data.result.message || "Daily reminders sent.";
            }

            if (res.data.state === "FAILURE") {
              clearInterval(this.dailyReminderPoller);
              this.dailyReminderPoller = null;
              this.dailyReminderLoading = false;
              this.dailyReminderMessage = "Daily reminders job failed.";
            }
          })
          .catch(() => {
            clearInterval(this.dailyReminderPoller);
            this.dailyReminderPoller = null;
            this.dailyReminderLoading = false;
            this.dailyReminderMessage = "Could not check job status.";
          });
      }, 2000);
    },

    runMonthlyReport() {
      const token = localStorage.getItem("token");

      this.monthlyReportLoading = true;
      this.monthlyReportMessage = "Monthly report started. Please wait...";
      this.monthlyReportUrl = "";

      api
        .post(
          "/admin/generate_monthly_report",
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        )
        .then(res => {
          this.monthlyReportTaskId = res.data.task_id;
          this.watchMonthlyReportStatus();
        })
        .catch(() => {
          this.monthlyReportLoading = false;
          this.monthlyReportMessage = "Could not start monthly report.";
        });
    },

    watchMonthlyReportStatus() {
      const token = localStorage.getItem("token");

      if (this.monthlyReportPoller) {
        clearInterval(this.monthlyReportPoller);
      }

      this.monthlyReportPoller = setInterval(() => {
        api
          .get(`/admin/task_status/${this.monthlyReportTaskId}`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          .then(res => {
            if (res.data.state === "SUCCESS") {
              clearInterval(this.monthlyReportPoller);
              this.monthlyReportPoller = null;
              this.monthlyReportLoading = false;
              this.monthlyReportMessage = "Monthly report sent.";
              this.monthlyReportUrl = res.data.result.report_url || "";
            }

            if (res.data.state === "FAILURE") {
              clearInterval(this.monthlyReportPoller);
              this.monthlyReportPoller = null;
              this.monthlyReportLoading = false;
              this.monthlyReportMessage = "Monthly report job failed.";
            }
          })
          .catch(() => {
            clearInterval(this.monthlyReportPoller);
            this.monthlyReportPoller = null;
            this.monthlyReportLoading = false;
            this.monthlyReportMessage = "Could not check job status.";
          });
      }, 2000);
    },

    // ===== LOAD ALL DATA =====

    loadStats() {
      const token = localStorage.getItem("token");

      api
        .get("/admin/stats", {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.stats = res.data;
        });
    },

    loadPendingCompanies() {
      const token = localStorage.getItem("token");

      api
        .get("/admin/pending_companies", {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.pendingCompanies = res.data;
        });
    },

    loadCompanies() {
      const token = localStorage.getItem("token");

      api
        .get("/admin/all_companies", {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.companies = res.data;
        });
    },

    loadStudents() {
      const token = localStorage.getItem("token");

      api
        .get("/admin/all_students", {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.students = res.data;
        });
    },

    loadPendingJobs() {
      const token = localStorage.getItem("token");

      api
        .get("/admin/pending_jobs", {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.pendingJobs = res.data;
        });
    },

    loadJobs() {
      const token = localStorage.getItem("token");

      api
        .get("/admin/all_jobs", {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.jobs = res.data;
        });
    },

    loadApplications() {
      const token = localStorage.getItem("token");

      api
        .get("/admin/all_applications", {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.applications = res.data;
        });
    },

    searchJobs() {
      const token = localStorage.getItem("token");

      if (this.jobSearch.trim() === "") {
        this.loadJobs();
        return;
      }

      api
        .get(`/admin/search_jobs?q=${this.jobSearch}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.jobs = res.data;
        });
    },

    // ===== ACTIONS =====

    approveCompany(id) {
      const token = localStorage.getItem("token");

      api
        .post(
          `/admin/approve_company/${id}`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        .then(() => {
          alert("Company Approved");
          this.loadPendingCompanies();
          this.loadCompanies();
          this.loadStats();
        })
        .catch(() => {
          alert("Error approving company");
        });
    },

    rejectCompany(id) {
      if (!confirm("Reject this company's registration? This cannot be undone.")) return;

      const token = localStorage.getItem("token");

      api
        .post(
          `/admin/reject_company/${id}`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        .then(() => {
          alert("Company Rejected");
          this.loadPendingCompanies();
          this.loadStats();
        })
        .catch(() => {
          alert("Error rejecting company");
        });
    },

    blockCompany(userId) {
      const token = localStorage.getItem("token");

      api
        .post(
          `/admin/toggle_company_block/${userId}`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        .then(() => {
          // flip the flag right here instead of reloading the whole list,
          // so the button text updates immediately
          const company = this.companies.find(c => c.user_id === userId);
          if (company) {
            company.is_blocked = !company.is_blocked;
          }
        })
        .catch(() => {
          alert("Error blocking/unblocking company");
        });
    },

    approveJob(id) {
      const token = localStorage.getItem("token");

      api
        .put(
          `/admin/approve_job/${id}`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        .then(() => {
          alert("Job Approved");
          this.loadPendingJobs();
          this.loadJobs();
        })
        .catch(() => {
          alert("Error approving job");
        });
    },

    rejectJob(id) {
      if (!confirm("Reject this drive? This deletes it completely — the company will need to post it again.")) return;

      const token = localStorage.getItem("token");

      api
        .put(
          `/admin/reject_job/${id}`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        .then(() => {
          alert("Job Rejected");
          this.loadPendingJobs();
          this.loadJobs();
          this.loadStats();
        })
        .catch(() => {
          alert("Error rejecting job");
        });
    },

    blockJob(id) {
      const token = localStorage.getItem("token");

      api
        .post(
          `/admin/toggle_job_block/${id}`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        .then(() => {
          // same idea as blockCompany above — update the flag locally so
          // the Block/Unblock button text changes right away
          const job = this.jobs.find(j => j.id === id);
          if (job) {
            job.is_blacklisted = !job.is_blacklisted;
          }
        })
        .catch(() => {
          alert("Error blocking/unblocking job");
        });
    },

    viewCompany(id) {
      this.$router.push(`/admin/company/${id}`);
    },

    viewStudent(id) {
      this.$router.push(`/admin/student/${id}`);
    },
    toggleStudent(id) {
      const token = localStorage.getItem("token");

      api
        .post(
          `/admin/toggle_student_block/${id}`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        )
        .then(() => {
          // update it locally instead of re-fetching the whole list
          const student = this.students.find(s => s.user_id === id);
          if (student) {
            student.is_active = !student.is_active;
          }
        })
        .catch(() => {
          alert("Error updating student status");
        });
    },
    viewJob(id) {
      this.$router.push(`/admin/job/${id}`);
    },
    searchStudents() {
      const token = localStorage.getItem("token");

      if (this.studentSearch.trim() === "") {
        this.loadStudents();
        return;
      }

      api
        .get(`/admin/search_students?q=${this.studentSearch}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.students = res.data;
        });
    },

    searchCompanies() {
      const token = localStorage.getItem("token");

      if (this.companySearch.trim() === "") {
        this.loadCompanies();
        return;
      }

      api
        .get(`/admin/search_companies?q=${this.companySearch}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.companies = res.data;
        });
    }
  },

  mounted() {
    // load everything
    this.loadStats();
    this.loadPendingCompanies();
    this.loadCompanies();
    this.loadStudents();
    this.loadPendingJobs();
    this.loadJobs();
    this.loadApplications();
  }
};
</script>

<style>
.main-box {
  max-width: 750px;
  margin: auto;
  padding: 20px;
  min-height: 100vh;
  background-color: #f3e2d4;
}

.main-box h2 {
  color: #5a3825;
  margin-bottom: 12px;
}

.main-box h3 {
  color: #5a3825;
  margin-top: 28px;
  margin-bottom: 10px;
}

.stats-box {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.stat {
  background: white;
  border-left: 4px solid #c47a44;
  padding: 10px 16px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(90, 56, 37, 0.1);
}

.info-card {
  background: white;
  border-left: 4px solid #8a9a5b;
  border-radius: 8px;
  padding: 12px 15px;
  margin: 10px 0;
  box-shadow: 0 1px 3px rgba(90, 56, 37, 0.1);
}

.info-card p {
  margin: 6px 0;
}

input {
  padding: 8px;
  border: 1px solid #d7b49e;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 8px;
  width: 100%;
  max-width: 320px;
}

button {
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
}

.approve-btn {
  background: #4caf50;
  color: white;
  margin-right: 8px;
}

.danger-btn {
  background: #c0392b;
  color: white;
}

.view-btn {
  background: #2196f3;
  color: white;
  margin-right: 8px;
}

.link-btn {
  display: inline-block;
  background: #2196f3;
  color: white;
  text-decoration: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  margin-top: 6px;
}

.link-btn:hover {
  background: #1976d2;
  color: white;
}

.incomplete-badge {
  background: #ead1bc;
  color: #5a3825;
  border-radius: 6px;
  padding: 2px 8px;
  margin-left: 8px;
  font-size: 12px;
  font-weight: normal;
}
</style>