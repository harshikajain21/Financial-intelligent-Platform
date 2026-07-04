# create_dashboard.py

import os

files = {}

files["dashboard/src/App.js"] = """
import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { BarChart2, Search, BookMarked, Activity } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Analyze from './pages/Analyze';
import Watchlist from './pages/Watchlist';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <aside className="sidebar">
          <div className="logo">
            <Activity size={24} color="#00d4aa" />
            <span>FinIntel</span>
          </div>
          <nav className="nav">
            <NavLink to="/" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'} end>
              <BarChart2 size={18} />
              <span>Dashboard</span>
            </NavLink>
            <NavLink to="/analyze" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
              <Search size={18} />
              <span>Analyze</span>
            </NavLink>
            <NavLink to="/watchlist" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
              <BookMarked size={18} />
              <span>Watchlist</span>
            </NavLink>
          </nav>
          <div className="sidebar-footer">
            <span>Financial Intelligence Platform</span>
            <span>v0.1.0</span>
          </div>
        </aside>
        <main className="main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analyze" element={<Analyze />} />
            <Route path="/watchlist" element={<Watchlist />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
"""

files["dashboard/src/App.css"] = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e1e4e8; }
.app { display: flex; height: 100vh; overflow: hidden; }
.sidebar { width: 220px; background: #161b22; border-right: 1px solid #21262d; display: flex; flex-direction: column; padding: 20px 0; flex-shrink: 0; }
.logo { display: flex; align-items: center; gap: 10px; padding: 0 20px 30px; font-size: 18px; font-weight: 700; color: #fff; }
.nav { display: flex; flex-direction: column; gap: 4px; padding: 0 12px; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 10px 12px; border-radius: 8px; color: #8b949e; text-decoration: none; font-size: 14px; transition: all 0.2s; }
.nav-item:hover { background: #21262d; color: #e1e4e8; }
.nav-item.active { background: #1f3d2e; color: #00d4aa; }
.sidebar-footer { margin-top: auto; padding: 20px; font-size: 11px; color: #484f58; display: flex; flex-direction: column; gap: 2px; }
.main { flex: 1; overflow-y: auto; padding: 30px; }
.card { background: #161b22; border: 1px solid #21262d; border-radius: 12px; padding: 24px; margin-bottom: 20px; }
.card-title { font-size: 14px; color: #8b949e; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.5px; }
.badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; }
.badge-buy { background: #1f3d2e; color: #00d4aa; }
.badge-sell { background: #3d1f1f; color: #f85149; }
.badge-hold { background: #2d2a1f; color: #e3b341; }
.page-title { font-size: 24px; font-weight: 700; color: #fff; margin-bottom: 24px; }
.search-bar { display: flex; gap: 12px; margin-bottom: 24px; }
.search-input { flex: 1; background: #161b22; border: 1px solid #21262d; border-radius: 8px; padding: 12px 16px; color: #e1e4e8; font-size: 16px; outline: none; transition: border-color 0.2s; }
.search-input:focus { border-color: #00d4aa; }
.btn { padding: 12px 24px; border-radius: 8px; border: none; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.btn-primary { background: #00d4aa; color: #0f1117; }
.btn-primary:hover { background: #00bfa0; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { background: #3d1f1f; color: #f85149; border: 1px solid #f8514933; }
.btn-danger:hover { background: #4d2525; }
.score-bar-container { margin-bottom: 12px; }
.score-bar-label { display: flex; justify-content: space-between; font-size: 13px; color: #8b949e; margin-bottom: 4px; }
.score-bar-track { height: 6px; background: #21262d; border-radius: 3px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s ease; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.loading { display: flex; align-items: center; justify-content: center; padding: 60px; color: #8b949e; font-size: 14px; }
.error-msg { background: #3d1f1f; border: 1px solid #f8514933; border-radius: 8px; padding: 16px; color: #f85149; font-size: 14px; margin-bottom: 20px; }
.table { width: 100%; border-collapse: collapse; }
.table th { text-align: left; padding: 10px 12px; font-size: 12px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #21262d; }
.table td { padding: 12px; font-size: 14px; border-bottom: 1px solid #21262d22; color: #e1e4e8; }
.table tr:hover td { background: #21262d33; }
.confidence { font-size: 28px; font-weight: 700; color: #fff; }
.confidence-label { font-size: 12px; color: #8b949e; margin-top: 4px; }
"""

files["dashboard/src/api.js"] = """
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
"""

files["dashboard/src/pages/Dashboard.js"] = """
import React, { useState, useEffect } from 'react';
import { getDashboard } from '../api';

function getBadgeClass(d) {
  if (d === 'BUY') return 'badge badge-buy';
  if (d === 'SELL') return 'badge badge-sell';
  return 'badge badge-hold';
}

function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getDashboard()
      .then(res => setData(res.data))
      .catch(() => setError('Failed to load dashboard'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error) return <div className="error-msg">{error}</div>;

  return (
    <div>
      <h1 className="page-title">Dashboard</h1>
      <div className="card">
        <div className="card-title">Recent Analyses</div>
        {!data?.results?.length ? (
          <p style={{ color: '#8b949e', fontSize: 14 }}>No analyses yet. Go to Analyze to run your first one.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Decision</th>
                <th>Confidence</th>
                <th>Price</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {data.results.map(r => (
                <tr key={r.id}>
                  <td><strong>{r.symbol}</strong></td>
                  <td><span className={getBadgeClass(r.final_decision)}>{r.final_decision}</span></td>
                  <td>{r.confidence?.toFixed(1)}%</td>
                  <td>${r.close_price?.toFixed(2)}</td>
                  <td style={{ color: '#8b949e', fontSize: 12 }}>{new Date(r.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
"""

files["dashboard/src/pages/Analyze.js"] = """
import React, { useState } from 'react';
import { analyzeStock, addToWatchlist } from '../api';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts';

function getBadgeClass(d) {
  if (d === 'BUY') return 'badge badge-buy';
  if (d === 'SELL') return 'badge badge-sell';
  return 'badge badge-hold';
}

function getColor(score) {
  if (score >= 20) return '#00d4aa';
  if (score <= -20) return '#f85149';
  return '#e3b341';
}

function ScoreBar({ name, score }) {
  const pct = Math.min(Math.abs(score), 100);
  const color = getColor(score);
  const label = name.replace('Agent','').replace('Intelligence','').replace('Analysis','').trim();
  return (
    <div className="score-bar-container">
      <div className="score-bar-label">
        <span>{label}</span>
        <span style={{ color }}>{score?.toFixed(1)}</span>
      </div>
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: pct + '%', background: color }} />
      </div>
    </div>
  );
}

function Analyze() {
  const [symbol, setSymbol] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);

  const handleAnalyze = async () => {
    if (!symbol.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setSaved(false);
    try {
      const res = await analyzeStock(symbol.trim().toUpperCase());
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddWatchlist = async () => {
    try {
      await addToWatchlist(result.symbol);
      setSaved(true);
    } catch { }
  };

  const radarData = result ? Object.entries(result.scores).map(([key, val]) => ({
    subject: key.replace('Agent','').replace('Intelligence','').replace('Analysis','').trim(),
    score: Math.max(val + 100, 0),
    fullMark: 200,
  })) : [];

  return (
    <div>
      <h1 className="page-title">Analyze Stock</h1>
      <div className="search-bar">
        <input
          className="search-input"
          placeholder="Enter stock symbol e.g. AAPL, TSLA, MSFT"
          value={symbol}
          onChange={e => setSymbol(e.target.value.toUpperCase())}
          onKeyDown={e => e.key === 'Enter' && handleAnalyze()}
        />
        <button className="btn btn-primary" onClick={handleAnalyze} disabled={loading || !symbol.trim()}>
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {loading && <div className="loading">Running 9 agents... this takes 15-30 seconds</div>}
      {error && <div className="error-msg">{error}</div>}

      {result && (
        <>
          <div className="card" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 48, fontWeight: 700, color: '#fff', marginBottom: 8 }}>{result.symbol}</div>
            <span className={getBadgeClass(result.final_decision)} style={{ fontSize: 20, padding: '8px 24px' }}>
              {result.final_decision}
            </span>
            <div style={{ marginTop: 16 }}>
              <div className="confidence">{result.confidence?.toFixed(1)}%</div>
              <div className="confidence-label">Confidence</div>
            </div>
            <p style={{ marginTop: 16, color: '#8b949e', fontSize: 14, maxWidth: 500, margin: '16px auto 0' }}>
              {result.recommendation}
            </p>
            <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={handleAddWatchlist} disabled={saved}>
              {saved ? 'Added to Watchlist' : '+ Add to Watchlist'}
            </button>
          </div>

          <div className="grid-2">
            <div className="card">
              <div className="card-title">Agent Scores</div>
              {Object.entries(result.scores).map(([name, score]) => (
                <ScoreBar key={name} name={name} score={score} />
              ))}
            </div>
            <div className="card">
              <div className="card-title">Score Radar</div>
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#21262d" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#8b949e', fontSize: 11 }} />
                  <Radar dataKey="score" stroke="#00d4aa" fill="#00d4aa" fillOpacity={0.2} />
                  <Tooltip formatter={(val) => [(val - 100).toFixed(1), 'Score']} contentStyle={{ background: '#161b22', border: '1px solid #21262d', borderRadius: 8 }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {result.errors?.length > 0 && (
            <div className="card">
              <div className="card-title">Failed Agents</div>
              <p style={{ color: '#f85149', fontSize: 14 }}>{result.errors.join(', ')}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Analyze;
"""

files["dashboard/src/pages/Watchlist.js"] = """
import React, { useState, useEffect } from 'react';
import { getWatchlist, removeFromWatchlist, analyzeStock } from '../api';

function Watchlist() {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(null);

  const fetchWatchlist = () => {
    getWatchlist()
      .then(res => setWatchlist(res.data.watchlist || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchWatchlist(); }, []);

  const handleRemove = async (symbol) => {
    await removeFromWatchlist(symbol);
    fetchWatchlist();
  };

  const handleAnalyze = async (symbol) => {
    setAnalyzing(symbol);
    try {
      await analyzeStock(symbol);
      alert('Analysis complete for ' + symbol + '. Check Dashboard for results.');
    } catch {
      alert('Analysis failed for ' + symbol);
    } finally {
      setAnalyzing(null);
    }
  };

  if (loading) return <div className="loading">Loading watchlist...</div>;

  return (
    <div>
      <h1 className="page-title">Watchlist</h1>
      <div className="card">
        {!watchlist.length ? (
          <p style={{ color: '#8b949e', fontSize: 14 }}>Watchlist is empty. Analyze a stock and click Add to Watchlist.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Added</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {watchlist.map(item => (
                <tr key={item.id}>
                  <td><strong>{item.symbol}</strong></td>
                  <td style={{ color: '#8b949e', fontSize: 12 }}>{new Date(item.added_at).toLocaleDateString()}</td>
                  <td style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-primary" style={{ padding: '6px 14px', fontSize: 12 }} onClick={() => handleAnalyze(item.symbol)} disabled={analyzing === item.symbol}>
                      {analyzing === item.symbol ? 'Running...' : 'Analyze'}
                    </button>
                    <button className="btn btn-danger" style={{ padding: '6px 14px', fontSize: 12 }} onClick={() => handleRemove(item.symbol)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Watchlist;
"""

# Create pages directory
os.makedirs("dashboard/src/pages", exist_ok=True)

# Write all files
for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Written: {path}")

print("\nAll files written successfully!")