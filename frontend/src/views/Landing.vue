<template>
  <div class="main">

    <!-- Header -->
    <div class="header">
      <h1>Placement Portal</h1>
      <p>Empowering Students for Better Careers</p>
    </div>

    <!-- About Section -->
    <div class="card-section about">
      <h2>About Us</h2>
      <p>
        Our Placement Cell organizes campus drives, career guidance sessions,
        aptitude training, and interview preparation programs. Every year,
        hundreds of students get placed in reputed companies.
      </p>
    </div>

    <!-- Companies -->
    <div class="card-section companies">
      <h2>Top Recruiting Companies</h2>

      <div class="company-list">
        <div class="company-tile">ABC Technologies</div>
        <div class="company-tile">FutureSoft Pvt Ltd</div>
        <div class="company-tile">NextGen Solutions</div>
      </div>
    </div>

    <!-- Stats -->
    <div class="card-section stats">
      <h2>Placement Statistics</h2>

      <div class="stats-grid">
        <div class="stat-tile">
          <span class="stat-number">320+</span>
          <span class="stat-label">Students Placed</span>
        </div>
        <div class="stat-tile">
          <span class="stat-number">12 LPA</span>
          <span class="stat-label">Highest Package</span>
        </div>
        <div class="stat-tile">
          <span class="stat-number">5.5 LPA</span>
          <span class="stat-label">Average Package</span>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="footer">
      © 2026 Placement Portal | All Rights Reserved
    </div>

  </div>
</template>

<script>
export default {
  name: "Landing"
}
</script>

<style>
.main {
  margin: 0;
  min-height: 100vh;
  font-family: Arial;
  background-color: #f3e2d4;
}

.header {
  background-color: #5a3825;
  color: white;
  text-align: center;
  padding: 40px 20px;
}

.header h1 {
  margin: 0 0 8px 0;
}

.header p {
  margin: 0;
  opacity: 0.9;
}

.card-section {
  max-width: 900px;
  margin: 24px auto;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(90, 56, 37, 0.1);
}

.card-section h2 {
  margin-top: 0;
  color: #5a3825;
}

.about {
  border-left: 4px solid #c47a44;
}

.about p {
  line-height: 1.6;
  color: #444;
}

.companies {
  border-left: 4px solid #8a9a5b;
  text-align: center;
}

.company-list {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.company-tile {
  background: #f3e2d4;
  color: #5a3825;
  font-weight: bold;
  padding: 20px 24px;
  border-radius: 8px;
  min-width: 160px;
}

.stats {
  border-left: 4px solid #4a7a8c;
  text-align: center;
}

.stats-grid {
  display: flex;
  justify-content: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.stat-tile {
  background: #f3e2d4;
  padding: 16px 24px;
  border-radius: 8px;
  min-width: 140px;
}

.stat-number {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: #5a3825;
}

.stat-label {
  display: block;
  font-size: 13px;
  color: #7a5a45;
  margin-top: 4px;
}

.footer {
  background-color: #5a3825;
  color: white;
  text-align: center;
  padding: 15px;
}
</style>
