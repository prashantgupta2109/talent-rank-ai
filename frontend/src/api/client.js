import axios from 'axios';

const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export const parseJobDirect = async (rawText) => {
  const res = await api.post('/api/v1/jobs/parse', { raw_text: rawText });
  return res.data;
};

export const createJob = async (rawText, title = '') => {
  const res = await api.post('/jobs/', { raw_text: rawText, title });
  return res.data;
};

export const getJobById = async (jobId) => {
  const res = await api.get(`/jobs/${jobId}`);
  return res.data;
};

export const uploadJobResumes = async (jobId, files, onUploadProgress) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const res = await axios.post(`${API_BASE}/jobs/${jobId}/resumes`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress,
  });
  return res.data;
};

export const triggerJobMatch = async (jobId) => {
  const res = await api.post(`/jobs/${jobId}/match`);
  return res.data;
};

export const getJobRankings = async (jobId) => {
  const res = await api.get(`/jobs/${jobId}/rankings`);
  return res.data;
};

export const getCandidateDetail = async (candidateId) => {
  const res = await api.get(`/candidates/${candidateId}`);
  return res.data;
};

export default api;
