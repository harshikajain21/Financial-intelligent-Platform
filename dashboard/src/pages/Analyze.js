import React, { useState } from 'react';
import { analyzeStock, addToWatchlist } from '../api';
import SearchBar from '../components/SearchBar';
import PriceChart from '../components/PriceChart';
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
  const pct   = Math.min(Math.abs(score), 100);
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
  const [result,          setResult]          = useState(null);
  const [loading,         setLoading]         = useState(false);
  const [error,           setError]           = useState(null);
  const [saved,           setSaved]           = useState(false);
  const [analyzedSymbol,  setAnalyzedSymbol]  = useState(null);
  const [forecasts,       setForecasts]       = useState(null);

  const handleSearch = async (symbol, exchange) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setSaved(false);
    setAnalyzedSymbol(null);
    setForecasts(null);
    try {
      const res = await analyzeStock(symbol, exchange);
      setResult(res.data);
      setAnalyzedSymbol(res.data.symbol);

      // Extract forecast data if available
      const forecastScore = res.data.scores?.ForecastingAgent;
      if (forecastScore !== undefined && res.data.forecasts) {
        setForecasts(res.data.forecasts);
      }
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
            <div style={{ fontSize: 13, color: '#484f58' }}>10 agents working — usually takes 30-45 seconds</div>
          </div>
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}

      {result && (
        <>
          {/* Price Chart with Forecast */}
          <div className="card">
            <div className="card-title">Price History & Forecast</div>
            <PriceChart symbol={analyzedSymbol} forecasts={forecasts} />
          </div>

          {/* Decision card */}
          <div className="card" style={{ textAlign: 'center', padding: '32px 24px' }}>
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

          {result.errors?.length > 0 && (
            <div style={{ background: '#21262d', borderRadius: 8, padding: '12px 16px', fontSize: 13, color: '#8b949e' }}>
              Note: {result.errors.map(e => e.replace('Agent','')).join(', ')} data was unavailable.
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default Analyze;