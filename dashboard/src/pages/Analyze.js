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