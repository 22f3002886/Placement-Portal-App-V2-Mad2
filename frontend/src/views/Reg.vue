<template>
  <div class="page">
    <div class="box">
      <h2>Register</h2>

      <form @submit.prevent="registerUser">
        <label>Name</label>
        <input v-model="name" required />

        <label>Email</label>
        <input type="email" v-model="email" required />

        <label>Password</label>
        <input type="password" v-model="password" required />

        <label>Role</label>
        <select v-model="role" required>
          <option value="">Select</option>
          <option value="student">Student</option>
          <option value="company">Company</option>
        </select>

        <button>Register</button>
      </form>

      <p class="link">
        Already have an account?
        <router-link to="/login">Login</router-link>
      </p>
    </div>
  </div>
</template>

<script>
// Sign-up form for students and companies. Admin has no sign-up page —
// that one account is created straight in the database on first run.
import api from "../services/api";

export default {
  data() {
    return {
      name: "",
      email: "",
      password: "",
      role: ""
    };
  },

  methods: {
    registerUser() {
      api.post("/register", {
        name: this.name,
        email: this.email,
        password: this.password,
        role: this.role
      })
      .then(() => {
        alert("Registration successful. Please login.");
        this.$router.push("/login");
      })
      .catch(err => {
        alert(err.response?.data?.message || "Registration failed. Is the server running?");
      });
    }
  }
};
</script>

<style scoped>
/* Full screen background */
.page {
  min-height: 100vh;
  width: 100%;
  background-color: #f3e2d4;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Register card */
.box {
  width: 400px;
  background: #ffffff;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 8px 20px rgba(90, 56, 37, 0.2);
  border-top: 6px solid #c47a44;
  font-family: Arial, sans-serif;
}

/* Title */
h2 {
  text-align: center;
  margin-bottom: 24px;
  color: #5a3825;
}

/* Labels */
label {
  display: block;
  margin-top: 14px;
  font-size: 14px;
  color: #5a3825;
}

/* Inputs & Select */
input,
select {
  width: 100%;
  padding: 10px;
  margin-top: 6px;
  border-radius: 6px;
  border: 1px solid #d7b49e;
  font-size: 14px;
  background: white;
}

input:focus,
select:focus {
  outline: none;
  border-color: #c47a44;
}

/* Button */
button {
  width: 100%;
  margin-top: 24px;
  padding: 10px;
  background-color: #5a3825;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

button:hover {
  background-color: #c47a44;
}

/* Link */
.link {
  margin-top: 18px;
  text-align: center;
  font-size: 14px;
  color: #5a3825;
}

.link a {
  color: #c47a44;
  text-decoration: none;
}

.link a:hover {
  text-decoration: underline;
}
</style>