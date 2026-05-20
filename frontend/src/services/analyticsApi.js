import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  timeout: 60000,
});

function buildQuery(filters = {}) {
  const params = new URLSearchParams();
  if (filters.startDate) params.set("start_date", filters.startDate);
  if (filters.endDate) params.set("end_date", filters.endDate);
  if (filters.course) params.set("course", filters.course);
  if (filters.datasetId) params.set("dataset_id", filters.datasetId);
  const text = params.toString();
  return text ? `?${text}` : "";
}

export function setAuthToken(token) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common.Authorization;
  }
}

export async function login(username, password) {
  const { data } = await api.post("/auth/login", { username, password });
  return data;
}

export async function fetchMe() {
  const { data } = await api.get("/auth/me");
  return data;
}

export async function fetchCourses(datasetId = null) {
  const q = datasetId ? `?dataset_id=${datasetId}` : "";
  const { data } = await api.get(`/analytics/courses${q}`);
  return data;
}

export async function fetchOverview(filters = {}) {
  const { data } = await api.get(`/analytics/overview${buildQuery(filters)}`);
  return data;
}

export async function fetchTrend(filters = {}) {
  const { data } = await api.get(`/analytics/engagement-trend${buildQuery(filters)}`);
  return data;
}

export async function fetchActivityBreakdown(filters = {}) {
  const { data } = await api.get(`/analytics/activity-breakdown${buildQuery(filters)}`);
  return data;
}

export async function fetchScoreDistribution(filters = {}) {
  const { data } = await api.get(`/analytics/score-distribution${buildQuery(filters)}`);
  return data;
}

export async function fetchAtRisk(limit = 8, filters = {}) {
  const query = buildQuery(filters);
  const joiner = query ? `${query}&` : "?";
  const { data } = await api.get(`/analytics/at-risk-students${joiner}limit=${limit}`);
  return data;
}

export async function fetchActiveDaysHistogram(filters = {}) {
  const { data } = await api.get(`/analytics/active-days-histogram${buildQuery(filters)}`);
  return data;
}

export async function fetchEngagementVsGrade(filters = {}) {
  const { data } = await api.get(`/analytics/engagement-vs-grade${buildQuery(filters)}`);
  return data;
}

export async function fetchAiInsights(filters = {}, provider = "groq") {
  const params = new URLSearchParams();
  params.set("provider", provider);
  if (filters.startDate) params.set("start_date", filters.startDate);
  if (filters.endDate) params.set("end_date", filters.endDate);
  if (filters.course) params.set("course", filters.course);
  if (filters.datasetId) params.set("dataset_id", filters.datasetId);
  const { data } = await api.get(`/analytics/ai-insights?${params.toString()}`);
  return data;
}

export async function fetchMlRisk(limit = 10, filters = {}) {
  const query = buildQuery(filters);
  const joiner = query ? `${query}&` : "?";
  const { data } = await api.get(`/analytics/ml-risk${joiner}limit=${limit}`);
  return data;
}

export async function fetchForecast(filters = {}) {
  const { data } = await api.get(`/analytics/forecast${buildQuery(filters)}`);
  return data;
}

export async function fetchAnomalies(filters = {}) {
  const { data } = await api.get(`/analytics/anomalies${buildQuery(filters)}`);
  return data;
}

export async function fetchStudentIds(datasetId = null) {
  const q = datasetId ? `?dataset_id=${datasetId}` : "";
  const { data } = await api.get(`/analytics/students${q}`);
  return data;
}

export async function fetchStudentDetail(studentId, datasetId = null) {
  const q = datasetId ? `?dataset_id=${datasetId}` : "";
  const { data } = await api.get(`/analytics/student/${encodeURIComponent(studentId)}${q}`);
  return data;
}

export async function fetchComparison(a, b, datasetId = null) {
  const params = new URLSearchParams({ a, b });
  if (datasetId) params.set("dataset_id", datasetId);
  const { data } = await api.get(`/analytics/compare?${params.toString()}`);
  return data;
}

export async function fetchHeatmap(datasetId = null) {
  const q = datasetId ? `?dataset_id=${datasetId}` : "";
  const { data } = await api.get(`/analytics/heatmap${q}`);
  return data;
}

export function exportDataUrl(fmt = "csv", filters = {}) {
  const params = new URLSearchParams({ fmt });
  if (filters.startDate) params.set("start_date", filters.startDate);
  if (filters.endDate) params.set("end_date", filters.endDate);
  if (filters.course) params.set("course", filters.course);
  if (filters.datasetId) params.set("dataset_id", filters.datasetId);
  return `${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}/analytics/export?${params.toString()}`;
}

export async function listDatasets() {
  const { data } = await api.get("/datasets/");
  return data;
}

export async function uploadDataset(name, file) {
  const form = new FormData();
  form.append("name", name);
  form.append("file", file);
  const { data } = await api.post(`/datasets/upload?name=${encodeURIComponent(name)}`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function addDatasetFromUrl(url, name) {
  const { data } = await api.post("/datasets/from-url", { url, name });
  return data;
}

export async function deleteDataset(datasetId) {
  const { data } = await api.delete(`/datasets/${datasetId}`);
  return data;
}

export async function addDatasetFromKaggle(datasetPath, name, kaggleUsername, kaggleKey) {
  const { data } = await api.post("/datasets/from-kaggle", {
    dataset_path: datasetPath,
    name,
    kaggle_username: kaggleUsername,
    kaggle_key: kaggleKey,
  });
  return data;
}

export async function validateDataset(datasetId) {
  const id = datasetId ?? "default";
  const { data } = await api.get(`/datasets/${id}/validate`);
  return data;
}

export async function register(username, password, email, role) {
  const { data } = await api.post("/auth/register", { username, password, email, role });
  return data;
}

export async function fetchAdminData() {
  const { data } = await api.get("/auth/admin-data");
  return data; // { users: [...], requests: [...] }
}

export async function fetchUsers() {
  const { data } = await api.get("/auth/users");
  return data;
}

export async function createUser(username, password, role) {
  const { data } = await api.post("/auth/users", { username, password, role });
  return data;
}

export async function updateUser(username, password, role) {
  const { data } = await api.put(`/auth/users/${encodeURIComponent(username)}`, { password, role });
  return data;
}

export async function deleteUser(username) {
  const { data } = await api.delete(`/auth/users/${encodeURIComponent(username)}`);
  return data;
}

export async function fetchRegistrationRequests(status = null) {
  const q = status ? `?status=${status}` : "";
  const { data } = await api.get(`/auth/registration-requests${q}`);
  return data;
}

export async function approveRequest(requestId) {
  const { data } = await api.post(`/auth/registration-requests/${requestId}/approve`);
  return data;
}

export async function declineRequest(requestId) {
  const { data } = await api.post(`/auth/registration-requests/${requestId}/decline`);
  return data;
}
