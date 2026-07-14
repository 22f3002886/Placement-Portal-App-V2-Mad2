<template>
  <div class="main-box">
    <button class="back-btn" @click="$router.back()">← Back</button>

    <h2>Student Details</h2>

    <div v-if="data">
      <div class="profile-box">
        <p><b>Name:</b> {{ data.name }}</p>
        <p><b>Department:</b> {{ data.department }}</p>
        <p><b>CGPA:</b> {{ data.cgpa }}</p>
        <p><b>Total Applications:</b> {{ data.applications_count }}</p>
        <p><b>Email:</b> {{ data.email }}</p>
        <p><b>Phone:</b> {{ data.phone }}</p>
        <p><b>Year:</b> {{ data.year }}</p>
        <p><b>Skills:</b> {{ data.skills }}</p>
        <p><b>Placement Status:</b> {{ data.placement_status }}</p>
        <p><b>Account Active:</b> {{ data.is_active ? "Yes" : "Blocked" }}</p>
        <p><b>Joined On:</b> {{ data.created_at }}</p>
      </div>

      <h3>Applications</h3>

      <div v-if="data.applications.length === 0">No applications</div>

      <div v-for="app in data.applications" :key="app.job" class="info-card">
        <p><b>{{ app.job }}</b></p>
        <p>Company: {{ app.company }}</p>
        <p>Status: {{ app.status }}</p>
      </div>
    </div>

    <div v-else>Loading...</div>
  </div>
</template>

<script>
// Admin's view of one student: full profile plus their whole application
// history, so the admin can see where a student has applied without
// having to dig through the applications list.
import api from "../services/api";

export default {
  data() {
    return {
      data: null,
    };
  },

  methods: {
    getStudentDetails() {
      const token = localStorage.getItem("token");
      const id = this.$route.params.id;

      api
        .get(`/admin/student_details/${id}`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then((res) => {
          this.data = res.data;
        })
        .catch(() => {
          alert("Error loading student");
        });
    },
  },

  mounted() {
    this.getStudentDetails();
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

.back-btn {
  background: none;
  border: none;
  color: #2196f3;
  font-size: 15px;
  cursor: pointer;
  margin-bottom: 15px;
  padding: 0;
}
</style>