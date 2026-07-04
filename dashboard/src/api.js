import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 60000,
});

export const analyzeStock = (symbol) => api.post('/analyze/' + symbol);
export const getHistory = (symbol, limit = 10) => api.get('/history/' + symbol + '?limit=' + limit);
export const getDashboard = () => api.get('/dashboard');
export const addToWatchlist = (symbol) => api.post('/watchlist/' + symbol);
export const getWatchlist = () => api.get('/watchlist');
export const removeFromWatchlist = (symbol) => api.delete('/watchlist/' + symbol);
export default api;