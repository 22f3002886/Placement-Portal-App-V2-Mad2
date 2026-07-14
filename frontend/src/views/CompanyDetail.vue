<template>
  <div class="main-box">

    <button class="back-btn" @click="$router.back()">← Back</button>

    <!-- Company Profile -->
    <div v-if="company" class="profile-box">
      <h3>{{ company.company_name }}</h3>
      <p><b>Industry:</b> {{ company.industry }}</p>
      <p><b>Website:</b> {{ company.website }}</p>
      <p><b>Location:</b> {{ company.location }}</p>
      <p><b>Size:</b> {{ company.company_size }}</p>
      <p><b>HR Contact:</b> {{ company.hr_contact }}</p>
    </div>

    <!-- Jobs -->
    <div class="section-box">
      <h3>Jobs Posted</h3>

      <p v-if="jobs.length === 0" class="empty-msg">
        No jobs posted by this company.
      </p>

      <div v-for="job in jobs" :key="job.id" class="card mb-3 shadow-sm">
        <div class="card-body">
          <h5 class="card-title mb-1">
            {{ job.title }}
            <span v-if="job.is_blacklisted" class="badge bg-dark ms-2">Blocked</span>
            <span v-else-if="job.is_closed" class="badge bg-danger ms-2">Closed</span>
            <span v-else-if="job.is_eligible" class="badge bg-success ms-2">Eligible</span>
            <span v-else class="badge bg-secondary ms-2">Not eligible</span>
          </h5>
          <p class="card-text mb-2">{{ job.description }}</p>
          <div class="small text-muted mb-2">
            <div>
              <b>Skills:</b>
              {{ job.skills }}
            </div>
            <div v-if="job.experience">
              <b>Experience:</b>
              {{ job.experience }}
            </div>
            <div v-if="job.min_cgpa">
              <b>Minimum CGPA:</b>
              {{ job.min_cgpa }}
            </div>
            <div v-if="job.eligible_branches">
              <b>Eligible Branches:</b>
              {{ job.eligible_branches }}
            </div>
            <div v-if="job.eligible_years">
              <b>Eligible Years:</b>
              {{ job.eligible_years }}
            </div>
            <div>
              <b>Location:</b>
              {{ job.location }}
            </div>
            <div>
              <b>Salary:</b>
              {{ job.salary }}
            </div>
            <div>
              <b>Job Type:</b>
              {{ job.job_type }}
            </div>
            <div v-if="job.application_deadline">
              <b>Application Deadline:</b>
              {{ job.application_deadline }}
            </div>
          </div>

          <span v-if="job.is_blacklisted" class="badge bg-secondary">Blocked</span>
          <span v-else-if="job.is_closed" class="badge bg-secondary">Closed</span>
          <button
            v-else-if="!hasApplied(job.id)"
            class="btn btn-sm btn-success"
            :disabled="!job.is_eligible"
            @click="applyJob(job.id)"
          >Apply</button>
          <span v-else class="badge bg-secondary">✓ Applied</span>
        </div>
      </div>
    </div>

  </div>
</template>

<script>
// One company's public page, as seen by a student — profile info plus every
// job that company has posted, with an Apply button on each one.
import api from "../services/api";

export default {
  data() {
    return {
      company: null,
      jobs: [],
      myApplications: [],
    };
  },

  methods: {
    fetchCompanyDetails() {
      const token = localStorage.getItem("token");
      const companyId = this.$route.params.id;

      api.get(`/student/company_details/${companyId}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => {
        this.company = res.data.company;
        this.jobs = res.data.jobs;
      })
      .catch(() => {
        console.log("Error fetching company details");
      });
    },

    fetchMyApplications() {
      const token = localStorage.getItem("token");

      api.get("/student/my_applications", {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => {
        this.myApplications = res.data;
      })
      .catch(() => {
        console.log("Error fetching applications");
      });
    },

    hasApplied(jobId) {
      return this.myApplications.some(app => app.job_id === jobId);
    },

    applyJob(jobId) {
      const token = localStorage.getItem("token");

      if (!confirm("Apply for this job?")) return;

      api.post(
        `/student/apply/${jobId}`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      )
      .then(() => {
        alert("Applied successfully");
        this.myApplications.push({ job_id: jobId });
      })
      .catch((err) => {
        alert(err.response?.data?.message || "Error applying");
      });
    },
  },

  watch: {
    // going from one company's page straight to another company's page
    // reuses this same component instance, so mounted() alone won't
    // refetch — without this, the previous company's data stays on screen
    "$route.params.id"() {
      this.fetchCompanyDetails();
    },
  },

  mounted() {
    this.fetchCompanyDetails();
    this.fetchMyApplications();
  },
};
</script>

<style>
.main-box {
  max-width: 700px;
  margin: auto;
  padding: 20px;
  min-height: 100vh;
  background-color: #f3e2d4;
}

.back-btn {
  background: none;
  border: none;
  color: #2196f3;
  font-size: 15px;
  cursor: pointer;
  margin-bottom: 15px;
  padding: 0;
}

.profile-box {
  border: 1px solid #e0c9b3;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
}

.section-box {
  border: 1px solid #e0c9b3;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
}

.section-box h3 {
  margin-top: 0;
  margin-bottom: 12px;
}

.empty-msg {
  color: #888;
  font-size: 14px;
}
</style>