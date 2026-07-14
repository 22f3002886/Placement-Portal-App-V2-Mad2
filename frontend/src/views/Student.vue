<template>
  <div class="main-box">
    <div class="welcome-bar">
      <span>Welcome {{ user_name }}</span>
      <div class="top-links">
        <a @click="showProfileForm = true">edit profile</a> |
        <button
          class="btn btn-sm btn-success"
          @click="startExport"
          :disabled="exportLoading"
        >{{ exportLoading ? "Exporting..." : "Export CSV" }}</button>
      </div>
    </div>

    <div v-if="exportMessage" class="alert alert-info mt-3" role="alert">
      {{ exportMessage }}
      <a
        v-if="exportDownloadUrl"
        :href="exportDownloadUrl"
        class="alert-link ms-2"
        target="_blank"
      >Download file</a>
    </div>

    <!-- Edit Profile Form -->
    <div v-if="showProfileForm" class="form-box">
      <h3>{{ student_profile ? "Update Profile" : "Create Profile" }}</h3>

      <input :value="profileForm.department" @input="filterDepartment" placeholder="Department" />
      <input v-model="profileForm.year" placeholder="Passing Year (e.g. 2026)" type="number" />
      <input :value="profileForm.cgpa" @input="filterCgpa" placeholder="CGPA" inputmode="decimal" />
      <input v-model="profileForm.skills" placeholder="Skills (comma-separated)" />
      <input :value="profileForm.phone" @input="filterPhone" placeholder="Phone" inputmode="numeric" />

      <div class="form-actions">
        <button v-if="!student_profile" class="primary-btn" @click="submitProfile">Submit</button>
        <button v-if="student_profile" class="primary-btn" @click="updateProfile">Update Profile</button>
        <button class="cancel-btn" @click="showProfileForm = false">Cancel</button>
      </div>
    </div>

    <!-- Profile Display -->
    <div v-if="student_profile" class="profile-box">
      <h3>My Profile</h3>
      <p>
        <b>Name:</b>
        {{ user_name }}
      </p>
      <p>
        <b>Department:</b>
        {{ student_profile.department }}
      </p>
      <p>
        <b>Year:</b>
        {{ student_profile.year }}
      </p>
      <p>
        <b>CGPA:</b>
        {{ student_profile.cgpa }}
      </p>
      <p>
        <b>Skills:</b>
        {{ student_profile.skills }}
      </p>
      <p>
        <b>Placement Status:</b>
        {{ student_profile.placement_status }}
      </p>
      <p>
        <b>Phone:</b>
        {{ student_profile.phone }}
      </p>
      <p v-if="resumeLink">
        <b>Resume:</b>
        <a :href="resumeLink" target="_blank" class="link-btn">View Resume</a>
      </p>
    </div>

    <!-- Resume Upload -->
    <div class="section-box">
      <h3>Resume Upload</h3>
      <input type="file" class="form-control mb-2" @change="onResumeChange" />
      <button class="btn btn-primary btn-sm" @click="uploadResume">Upload Resume</button>
      <p v-if="resumeMessage" class="mt-2">{{ resumeMessage }}</p>
    </div>

    <!-- Organizations Section -->
    <div class="section-box">
      <h3>Companies</h3>

      <input
        v-model="companySearch"
        @input="fetchCompanies"
        class="form-control form-control-sm mb-2"
        placeholder="Search companies by name, industry or location..."
      />

      <div v-for="company in companies" :key="company.id" class="list-row">
        <span>{{ company.company_name }}</span>
        <button class="view-btn" @click="$router.push(`/company/${company.id}`)">view details</button>
      </div>

      <p v-if="companies.length === 0" class="empty-msg">No companies available.</p>
    </div>

    <!-- Available Drives Section -->
    <div class="section-box">
      <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <h3 class="mb-0">Available Placement Drives</h3>
        <div class="d-flex gap-2 flex-wrap align-items-center">
          <input
            v-model="driveSearch"
            @input="fetchAvailableJobs"
            class="form-control form-control-sm"
            placeholder="Search drives, skills, company..."
            style="min-width: 260px;"
          />
          <div class="form-check">
            <input
              id="eligibleOnly"
              v-model="eligibleOnly"
              class="form-check-input"
              type="checkbox"
            />
            <label class="form-check-label" for="eligibleOnly">Show eligible jobs only</label>
          </div>
        </div>
      </div>

      <div v-if="filteredJobs.length === 0" class="empty-msg">No approved drives found.</div>

      <div v-for="job in filteredJobs" :key="job.id" class="card mb-3 shadow-sm">
        <div class="card-body">
          <h5 class="card-title mb-1">
            {{ job.title }}
            <span v-if="job.is_eligible" class="badge bg-success ms-2">Eligible</span>
            <span v-else class="badge bg-secondary ms-2">Not eligible</span>
          </h5>
          <p class="card-text mb-2">{{ job.description }}</p>
          <div class="small text-muted mb-2">
            <div>
              <b>Company:</b>
              {{ job.company_name }}
            </div>
            <div>
              <b>Skills:</b>
              {{ job.skills }}
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
          </div>

          <button
            v-if="!hasApplied(job.id)"
            class="btn btn-sm btn-success"
            :disabled="!job.is_eligible"
            @click="applyToJob(job.id)"
          >Apply</button>
          <span v-else class="badge bg-secondary">✓ Applied</span>
        </div>
      </div>
    </div>

    <!-- Applied Drives Section -->
    <div class="section-box">
      <h3>Applied Drives</h3>

      <table v-if="applications.length > 0" class="drives-table">
        <thead>
          <tr>
            <th>Sr No.</th>
            <th>Drive Name</th>
            <th>Company</th>
            <th>Date</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(app, index) in applications" :key="app.id">
            <td>{{ index + 1 }}.</td>
            <td>{{ app.job_title }}</td>
            <td>{{ app.company_name }}</td>
            <td>{{ app.applied_at }}</td>
            <td>{{ app.status }}</td>
            <td>
              <button class="view-btn" @click="viewApplication(app)">view details</button>
            </td>
          </tr>
        </tbody>
      </table>

      <p v-if="applications.length === 0" class="empty-msg">No applications yet.</p>
    </div>

    <!-- Application Detail Modal -->
    <div v-if="selectedApplication" class="modal-overlay" @click.self="selectedApplication = null">
      <div class="modal-box">
        <div class="modal-header">
          <h3>Application Details</h3>
          <button class="close-btn" @click="selectedApplication = null">✕</button>
        </div>

        <p>
          <b>Job:</b>
          {{ selectedApplication.job_title }}
        </p>
        <p>
          <b>Company:</b>
          {{ selectedApplication.company_name }}
        </p>
        <p v-if="selectedApplication.job_type">
          <b>Job Type:</b>
          {{ selectedApplication.job_type }}
        </p>
        <p v-if="selectedApplication.job_location">
          <b>Job Location:</b>
          {{ selectedApplication.job_location }}
        </p>
        <p v-if="selectedApplication.is_job_closed !== null">
          <b>Job Status:</b>
          {{ selectedApplication.is_job_blacklisted ? "Blocked" : (selectedApplication.is_job_closed ? "Closed" : "Open") }}
        </p>
        <p>
          <b>Status:</b>
          {{ selectedApplication.status }}
        </p>
        <p>
          <b>Applied At:</b>
          {{ selectedApplication.applied_at }}
        </p>
        <p v-if="selectedApplication.remarks">
          <b>Remarks:</b>
          {{ selectedApplication.remarks }}
        </p>
        <p v-if="selectedApplication.interview_datetime">
          <b>Interview:</b>
          {{ selectedApplication.interview_datetime }}
        </p>
        <p v-if="selectedApplication.interview_mode">
          <b>Mode:</b>
          {{ selectedApplication.interview_mode }}
        </p>
        <p v-if="selectedApplication.interview_link">
          <b>Link:</b>
          {{ selectedApplication.interview_link }}
        </p>
        <p v-if="selectedApplication.interview_location">
          <b>Venue:</b>
          {{ selectedApplication.interview_location }}
        </p>
        <p v-if="selectedApplication.feedback">
          <b>Feedback:</b>
          {{ selectedApplication.feedback }}
        </p>
        <p v-if="selectedApplication.offer_letter">
          <b>Offer Letter:</b>
          <a :href="selectedApplication.offer_letter" target="_blank" class="link-btn">View Offer Letter</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
// Student's home page: profile + resume, browse companies and open drives,
// apply to the ones you're eligible for, and track every application you've
// made so far. The "eligible" badges are worked out by the backend, based
// on the CGPA/branch/year rules each drive sets.
import api from "../services/api";

export default {
  data() {
    return {
      user_name: "",
      showProfileForm: false,
      student_profile: null,
      profileForm: {
        department: "",
        year: "",
        cgpa: "",
        skills: "",
        phone: ""
      },
      companies: [],
      availableJobs: [],
      driveSearch: "",
      companySearch: "",
      eligibleOnly: false,
      applications: [],
      selectedApplication: null,
      resumeFile: null,
      resumeMessage: "",
      resumeLink: "",
      exportMessage: "",
      exportTaskId: "",
      exportDownloadUrl: "",
      exportLoading: false,
      exportPoller: null
    };
  },

  computed: {
    filteredJobs() {
      if (!this.eligibleOnly) {
        return this.availableJobs;
      }
      return this.availableJobs.filter(job => job.is_eligible);
    }
  },

  methods: {
    logout() {
      localStorage.removeItem("token");
      this.$router.push("/login");
    },

    // strip anything that isn't a letter/space (plus basic name punctuation)
    // as the user types, so fields like Department can't end up with digits
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
    filterDepartment(e) {
      const filtered = this.stripToLetters(e.target.value);
      e.target.value = filtered;
      this.profileForm.department = filtered;
    },

    filterCgpa(e) {
      const filtered = this.stripToNumber(e.target.value);
      e.target.value = filtered;
      this.profileForm.cgpa = filtered;
    },

    filterPhone(e) {
      const filtered = e.target.value.replace(/[^0-9]/g, "").slice(0, 10);
      e.target.value = filtered;
      this.profileForm.phone = filtered;
    },

    // format checks only - none of these fields are required by the
    // backend, so an empty value is left alone and only a filled-in
    // value that's the wrong shape blocks submission
    validateProfileForm() {
      if (this.profileForm.department && !/^[A-Za-z\s.'&-]+$/.test(this.profileForm.department)) {
        alert("Department should contain only letters.");
        return false;
      }
      if (this.profileForm.cgpa !== "" && isNaN(Number(this.profileForm.cgpa))) {
        alert("CGPA must be a number.");
        return false;
      }
      if (this.profileForm.phone && this.profileForm.phone.length !== 10) {
        alert("Phone number must be exactly 10 digits.");
        return false;
      }
      return true;
    },

    submitProfile() {
      if (!this.validateProfileForm()) return;
      const token = localStorage.getItem("token");

      api
        .post("/student/create_profile", this.profileForm, {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(() => {
          alert("Profile Created Successfully");
          this.showProfileForm = false;
          this.fetchStudentProfile();
        })
        .catch(err => {
          alert(err.response?.data?.message || "Profile creation failed");
        });
    },

    updateProfile() {
      if (!this.validateProfileForm()) return;
      const token = localStorage.getItem("token");

      api
        .post("/student/edit_profile", this.profileForm, {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(() => {
          alert("Profile Updated");
          this.showProfileForm = false;
          this.fetchStudentProfile();
          // eligibility depends on the profile we just changed, so
          // re-fetch the drives list instead of leaving stale tags showing
          this.fetchAvailableJobs();
        })
        .catch(err => {
          alert(err.response?.data?.message || "Update failed");
        });
    },

    fetchStudentProfile() {
      const token = localStorage.getItem("token");

      api
        .get("/student/get_profile", {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.student_profile = res.data;
          this.user_name = res.data.user_name || "";
          this.resumeLink = res.data.resume
            ? `${api.defaults.baseURL}/${res.data.resume}`
            : "";
          this.profileForm = {
            department: res.data.department || "",
            year: res.data.year || "",
            cgpa: res.data.cgpa || "",
            skills: res.data.skills || "",
            phone: res.data.phone || ""
          };
        })
        .catch(() => {
          console.log("No student profile found");
        });
    },

    fetchCompanies() {
      const token = localStorage.getItem("token");

      api
        .get(`/student/companies?q=${encodeURIComponent(this.companySearch)}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.companies = res.data;
        })
        .catch(() => {
          console.log("Error fetching companies");
        });
    },

    fetchAvailableJobs() {
      const token = localStorage.getItem("token");

      api
        .get(
          `/student/available_jobs?q=${encodeURIComponent(this.driveSearch)}`,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        .then(res => {
          this.availableJobs = res.data;
        })
        .catch(() => {
          console.log("Error fetching available jobs");
        });
    },

    fetchApplications() {
      const token = localStorage.getItem("token");

      api
        .get("/student/my_applications", {
          headers: { Authorization: `Bearer ${token}` }
        })
        .then(res => {
          this.applications = res.data;
        })
        .catch(() => {
          console.log("Error fetching applications");
        });
    },

    viewApplication(app) {
      this.selectedApplication = app;
    },

    hasApplied(jobId) {
      return this.applications.some(app => app.job_id === jobId);
    },

    applyToJob(jobId) {
      const token = localStorage.getItem("token");

      if (!confirm("Apply for this job?")) return;

      api
        .post(
          `/student/apply/${jobId}`,
          {},
          { headers: { Authorization: `Bearer ${token}` } }
        )
        .then(() => {
          alert("Applied successfully");
          this.fetchApplications();
        })
        .catch(err => {
          alert(err.response?.data?.message || "Error applying");
        });
    },

    onResumeChange(event) {
      this.resumeFile = event.target.files[0] || null;
    },

    uploadResume() {
      const token = localStorage.getItem("token");

      if (!this.resumeFile) {
        this.resumeMessage = "Please choose a resume file first.";
        return;
      }

      const formData = new FormData();
      formData.append("resume", this.resumeFile);

      api
        .post("/student/upload_resume", formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data"
          }
        })
        .then(res => {
          this.resumeMessage = res.data.message;
          this.resumeLink = res.data.resume_url;
          this.fetchStudentProfile();
        })
        .catch(err => {
          this.resumeMessage =
            err.response?.data?.message || "Resume upload failed.";
        });
    },

    startExport() {
      const token = localStorage.getItem("token");

      this.exportLoading = true;
      this.exportMessage = "Export started. Please wait...";
      this.exportDownloadUrl = "";

      api
        .post(
          "/student/export_applications",
          {},
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        .then(res => {
          this.exportTaskId = res.data.task_id;
          this.watchExportStatus();
        })
        .catch(() => {
          this.exportLoading = false;
          this.exportMessage = "Could not start export.";
        });
    },

    // the CSV export also runs on Celery in the background, so we poll
    // every 2 seconds and stop as soon as it's done (or fails)
    watchExportStatus() {
      const token = localStorage.getItem("token");

      if (this.exportPoller) {
        clearInterval(this.exportPoller);
      }

      this.exportPoller = setInterval(() => {
        api
          .get(`/student/export_applications/status/${this.exportTaskId}`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          .then(res => {
            if (res.data.state === "SUCCESS") {
              clearInterval(this.exportPoller);
              this.exportPoller = null;
              this.exportLoading = false;
              this.exportMessage = res.data.result.message || "Export ready.";
              this.exportDownloadUrl = res.data.result.download_url || "";
            }

            if (res.data.state === "FAILURE") {
              clearInterval(this.exportPoller);
              this.exportPoller = null;
              this.exportLoading = false;
              this.exportMessage = "Export failed.";
            }
          })
          .catch(() => {
            clearInterval(this.exportPoller);
            this.exportPoller = null;
            this.exportLoading = false;
            this.exportMessage = "Could not check export status.";
          });
      }, 2000);
    }
  },

  mounted() {
    this.fetchStudentProfile();
    this.fetchCompanies();
    this.fetchAvailableJobs();
    this.fetchApplications();
  }
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

.welcome-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  border-left: 4px solid #c47a44;
  border-radius: 8px;
  padding: 10px 15px;
  margin-bottom: 20px;
  font-weight: bold;
  box-shadow: 0 1px 3px rgba(90, 56, 37, 0.1);
}

.top-links a {
  color: #2196f3;
  cursor: pointer;
  font-weight: normal;
  font-size: 14px;
  margin: 0 2px;
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
  margin-bottom: 12px;
  color: #5a3825;
}

.list-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid #ddd;
  padding: 8px 12px;
  margin-bottom: 8px;
}

.drives-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.drives-table th,
.drives-table td {
  border: 1px solid #ddd;
  padding: 8px 10px;
  text-align: left;
}

.drives-table th {
  background: #f5f5f5;
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
  margin-bottom: 20px;
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
}

.profile-box {
  background: white;
  border-left: 4px solid #4a7a8c;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 20px;
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

.link-btn {
  display: inline-block;
  background: #2196f3;
  color: white;
  text-decoration: none;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.link-btn:hover {
  background: #1976d2;
  color: white;
}

.view-btn {
  background: #2196f3;
  color: white;
  border: none;
  padding: 6px 12px;
  cursor: pointer;
}

.view-btn:disabled {
  background: #aaa;
  cursor: not-allowed;
}

.empty-msg {
  color: #888;
  font-size: 14px;
}

/* Application modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 60px;
  z-index: 999;
}

.modal-box {
  background: white;
  width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  padding: 25px;
  border: 1px solid #e0c9b3;
  border-radius: 8px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: #555;
}
</style>