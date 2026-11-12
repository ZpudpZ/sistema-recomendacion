import axios from "axios";

const apiClient = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json"
  }
});

export async function checkHealth() {
  const response = await apiClient.get("/health");
  return response.data;
}

export async function getMetadata() {
  const response = await apiClient.get("/metadata");
  return response.data;
}

export async function getUserProfile(userId) {
  const response = await apiClient.get(`/users/${userId}/profile`);
  return response.data;
}

export async function getRecommendations(payload) {
  const response = await apiClient.post("/recommend", {
    user_id: Number(payload.user_id),
    alpha: Number(payload.alpha),
    top_n: Number(payload.top_n),
    k: Number(payload.k)
  });
  return response.data;
}

export async function runEvaluation(testSize) {
  const response = await apiClient.post("/evaluate", {
    test_size: Number(testSize)
  });
  return response.data;
}

export default apiClient;