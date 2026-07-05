# update_dashboard.py

import os

os.makedirs("dashboard/src/pages", exist_ok=True)
os.makedirs("dashboard/src/components", exist_ok=True)

files = {}

# ── api.js ──────────────────────────────────────────────────────
files["dashboard/src/api.js"] = """
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 60000,
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
"""

# ── SearchBar component ─────────────────────────────────────────
files["dashboard/src/components/SearchBar.js"] = """
import React, { useState, useEffect, useRef } from 'react';
import { searchStocks } from '../api';

function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [exchange, setExchange] = useState('NSE');
  const [showDrop, setShowDrop] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (query.length < 2) { setSuggestions([]); return; }
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      searchStocks(query)
        .then(res => { setSuggestions(res.data.results || []); setShowDrop(true); })
        .catch(() => setSuggestions([]));
    }, 300);
  }, [query]);

  const handleSelect = (stock) => {
    setQuery(stock.name);
    setSuggestions([]);
    setShowDrop(false);
    onSearch(stock.symbol, exchange);
  };

  const handleSubmit = () => {
    if (!query.trim()) return;
    setShowDrop(false);
    onSearch(query.trim(), exchange);
  };

  const marketLabel = (market) => {
    const labels = { US: 'US', IN: 'India', KR: 'Korea', JP: 'Japan', CN: 'China', DE: 'Germany', UK: 'UK', FR: 'France', NL: 'Netherlands', CH: 'Switzerland', TW: 'Taiwan' };
    return labels[market] || market;
  };

  return (
    <div style={{ position: 'relative', marginBottom: 24 }}>
      <div className="search-bar">
        <input
          className="search-input"
          placeholder="Search by company name or ticker e.g. Apple, Reliance, TSLA..."
          value={query}
          onChange={e => { setQuery(e.target.value); setShowDrop(true); }}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          onFocus={() => suggestions.length > 0 && setShowDrop(true)}
        />
        <select
          value={exchange}
          onChange={e => setExchange(e.target.value)}
          style={{ background: '#161b22', border: '1px solid #21262d', borderRadius: 8, padding: '0 12px', color: '#e1e4e8', fontSize: 14, cursor: 'pointer' }}
        >
          <option value="NSE">NSE (India)</option>
          <option value="BSE">BSE (India)</option>
          <option value="US">US</option>
        </select>
        <button className="btn btn-primary" onClick={handleSubmit} disabled={loading || !query.trim()}>
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {showDrop && suggestions.length > 0 && (
        <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: '#161b22', border: '1px solid #21262d', borderRadius: 8, zIndex: 100, maxHeight: 300, overflowY: 'auto', marginTop: 4 }}>
          {suggestions.map((s, i) => (
            <div
              key={i}
              onClick={() => handleSelect(s)}
              style={{ padding: '10px 16px', cursor: 'pointer', borderBottom: '1px solid #21262d22', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
              onMouseEnter={e => e.currentTarget.style.background = '#21262d'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <div>
                <div style={{ color: '#e1e4e8', fontSize: 14, fontWeight: 600 }}>{s.name}</div>
                <div style={{ color: '#8b949e', fontSize: 12 }}>{s.symbol}</div>
              </div>
              <span style={{ background: '#21262d', padding: '2px 8px', borderRadius: 4, fontSize: 11, color: '#8b949e' }}>
                {marketLabel(s.market)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SearchBar;
"""

# ── PriceChart component ────────────────────────────────────────
files["dashboard/src/components/PriceChart.js"] = """
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import axios from 'axios';

function PriceChart({ symbol }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    axios.get('http://localhost:8000/api/v1/history/' + symbol + '?limit=1')
      .then(res => {
        const history = res.data.history;
        if (history && history.length > 0 && history[0].scores) {
          // We don't have raw price history from history endpoint
          // So we'll show a placeholder message
          setData([]);
        }
      })
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) return <div style={{ color: '#8b949e', fontSize: 13, padding: 20 }}>Loading chart...</div>;

  return (
    <div>
      <div style={{ color: '#8b949e', fontSize: 13, textAlign: 'center', padding: 20 }}>
        Price chart coming soon — run analysis to see latest price data.
      </div>
    </div>
  );
}

export default PriceChart;
"""

# ── Analyze page ────────────────────────────────────────────────
files["dashboard/src/pages/Analyze.js"] = """
import React, { useState } from 'react';
import { analyzeStock, addToWatchlist } from '../api';
import SearchBar from '../components/SearchBar';
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';

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
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);

  const handleSearch = async (symbol, exchange) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setSaved(false);
    try {
      const res = await analyzeStock(symbol, exchange);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Check the symbol and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddWatchlist = async () => {
    try { await addToWatchlist(result.symbol); setSaved(true); } catch {}
  };

  const radarData = result ? Object.entries(result.scores).map(([key, val]) => ({
    subject: key.replace('Agent','').replace('Intelligence','').replace('Analysis','').trim(),
    score: Math.max(val + 100, 0),
    fullMark: 200,
  })) : [];

  return (
    <div>
      <h1 className="page-title">Analyze Stock</h1>
      <SearchBar onSearch={handleSearch} loading={loading} />

      {loading && (
        <div className="loading">
          <div>
            <div style={{ fontSize: 16, marginBottom: 8 }}>Running AI analysis...</div>
            <div style={{ fontSize: 13, color: '#484f58' }}>9 agents working — usually takes 15-30 seconds</div>
          </div>
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}

      {result && (
        <>
          {/* Decision hero card */}
          <div className="card" style={{ textAlign: 'center', padding: '40px 24px' }}>
            <div style={{ fontSize: 13, color: '#8b949e', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>
              {result.symbol}
            </div>
            <span className={getBadgeClass(result.final_decision)} style={{ fontSize: 22, padding: '10px 28px' }}>
              {result.final_decision}
            </span>
            <div style={{ marginTop: 20 }}>
              <div className="confidence">{result.confidence?.toFixed(1)}%</div>
              <div className="confidence-label">Confidence Level</div>
            </div>
            <p style={{ marginTop: 16, color: '#8b949e', fontSize: 14, maxWidth: 520, margin: '16px auto 0', lineHeight: 1.6 }}>
              {result.recommendation}
            </p>
            <button className="btn btn-primary" style={{ marginTop: 20 }} onClick={handleAddWatchlist} disabled={saved}>
              {saved ? 'Added to Watchlist' : '+ Add to Watchlist'}
            </button>
          </div>

          {/* Plain English Explanations */}
          {result.explanations && Object.keys(result.explanations).length > 0 && (
            <div className="card">
              <div className="card-title">Why this decision?</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {Object.entries(result.explanations).map(([key, val]) => (
                  <div key={key} style={{ background: '#0f1117', borderRadius: 8, padding: '12px 16px' }}>
                    <div style={{ fontSize: 12, color: '#8b949e', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.5 }}>{key}</div>
                    <div style={{ fontSize: 13, color: '#e1e4e8', lineHeight: 1.5 }}>{val}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid-2">
            {/* Score bars */}
            <div className="card">
              <div className="card-title">Agent Scores</div>
              {Object.entries(result.scores).map(([name, score]) => (
                <ScoreBar key={name} name={name} score={score} />
              ))}
            </div>

            {/* Radar chart */}
            <div className="card">
              <div className="card-title">Score Radar</div>
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#21262d" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: '#8b949e', fontSize: 10 }} />
                  <Radar dataKey="score" stroke="#00d4aa" fill="#00d4aa" fillOpacity={0.2} />
                  <Tooltip
                    formatter={(val) => [(val - 100).toFixed(1), 'Score']}
                    contentStyle={{ background: '#161b22', border: '1px solid #21262d', borderRadius: 8 }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Failed agents note */}
          {result.errors?.length > 0 && (
            <div style={{ background: '#21262d', borderRadius: 8, padding: '12px 16px', fontSize: 13, color: '#8b949e' }}>
              Note: {result.errors.map(e => e.replace('Agent','')).join(', ')} data was unavailable — decision based on remaining agents.
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Analyze;
"""

# ── Dashboard page ──────────────────────────────────────────────
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

  const fetch = () => {
    getDashboard()
      .then(res => setData(res.data))
      .catch(() => setError('Failed to load dashboard'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetch(); }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error) return <div className="error-msg">{error}</div>;

  const buys  = data?.results?.filter(r => r.final_decision === 'BUY').length || 0;
  const sells = data?.results?.filter(r => r.final_decision === 'SELL').length || 0;
  const holds = data?.results?.filter(r => r.final_decision === 'HOLD').length || 0;

  return (
    <div>
      <h1 className="page-title">Dashboard</h1>

      {/* Summary stats */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 20 }}>
        <div className="card" style={{ textAlign: 'center', padding: 20 }}>
          <div style={{ fontSize: 32, fontWeight: 700, color: '#00d4aa' }}>{buys}</div>
          <div style={{ fontSize: 13, color: '#8b949e', marginTop: 4 }}>BUY Signals</div>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: 20 }}>
          <div style={{ fontSize: 32, fontWeight: 700, color: '#e3b341' }}>{holds}</div>
          <div style={{ fontSize: 13, color: '#8b949e', marginTop: 4 }}>HOLD Signals</div>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: 20 }}>
          <div style={{ fontSize: 32, fontWeight: 700, color: '#f85149' }}>{sells}</div>
          <div style={{ fontSize: 13, color: '#8b949e', marginTop: 4 }}>SELL Signals</div>
        </div>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div className="card-title" style={{ marginBottom: 0 }}>Recent Analyses</div>
          <button className="btn btn-primary" style={{ padding: '6px 14px', fontSize: 12 }} onClick={fetch}>
            Refresh
          </button>
        </div>
        {!data?.results?.length ? (
          <p style={{ color: '#8b949e', fontSize: 14 }}>No analyses yet. Go to Analyze to run your first one.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Company</th>
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
                  <td>{r.close_price ? '$' + r.close_price.toFixed(2) : '—'}</td>
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

# ── Watchlist page ──────────────────────────────────────────────
files["dashboard/src/pages/Watchlist.js"] = """
import React, { useState, useEffect } from 'react';
import { getWatchlist, removeFromWatchlist, analyzeStock } from '../api';

function getBadgeClass(d) {
  if (d === 'BUY') return 'badge badge-buy';
  if (d === 'SELL') return 'badge badge-sell';
  return 'badge badge-hold';
}

function Watchlist() {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(null);
  const [results, setResults] = useState({});

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
      const res = await analyzeStock(symbol);
      setResults(prev => ({ ...prev, [symbol]: res.data }));
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
          <p style={{ color: '#8b949e', fontSize: 14 }}>
            Watchlist is empty. Analyze a stock and click Add to Watchlist.
          </p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Latest Signal</th>
                <th>Confidence</th>
                <th>Added</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {watchlist.map(item => {
                const r = results[item.symbol];
                return (
                  <tr key={item.id}>
                    <td><strong>{item.symbol}</strong></td>
                    <td>
                      {r ? <span className={getBadgeClass(r.final_decision)}>{r.final_decision}</span> : <span style={{ color: '#484f58', fontSize: 12 }}>Not run yet</span>}
                    </td>
                    <td>{r ? r.confidence?.toFixed(1) + '%' : '—'}</td>
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
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Watchlist;
"""

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Written: {path}")

print("\nAll dashboard files updated!")