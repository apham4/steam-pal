import axios from 'axios';

// Create an Axios instance configured for our API
const apiClient = axios.create({
  baseURL: 'http://localhost:8000', // The address of your FastAPI server
  headers: {
    'Content-Type': 'application/json',
  },
});

// Export functions that map to our API endpoints
export default {
  getNewRecommendation(filters) {
    return apiClient.post('/api/recommendations', filters);
  },
  getCurrentUser() {
    return apiClient.get('/api/me');
  },
};