<template>
  <div class="main-box">
    <button class="back-btn" @click="$router.back()">← Back</button>

    <h2>Applicants</h2>

    <div v-if="applicants.length === 0">
      No applicants yet 😴
    </div>

    <!-- Applicants List -->
    <div
      v-for="app in applicants"
      :key="app.application_id"
      class="info-card"
    >
      <p><b>Name:</b> {{ app.name }}</p>
      <p><b>Email:</b> {{ app.email }}</p>
      <p><b>Phone:</b> {{ app.phone }}</p>
      <p><b>Skills:</b> {{ app.skills }}</p>
      <p><b>CGPA:</b> {{ app.cgpa }}</p>
      <p><b>Status:</b> {{ app.status }}</p>

      <a :href="app.resume" target="_blank" class="link-btn">View Resume</a>

      <!-- Interview Details -->
      <div v-if="app.status === 'Shortlisted' && app.interview_datetime" class="mt-3">
        <p>
          <b>Interview Date:</b>
          {{ formatDate(app.interview_datetime) }}
        </p>

        <p>
          <b>Interview Link:</b>
        </p>
        <a :href="app.interview_link" target="_blank" class="link-btn">
          Join Interview
        </a>
      </div>

      <!-- Offer Letter -->
      <div v-if="app.status === 'Selected' && app.offer_letter" class="mt-3">
        <p><b>Offer Letter:</b></p>
        <a :href="app.offer_letter" target="_blank" class="link-btn">
          View Offer Letter
        </a>
      </div>

      <!-- Action Buttons -->
      <div class="mt-3 action-buttons">
        <button
          @click="openShortlist(app)"
          :disabled="app.status === 'Selected'"
        >
          Shortlist
        </button>

        <button
          @click="openReject(app)"
          :disabled="app.status === 'Selected'"
        >
          Reject
        </button>

        <button
          @click="openSelect(app)"
          :disabled="app.status === 'Selected'"
        >
          Select
        </button>
      </div>
    </div>

    <!-- MODAL -->
    <div v-if="showModal" class="modal">
      <div class="modal-content">
        <h3>{{ modalTitle }}</h3>

        <!-- Shortlist -->
        <div v-if="actionType === 'shortlist'" class="modal-fields">
          <input
            type="datetime-local"
            v-model="form.interview_datetime"
          />
          <input
            type="text"
            placeholder="Meet Link"
            v-model="form.interview_link"
          />
        </div>

        <!-- Reject -->
        <div v-if="actionType === 'reject'" class="modal-fields">
          <textarea
            placeholder="Provide feedback..."
            v-model="form.feedback"
          ></textarea>
        </div>

        <!-- Select -->
        <div v-if="actionType === 'select'" class="modal-fields">
          <input type="file" @change="handleFileUpload" />
        </div>

        <div class="modal-actions">
          <button @click="submitAction">Submit</button>
          <button class="cancel-btn" @click="closeModal">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// Shows everyone who applied to one specific drive. A company can shortlist
// (with an interview time + link), reject (with feedback), or select
// (with an offer letter) each applicant — the modal below just swaps out
// which fields it shows based on which of those three buttons was clicked.
import api from "../services/api";

export default {
  data() {
    return {
      applicants: [],
      showModal: false,
      actionType: "",
      selectedApp: null,
      modalTitle: "",
      form: {
        interview_datetime: "",
        interview_link: "",
        feedback: "",
        offer_letter: null,
      },
    };
  },

  methods: {
    formatDate(date) {
      if (!date) return "";

      const d = new Date(date);

      return d.toLocaleString("en-IN", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    },

    fetchApplicants() {
      const token = localStorage.getItem("token");
      const jobId = this.$route.params.jobId;

      api
        .get(`/company/job/${jobId}/applicants`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then((res) => {
          this.applicants = res.data;
        })
        .catch(() => {
          alert("Error fetching applicants");
        });
    },

    openShortlist(app) {
      this.actionType = "shortlist";
      this.modalTitle = "Schedule Interview";
      this.selectedApp = app;
      this.showModal = true;
    },

    openReject(app) {
      this.actionType = "reject";
      this.modalTitle = "Provide Feedback";
      this.selectedApp = app;
      this.showModal = true;
    },

    openSelect(app) {
      this.actionType = "select";
      this.modalTitle = "Upload Offer Letter";
      this.selectedApp = app;
      this.showModal = true;
    },

    closeModal() {
      this.showModal = false;
      this.resetForm();
    },

    resetForm() {
      this.form = {
        interview_datetime: "",
        interview_link: "",
        feedback: "",
        offer_letter: null,
      };
    },

    handleFileUpload(e) {
      this.form.offer_letter = e.target.files[0];
    },

    submitAction() {
      const token = localStorage.getItem("token");
      const id = this.selectedApp.application_id;

      if (this.actionType === "select" && !this.form.offer_letter) {
        alert("Please choose an offer letter file before submitting.");
        return;
      }

      // actionType is just the internal modal state name — the backend
      // stores the full, capitalized status word
      const statusLabels = {
        shortlist: "Shortlisted",
        reject: "Rejected",
        select: "Selected",
      };
      const status = statusLabels[this.actionType];

      const formData = new FormData();
      formData.append("status", status);

      if (this.actionType === "shortlist") {
        formData.append("interview_datetime", this.form.interview_datetime);
        formData.append("interview_link", this.form.interview_link);
      }

      if (this.actionType === "reject") {
        formData.append("feedback", this.form.feedback);
      }

      if (this.actionType === "select") {
        formData.append("offer_letter", this.form.offer_letter);
      }

      api
        .put(`/company/application/${id}/status`, formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "multipart/form-data",
          },
        })
        .then(() => {
          this.selectedApp.status = status;
          this.fetchApplicants();
          this.closeModal();
        })
        .catch(() => {
          alert("Update failed");
        });
    },
  },

  mounted() {
    this.fetchApplicants();
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

.info-card {
  background: white;
  border-left: 4px solid #8a9a5b;
  border-radius: 8px;
  padding: 15px;
  margin: 12px 0;
  box-shadow: 0 1px 3px rgba(90, 56, 37, 0.1);
}

.info-card p {
  margin: 6px 0;
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

.action-buttons {
  display: flex;
  gap: 8px;
}

button {
  padding: 5px 12px;
  border: none;
  border-radius: 6px;
  background: #5a3825;
  color: white;
  cursor: pointer;
  font-size: 13px;
}

button:hover:not(:disabled) {
  background: #c47a44;
}

button:disabled {
  background: #ccc;
  color: #666;
  cursor: not-allowed;
}

/* Modal */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content {
  background: white;
  padding: 24px;
  width: 400px;
  max-width: 90vw;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal-content h3 {
  margin: 0;
  color: #5a3825;
}

.modal-fields {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.modal-fields input,
.modal-fields textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #d7b49e;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
}

.modal-fields textarea {
  min-height: 80px;
  resize: vertical;
}

.modal-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.cancel-btn {
  background: gray;
}
</style>