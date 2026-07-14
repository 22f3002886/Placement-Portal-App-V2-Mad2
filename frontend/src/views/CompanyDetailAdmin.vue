<template>
  <div class="main-box">
    <button class="back-btn" @click="$router.back()">← Back</button>

    <h2>Company Details</h2>

    <!-- ===== COMPANY INFO ===== -->
    <div v-if="company" class="profile-box">
      <p><b>Company Name:</b> {{ company.company_name }}</p>
      <p><b>Email:</b> {{ company.email }}</p>
      <p><b>Industry:</b> {{ company.industry }}</p>
      <p><b>Website:</b> {{ company.website }}</p>
      <p><b>Location:</b> {{ company.location }}</p>
      <p><b>Company Size:</b> {{ company.company_size }}</p>
      <p><b>HR Contact:</b> {{ company.hr_contact }}</p>
      <p><b>Status:</b> {{ company.is_blocked ? "Blocked" : "Active" }}</p>
      <p><b>Joined On:</b> {{ company.created_at }}</p>

      <button class="danger-btn" @click="toggleCompany">
        {{ company.is_blocked ? "Unblock Company" : "Block Company" }}
      </button>
    </div>

    <!-- ===== JOBS ===== -->
    <h3>Jobs Posted</h3>

    <div v-if="jobs.length === 0">No jobs posted</div>

    <div v-for="job in jobs" :key="job.id" class="info-card">
      <p><b>{{ job.title }}</b></p>
      <p>{{ job.description }}</p>
      <p><b>Salary:</b> {{ job.salary }}</p>
      <p v-if="job.application_deadline"><b>Application Deadline:</b> {{ job.application_deadline }}</p>
      <p><b>Applications:</b> {{ job.applications_count }}</p>
      <p><b>Drive Status:</b> {{ job.is_closed ? "Closed" : "Open" }}</p>
      <p><b>Status:</b> {{ job.is_blacklisted ? "Blocked" : "Active" }}</p>

      <button class="danger-btn" @click="toggleJob(job.id)">
        {{ job.is_blacklisted ? "Unblock Job" : "Block Job" }}
      </button>
    </div>
  </div>
</template>

<script>
// Admin's view of one company: full profile, every job they've posted, and
// a block/unblock button for the company and for each job individually.
import api from "../services/api";

export default {
  data() {
    return {
      company: null,
      jobs: [],
    };
  },

  methods: {
    loadCompany() {
      const token = localStorage.getItem("token");
      const id = this.$route.params.id;

      api.get(`/admin/company_details/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => {
        this.company = res.data.company;
        this.jobs = res.data.jobs;
      })
      .catch(() => {
        alert("Error loading company");
      });
    },

    toggleCompany() {
      const token = localStorage.getItem("token");

      api.post(`/admin/toggle_company_block/${this.company.user_id}`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then(() => {
        this.company.is_blocked = !this.company.is_blocked;
      })
      .catch(() => {
        alert("Error updating company status");
      });
    },

    toggleJob(jobId) {
      const token = localStorage.getItem("token");

      api.post(`/admin/toggle_job_block/${jobId}`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then(() => {
        const job = this.jobs.find(j => j.id === jobId);
        if (job) job.is_blacklisted = !job.is_blacklisted;
      })
      .catch(() => {
        alert("Error updating job status");
      });
    }
  },

  mounted() {
    this.loadCompany();
  },
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

.profile-box {
  background: white;
  border-left: 4px solid #4a7a8c;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(90, 56, 37, 0.1);
}

.info-card {
  background: white;
  border-left: 4px solid #8a9a5b;
  border-radius: 8px;
  padding: 10px 15px;
  margin: 10px 0;
  box-shadow: 0 1px 3px rgba(90, 56, 37, 0.1);
}

.danger-btn {
  background: #c0392b;
  color: white;
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  margin-top: 5px;
}

.back-btn {
  background: none;
  border: none;
  color: #2196f3;
  cursor: pointer;
  margin-bottom: 15px;
}
</style>