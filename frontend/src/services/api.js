import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:5000",
});

// attaches the saved login token to every request automatically, so we
// don't have to pass the Authorization header by hand in every component
api.interceptors.request.use(config => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
