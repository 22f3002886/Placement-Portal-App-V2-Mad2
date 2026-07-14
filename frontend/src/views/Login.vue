<template>
  <div class="page">
    <div class="box">
      <h2>Login</h2>

      <form @submit.prevent="loginUser">
        <label>Email</label>
        <input type="email" v-model="email" required />

        <label>Password</label>
        <input type="password" v-model="password" required />

        <button>Login</button>
      </form>

      <p class="link">
        New user?
        <router-link to="/register">Register</router-link>
      </p>
    </div>
  </div>
</template>

<script>
// Login form for all three roles. The backend tells us which role just
// logged in, and we send that person to their own dashboard.
import api from "../services/api";

export default {
  data() {
    return {
      email: "",
      password: ""
    };
  },

  methods: {
    loginUser() {
      if (!this.email || !this.password) {
        alert("Please enter email and password");
        return;
      }

      api.post("/login", {
        email: this.email,
        password: this.password
      })
      .then(response => {
        // the token goes in localStorage so the api.js interceptor can
        // attach it to every request from here on
        localStorage.setItem("token", response.data.token);
        localStorage.setItem("role", response.data.role);
        localStorage.setItem("name", response.data.name);

        if (response.data.role === "company") {
          this.$router.push("/company_dashboard");
        } else if (response.data.role === "student") {
          this.$router.push("/student-dashboard");
        } else if (response.data.role === "admin") {
          this.$router.push("/admin");
        }
      })
      .catch(error => {
        if (error.response && error.response.data) {
          alert(error.response.data.msg);

          // blocked by admin, or a company still waiting on approval —
          // either way they can't log in right now, so clear the form
          // instead of leaving the wrong-looking credentials sitting there
          const reason = error.response.data.reason;
          if (reason === "blocked" || reason === "pending_approval") {
            this.email = "";
            this.password = "";
          }
        }
        else {
          // server not running / network issue
          alert("Server not reachable. Is Flask running?");
        }
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

/* Login card */
.box {
  width: 380px;
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
  color: #5a3825;
  display: block;
  margin-top: 14px;
  font-size: 14px;
}

/* Inputs */
input {
  width: 100%;
  padding: 10px;
  margin-top: 6px;
  border-radius: 6px;
  border: 1px solid #d7b49e;
  font-size: 14px;
}

input:focus {
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