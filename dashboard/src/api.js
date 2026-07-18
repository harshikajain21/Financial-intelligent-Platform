import axios from 'axios';

const api = axios.create({
  baseURL: 'https://financial-ntelligent-platform.onrender.com/api/v1',
  timeout: 120000,
});

export const searchStocks = (query) => api.get('/search?query=' + query);
export const analyzeStock = (symbol, exchange = 'NSE') =>
  api.post('/analyze/' + symbol + '?exchange=' + exchange);
export const getHistory = (symbol, limit = 10) =>
  api.get('/history/' + symbol + '?limit=' + limit);
export const getDashboard = () => api.get('/dashboard');
export const addToWatchlist = (symbol) => api.post('/watchlist/' + symbol);
export const getWatchlist = () => api.get('/watchlist');
export const removeFromWatchlist = (symbol) => api.delete('/watchlist/' + symbol);
export default api;

export const startAsyncAnalysis = (symbol, exchange = 'NSE') =>
  api.post('/analyze/async/' + symbol + '?exchange=' + exchange);

export const getJobStatus = (jobId) =>
  api.get('/jobs/' + jobId);