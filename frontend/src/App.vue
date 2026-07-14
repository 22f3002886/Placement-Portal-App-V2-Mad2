<template>
  <div class="main">
    <!-- Navbar -->
    <nav class="navbar">
      <div class="logo">Placement Portal</div>

      <div class="nav-links">
        <router-link to="/">Home</router-link>
        <div v-if="!loggedIn">
          <router-link to="/login" class="nav-btn">Login</router-link>
          <router-link to="/register" class="nav-btn">Register</router-link>
        </div>
        <div v-if="loggedIn">
          <button class="nav-btn" @click="logout">Logout</button>
        </div>
      </div>
    </nav>

    <!-- Page Content -->
    <router-view />
  </div>
</template>

<script>
export default {
  name: "App",

  data() {
    return {
      // read once on load, then kept in sync by the route watcher below —
      // localStorage changes aren't reactive on their own, so without this
      // the navbar wouldn't update right after login/logout
      loggedIn: !!localStorage.getItem("token"),
    };
  },

  watch: {
    $route() {
      this.loggedIn = !!localStorage.getItem("token");
    },
  },

  methods: {
    logout() {
      localStorage.removeItem("token");
      localStorage.removeItem("role");
      localStorage.removeItem("name");
      this.loggedIn = false;
      this.$router.push("/login");
    },
  },
};
</script>

<style>
.main {
  margin: 0;
  font-family: Arial;
  background-color: #f3e2d4;
}

/* Navbar */
.navbar {
  background-color: #5a3825;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  padding: 15px 30px;
}

.logo {
  font-size: 15px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.nav-links > div {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-links a {
  text-decoration: none;
  color: white;
}

.nav-btn {
  background-color: #c47a44;
  padding: 6px 12px;
  border-radius: 4px;
}

/* Router active link */
.router-link-active {
  font-weight: bold;
}
</style>