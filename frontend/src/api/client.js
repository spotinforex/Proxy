import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WEBHOOK_TOKEN = import.meta.env.VITE_WEBHOOK_TOKEN;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${WEBHOOK_TOKEN}`,
  },
});

export const setAuthToken = (token) => {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    localStorage.setItem('auth_token', token);
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
    localStorage.removeItem('auth_token');
  }
};

const storedToken = localStorage.getItem('auth_token');
if (storedToken) {
  setAuthToken(storedToken);
}

export const pipelineAPI = {
  getDataFeed: () => apiClient.get('/api/pipeline/data'),
  generateReport: () => apiClient.post('/api/pipeline/report'),
  generateFilteredReport: (filters) => apiClient.post('/api/pipeline/report/filtered', filters),
};

export default apiClient;
