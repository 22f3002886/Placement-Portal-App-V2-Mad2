import { createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    component: () => import("./views/Landing.vue"),
  },
  {
    path: "/login",
    component: () => import("./views/Login.vue"),
  },
  {
    path: "/register",
    component: () => import("./views/Reg.vue"),
  },
  {
    path: "/company_dashboard",
    component: () => import("./views/Company.vue"),
    meta: { role: "company" },
  },
  {
    path: "/student-dashboard",
    component: () => import("./views/Student.vue"),
    meta: { role: "student" },
  },
  {
    path: "/company/:id",
    component: () => import("./views/CompanyDetail.vue"),
    meta: { role: "student" },
  },
  {
    path: "/job/:jobId/applicants",
    component: () => import("./views/ViewApplicant.vue"),
    meta: { role: "company" },
  },
  {
    path: "/admin",
    component: () => import("./views/Admin.vue"),
    meta: { role: "admin" },
  },
  {
    path: "/admin/company/:id",
    component: () => import("./views/CompanyDetailAdmin.vue"),
    meta: { role: "admin" },
  },
  {
    path: "/admin/student/:id",
    component: () => import("./views/StudentDetail.vue"),
    meta: { role: "admin" },
  },
  {
    path: "/admin/job/:id",
    component: () => import("./views/AdminJobDetail.vue"),
    meta: { role: "admin" },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  // without this, navigating to a new page keeps whatever scroll position
  // the previous page was at, so a new page can open looking like it's
  // scrolled to the middle instead of starting at the top
  scrollBehavior() {
    return { top: 0 };
  },
});

// route-level access control — a route with meta.role needs someone logged
// in with that exact role, otherwise send them to the login page instead of
// showing a blank/broken dashboard
router.beforeEach((to) => {
  if (!to.meta.role) {
    return true;
  }

  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");

  if (!token || role !== to.meta.role) {
    return "/login";
  }

  return true;
});

export default router;