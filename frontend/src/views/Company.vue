<template>
  <div class="main-box">
    <!-- Welcome Bar -->
    <div class="welcome-bar">
      <span>Welcome, {{ companyName }}</span>
    </div>

    <!-- Getting Started (shown until the profile is completed) -->
    <div v-if="!company_data" class="section-box">
      <h3>Get started</h3>
      <p>Complete your company profile so students can see who you are, then start posting placement drives.</p>
      <button class="create-btn" @click="showForm = true">
        + Complete Profile
      </button>
    </div>

    <!-- Profile Button -->
    <button v-if="company_data" class="create-btn" @click="showForm = true">
      + Update Profile
    </button>

    <!-- Profile Form -->
    <div v-if="showForm" class="form-box">
      <h3>
        {{ company_data ? "Update Company Profile" : "Create Company Profile" }}
      </h3>

      <input :value="profile.company_name" @input="filterCompanyName" placeholder="Company Name" />
      <input :value="profile.industry" @input="filterIndustry" placeholder="Industry" />
      <input v-model="profile.website" placeholder="Website" />
      <input :value="profile.location" @input="filterCompanyLocation" placeholder="Location" />
      <input :value="profile.company_size" @input="filterCompanySize" placeholder="Company Size" />
      <input :value="profile.hr_contact" @input="filterHrContact" placeholder="HR Contact" inputmode="numeric" />

      <div class="form-actions">
        <button v-if="!company_data" class="primary-btn" @click="submitProfile">Submit</button>
        <button v-if="company_data" class="primary-btn" @click="editProfile">Update Profile</button>
        <button class="cancel-btn" @click="showForm = false">Cancel</button>
      </div>
    </div>

    <!-- Profile Display -->
    <div v-if="company_data" class="profile-box">
      <h3>Company Profile</h3>

      <p><b>Name:</b> {{ company_data.company_name }}</p>
      <p><b>Industry:</b> {{ company_data.industry }}</p>
      <p><b>Website:</b> {{ company_data.website }}</p>
      <p><b>Location:</b> {{ company_data.location }}</p>
      <p><b>Size:</b> {{ company_data.company_size }}</p>
      <p><b>HR Contact:</b> {{ company_data.hr_contact }}</p>
    </div>

    <!-- Job Button -->
    <button class="create-btn" @click="openJobForm">+ Post Job</button>

    <!-- Job Form -->
    <div v-if="showJobForm" class="form-box" ref="jobFormBox">
      <h3>{{ editingJobId ? "Edit Job" : "Post Job" }}</h3>

      <input :value="jobForm.title" @input="filterJobTitle" placeholder="Job Title" />
      <input v-model="jobForm.description" placeholder="Description" />
      <input v-model="jobForm.skills" placeholder="Skills" />
      <input v-model="jobForm.experience" placeholder="Experience" />
      <input :value="jobForm.salary" @input="filterSalary" placeholder="Salary" />
      <input :value="jobForm.location" @input="filterJobLocation" placeholder="Location" />

      <label>Application Deadline</label>
      <input v-model="jobForm.application_deadline" type="date" />

      <h4 class="criteria-heading">Eligibility Criteria</h4>
      <input :value="jobForm.min_cgpa" @input="filterMinCgpa" placeholder="Minimum CGPA" inputmode="decimal" />
      <input v-model="jobForm.eligible_branches" placeholder="Eligible Branches (comma-separated, e.g. CSE, ECE)" />
      <input v-model="jobForm.eligible_years" placeholder="Eligible passing year" />

      <div class="form-actions">
        <button v-if="!editingJobId" class="primary-btn" @click="postJob">Post</button>
        <button v-if="editingJobId" class="primary-btn" @click="updateJob">Save Changes</button>
        <button class="cancel-btn" @click="showJobForm = false">Cancel</button>
      </div>
    </div>

    <!-- Jobs List -->
    <div v-if="jobs.length > 0" class="job-list">
      <h3>Your Jobs</h3>

      <div v-for="job in jobs" :key="job.id" class="card mb-3 shadow-sm">
        <div class="card-body">
          <h5 class="card-title mb-1">
            {{ job.title }}
            <span v-if="job.is_blacklisted" class="badge bg-dark ms-2">Blocked</span>
            <span v-else-if="!job.is_approved" class="badge bg-warning text-dark ms-2">Pending</span>
            <span v-else-if="job.is_closed" class="badge bg-danger ms-2">Closed</span>
            <span v-else class="badge bg-success ms-2">Open</span>
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
            <div v-if="job.application_deadline">
              <b>Application Deadline:</b>
              {{ job.application_deadline }}
            </div>
            <div>
              <b>Applicants:</b>
              {{ job.applications_count }}
            </div>
          </div>

          <div class="d-flex gap-2">
            <button
              class="btn btn-sm btn-secondary"
              @click="editJob(job)"
            >
              Edit
            </button>

            <button
              class="btn btn-sm btn-danger"
              v-if="job.is_closed === false"
              @click="closeJob(job.id)"
            >
              Close Job
            </button>

            <button
              class="btn btn-sm btn-primary"
              v-if="job.is_closed === true"
              @click="openJob(job.id)"
            >
              Reopen Job
            </button>
            <button
              @click="$router.push(`/job/${job.id}/applicants`)"
              class="btn btn-sm btn-primary"
            >
              View Applicants
            </button>
          </div>
        </div>
      </div>

    </div>

  </div>
</template>

<script>
// Company's home page: fill in the company profile, post placement drives,
// and open/close them. Applicants for a drive are handled on a separate
// page (ViewApplicant.vue), reached from the "View Applicants" button below.
import api from "../services/api";

export default {
  data() {
    return {
      showForm: false,
      showJobForm: false,
      editingJobId: null,
      companyName: localStorage.getItem("name") || "",
      company_data: null,
      profile: {
        company_name: "",
        industry: "",
        website: "",
        location: "",
        company_size: "",
        hr_contact: "",
      },
      jobForm: {
        title: "",
        description: "",
        skills: "",
        experience: "",
        salary: "",
        location: "",
        job_type: "Full-time",
        application_deadline: "",
        min_cgpa: "",
        eligible_branches: "",
        eligible_years: "",
      },
      jobs: [],
    };
  },

  methods: {
    // strip anything that isn't a letter/space (plus basic name punctuation)
    // as the user types
    stripToLetters(value) {
      return value.replace(/[^A-Za-z\s.'&-]/g, "");
    },

    // strip anything that isn't a digit or a single decimal point
    stripToNumber(value) {
      let v = value.replace(/[^0-9.]/g, "");
      const dot = v.indexOf(".");
      if (dot !== -1) v = v.slice(0, dot + 1) + v.slice(dot + 1).replace(/\./g, "");
      return v;
    },

    // every filter forces e.target.value itself, not just the reactive
    // field behind it - if the filtered result happens to equal what the
    // field already held (e.g. typing a letter into an empty numbers-only
    // box filters back down to ""), Vue sees "no change" and skips
    // re-syncing the real <input>, leaving the bad character sitting there
    // visibly even though the stored value is correct. Setting el.value
    // directly guarantees the box itself always shows the filtered text.
    filterCompanyName(e) {
      const filtered = this.stripToLetters(e.target.value);
      e.target.value = filtered;
      this.profile.company_name = filtered;
    },
    filterIndustry(e) {
      const filtered = this.stripToLetters(e.target.value);
      e.target.value = filtered;
      this.profile.industry = filtered;
    },
    filterCompanyLocation(e) {
      const filtered = this.stripToLetters(e.target.value);
      e.target.value = filtered;
      this.profile.location = filtered;
    },
    filterCompanySize(e) {
      const filtered = this.stripToNumber(e.target.value);
      e.target.value = filtered;
      this.profile.company_size = filtered;
    },
    filterHrContact(e) {
      const filtered = e.target.value.replace(/[^0-9]/g, "").slice(0, 10);
      e.target.value = filtered;
      this.profile.hr_contact = filtered;
    },

    filterJobTitle(e) {
      const filtered = this.stripToLetters(e.target.value);
      e.target.value = filtered;
      this.jobForm.title = filtered;
    },
    filterJobLocation(e) {
      const filtered = this.stripToLetters(e.target.value);
      e.target.value = filtered;
      this.jobForm.location = filtered;
    },
    filterSalary(e) {
      const filtered = this.stripToNumber(e.target.value);
      e.target.value = filtered;
      this.jobForm.salary = filtered;
    },
    filterMinCgpa(e) {
      const filtered = this.stripToNumber(e.target.value);
      e.target.value = filtered;
      this.jobForm.min_cgpa = filtered;
    },

    // format checks only - fields the backend treats as optional stay
    // optional here too; a filled-in value just has to be the right shape
    validateProfileForm() {
      if (this.profile.company_name && !/^[A-Za-z\s.'&-]+$/.test(this.profile.company_name)) {
        alert("Company Name should contain only letters.");
        return false;
      }
      if (this.profile.industry && !/^[A-Za-z\s.'&-]+$/.test(this.profile.industry)) {
        alert("Industry should contain only letters.");
        return false;
      }
      if (this.profile.location && !/^[A-Za-z\s.'&-]+$/.test(this.profile.location)) {
        alert("Location should contain only letters.");
        return false;
      }
      if (this.profile.company_size && isNaN(Number(this.profile.company_size))) {
        alert("Company Size must be a number.");
        return false;
      }
      if (this.profile.hr_contact && this.profile.hr_contact.length !== 10) {
        alert("HR Contact number must be exactly 10 digits.");
        return false;
      }
      return true;
    },

    validateJobForm() {
      if (this.jobForm.title && !/^[A-Za-z\s.'&-]+$/.test(this.jobForm.title)) {
        alert("Job Title should contain only letters.");
        return false;
      }
      if (this.jobForm.location && !/^[A-Za-z\s.'&-]+$/.test(this.jobForm.location)) {
        alert("Job Location should contain only letters.");
        return false;
      }
      if (this.jobForm.salary && isNaN(Number(this.jobForm.salary))) {
        alert("Salary must be a number.");
        return false;
      }
      // eligibility criteria are compulsory so the eligibility filtering
      // feature always has something to filter students on
      if (this.jobForm.min_cgpa === "" || isNaN(Number(this.jobForm.min_cgpa))) {
        alert("Minimum CGPA is required and must be a number.");
        return false;
      }
      if (!this.jobForm.eligible_branches.trim()) {
        alert("Eligible Branches is required.");
        return false;
      }
      if (!this.jobForm.eligible_years.trim()) {
        alert("Eligible Years is required.");
        return false;
      }
      return true;
    },

    submitProfile() {
      if (!this.validateProfileForm()) return;
      const token = localStorage.getItem("token");

      api
        .post("/company/create_profile", this.profile, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then(() => {
          alert("Profile Created Successfully");
          this.showForm = false;
          this.fetch_company_profile();
        })
        .catch((err) => {
          alert(err.response?.data?.message || "Profile creation failed");
        });
    },

    editProfile() {
      if (!this.validateProfileForm()) return;
      const token = localStorage.getItem("token");

      api
        .post("/edit_company_profile", this.profile, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then(() => {
          alert("Profile Updated");
          this.showForm = false;
          this.fetch_company_profile();
        })
        .catch((err) => {
          alert(err.response?.data?.message || "Profile update failed");
        });
    },

    fetch_company_profile() {
      const token = localStorage.getItem("token");

      api
        .get("/get_company_profie", {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then((res) => {
          this.company_data = res.data;

          // pre-fill the edit form with the current values so editing
          // doesn't wipe out fields the user didn't retype
          this.profile = {
            company_name: res.data.company_name || "",
            industry: res.data.industry || "",
            website: res.data.website || "",
            location: res.data.location || "",
            company_size: res.data.company_size || "",
            hr_contact: res.data.hr_contact || "",
          };
        })
        .catch(() => {
          console.log("error getting profile");
        });
    },

    // the form can end up far from where the user clicked (e.g. "Edit" on
    // a job card lower down opens the form back up near the top) - scroll
    // it into view instead of leaving them to hunt for it. $nextTick
    // because the form only exists in the DOM after Vue re-renders for
    // showJobForm becoming true.
    scrollToJobForm() {
      this.$nextTick(() => {
        this.$refs.jobFormBox?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    },

    openJobForm() {
      // always start from a clean form, not whatever was left over
      // from the last job posted
      this.editingJobId = null;
      this.jobForm = {
        title: "",
        description: "",
        skills: "",
        experience: "",
        salary: "",
        location: "",
        job_type: "Full-time",
        application_deadline: "",
        min_cgpa: "",
        eligible_branches: "",
        eligible_years: "",
      };
      this.showJobForm = true;
      this.scrollToJobForm();
    },

    editJob(job) {
      this.editingJobId = job.id;
      this.jobForm = {
        title: job.title || "",
        description: job.description || "",
        skills: job.skills || "",
        experience: job.experience || "",
        salary: job.salary || "",
        location: job.location || "",
        job_type: job.job_type || "Full-time",
        // the backend sends dates as a full timestamp string, but the
        // <input type="date"> needs plain YYYY-MM-DD
        application_deadline: job.application_deadline
          ? new Date(job.application_deadline).toISOString().slice(0, 10)
          : "",
        min_cgpa: job.min_cgpa != null ? String(job.min_cgpa) : "",
        eligible_branches: job.eligible_branches || "",
        eligible_years: job.eligible_years || "",
      };
      this.showJobForm = true;
      this.scrollToJobForm();
    },

    postJob() {
      if (!this.validateJobForm()) return;
      const token = localStorage.getItem("token");

      api
        .post("/company/post_job", this.jobForm, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then(() => {
          alert("Job posted");
          this.showJobForm = false;
          this.fetchJobs();
        })
        .catch((err) => {
          alert(err.response?.data?.message || "Error posting job");
        });
    },

    updateJob() {
      if (!this.validateJobForm()) return;
      const token = localStorage.getItem("token");

      api
        .post(`/company/edit_job/${this.editingJobId}`, this.jobForm, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then(() => {
          alert("Job updated");
          this.showJobForm = false;
          this.editingJobId = null;
          this.fetchJobs();
        })
        .catch((err) => {
          alert(err.response?.data?.message || "Error updating job");
        });
    },

    fetchJobs() {
      const token = localStorage.getItem("token");

      api
        .get("/company/my_jobs", {
          headers: { Authorization: `Bearer ${token}` },
        })

        .then((res) => {
          this.jobs = res.data;
        })
        .catch(() => {
          console.log("error fetching jobs");
        });
    },

    closeJob(jobId) {
      const token = localStorage.getItem("token");

      if (!confirm("Are you sure you want to close this job?")) return;

      api
        .post(
          `/company/close_job/${jobId}`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        )
        .then(() => {
          alert("Job closed");
          this.fetchJobs();
        })
        .catch((err) => {
          alert(err.response?.data?.message || "Error closing job");
        });
    },

    openJob(jobId) {
      const token = localStorage.getItem("token");

      api
        .post(
          `/company/open_job/${jobId}`,
          {},
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        )
        .then(() => {
          alert("Job reopened");
          this.fetchJobs();
        })
        .catch((err) => {
          alert(err.response?.data?.message || "Error reopening job");
        });
    },
  },

  mounted() {
    this.fetch_company_profile();
    this.fetchJobs();
  },
};
</script>

<style>
.main-box {
  max-width: 600px;
  margin: auto;
  padding: 20px;
  min-height: 100vh;
  background-color: #f3e2d4;
}

.welcome-bar {
  background: white;
  border-left: 4px solid #c47a44;
  border-radius: 8px;
  padding: 10px 15px;
  margin-bottom: 20px;
  font-weight: bold;
  box-shadow: 0 1px 3px rgba(90, 56, 37, 0.1);
}

.section-box {
  background: white;
  border-left: 4px solid #8a9a5b;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(90, 56, 37, 0.1);
}

.section-box h3 {
  margin-top: 0;
  color: #5a3825;
}

.create-btn {
  background: #4caf50;
  color: white;
  padding: 8px 14px;
  margin: 10px 5px 10px 0;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.form-box {
  margin-top: 20px;
  background: white;
  border-left: 4px solid #c47a44;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 1px 3px rgba(90, 56, 37, 0.1);
}

.form-box h3 {
  margin-top: 0;
  color: #5a3825;
}

.form-box input {
  padding: 8px;
  border: 1px solid #d7b49e;
  border-radius: 6px;
  font-size: 14px;
}

.profile-box {
  margin-top: 20px;
  background: white;
  border-left: 4px solid #4a7a8c;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 1px 3px rgba(90, 56, 37, 0.1);
}

.profile-box h3 {
  margin-top: 0;
  color: #5a3825;
}

.form-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.primary-btn {
  background: #5a3825;
  color: white;
  padding: 8px 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.primary-btn:hover {
  background: #c47a44;
}

.cancel-btn {
  background: gray;
  color: white;
  padding: 8px 14px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.criteria-heading {
  font-size: 15px;
  color: #5a3825;
  margin: 4px 0;
}
</style>