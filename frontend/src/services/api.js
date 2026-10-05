import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

/**
 * Fetch candidates with pagination and filters
 * GET /candidates?page=1&limit=20&skill=Python&location=Bangalore&min_experience=3
 */
export const fetchCandidates = async (params = {}) => {
  const queryParams = new URLSearchParams();
  
  if (params.page) queryParams.append('page', params.page);
  if (params.limit) queryParams.append('limit', params.limit);
  if (params.skill && params.skill.trim()) queryParams.append('skill', params.skill.trim());
  if (params.location && params.location.trim()) queryParams.append('location', params.location.trim());
  if (params.min_experience !== undefined && params.min_experience !== null && params.min_experience !== '') {
    queryParams.append('min_experience', params.min_experience);
  }

  const response = await apiClient.get(`/candidates?${queryParams.toString()}`);
  return response.data;
};

/**
 * Fetch candidate details by ID
 * GET /candidates/{candidate_id}
 */
export const fetchCandidateById = async (candidateId) => {
  const response = await apiClient.get(`/candidates/${candidateId}`);
  return response.data;
};

/**
 * Search candidates using natural language query & filters via OpenSearch Hybrid & Ranking
 * POST /search/opensearch?rank=true
 */
export const searchCandidates = async ({ query, page = 1, limit = 20, filters = {} }) => {
  const response = await apiClient.post('/search/opensearch?rank=true', {
    query,
    page,
    limit,
    filters,
  });
  return response.data;
};

/**
 * Fetch dashboard analytics overview metrics
 * GET /analytics/dashboard
 */
export const fetchDashboardAnalytics = async () => {
  try {
    const response = await apiClient.get('/analytics/dashboard');
    return response.data;
  } catch (error) {
    console.error('Error fetching dashboard analytics:', error);
    return null;
  }
};

/**
 * Check backend health status
 * GET /health
 */
export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    return { status: 'offline' };
  }
};

