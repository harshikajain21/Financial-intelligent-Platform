# add_explanation_ui.py

content = """
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

function getVerdictColor(verdict) {
  if (verdict?.includes('BULLISH')) return '#00d4aa';
  if (verdict?.includes('BEARISH')) return '#f85149';
  return '#8b949e';
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

function FullReport({ explanation }) {
  const [open, setOpen] = useState(false);
  if (!explanation || !explanation.executive_summary) return null;

  return (
    <div className="card">
      <div
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        onClick={() => setOpen(!open)}
      >
        <div className="card-title" style={{ marginBottom: 0 }}>Full AI Investment Report</div>
        <span style={{ color: '#00d4aa', fontSize: 13 }}>{open ? 'Hide' : 'Show Report'}</span>
      </div>

      {open && (
        <div style={{ marginTop: 20 }}>

          {/* Executive Summary */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, color: '#8b949e', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>Executive Summary</div>
            <p style={{ fontSize: 14, color: '#e1e4e8', lineHeight: 1.7, background: '#0f1117', padding: 16, borderRadius: 8 }}>
              {explanation.executive_summary}
            </p>
          </div>

          {/* Signal Analysis */}
          {explanation.signal_analysis?.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 12, color: '#8b949e', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>Signal Breakdown</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {explanation.signal_analysis.map((s, i) => (
                  <div key={i} style={{ background: '#0f1117', borderRadius: 8, padding: '10px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: 13, color: '#e1e4e8', fontWeight: 600 }}>{s.agent}</div>
                      <div style={{ fontSize: 12, color: '#484f58', marginTop: 2 }}>{s.description}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: 13, color: getVerdictColor(s.verdict), fontWeight: 600 }}>{s.verdict}</div>
                      <div style={{ fontSize: 12, color: '#8b949e' }}>Score: {s.score}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Agreement Map */}
          {explanation.agreement_map && (
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 12, color: '#8b949e', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>Agent Agreement</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
                <div style={{ background: '#1f3d2e', borderRadius: 8, padding: '12px 16px' }}>
                  <div style={{ fontSize: 11, color: '#00d4aa', marginBottom: 6 }}>AGREEING ({explanation.agreement_map.agreeing?.length})</div>
                  {explanation.agreement_map.agreeing?.map((a, i) => (
                    <div key={i} style={{ fontSize: 12, color: '#e1e4e8', marginBottom: 2 }}>• {a}</div>
                  ))}
                </div>
                <div style={{ background: '#21262d', borderRadius: 8, padding: '12px 16px' }}>
                  <div style={{ fontSize: 11, color: '#8b949e', marginBottom: 6 }}>NEUTRAL ({explanation.agreement_map.neutral?.length})</div>
                  {explanation.agreement_map.neutral?.map((a, i) => (
                    <div key={i} style={{ fontSize: 12, color: '#8b949e', marginBottom: 2 }}>• {a}</div>
                  ))}
                </div>
                <div style={{ background: '#3d1f1f', borderRadius: 8, padding: '12px 16px' }}>
                  <div style={{ fontSize: 11, color: '#f85149', marginBottom: 6 }}>DISAGREEING ({explanation.agreement_map.disagreeing?.length})</div>
                  {explanation.agreement_map.disagreeing?.map((a, i) => (
                    <div key={i} style={{ fontSize: 12, color: '#e1e4e8', marginBottom: 2 }}>• {a}</div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Key Risks */}
          {explanation.key_risks?.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 12, color: '#8b949e', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>Key Risks</div>
              {explanation.key_risks.map((risk, i) => (
                <div key={i} style={{ background: '#3d1f1f22', border: '1px solid #f8514922', borderRadius: 8, padding: '10px 16px', marginBottom: 8, fontSize: 13, color: '#e1e4e8', lineHeight: 1.5 }}>
                  ⚠️ {risk}
                </div>
              ))}
            </div>
          )}

          {/* What Would Change */}
          {explanation.what_would_change?.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 12, color: '#8b949e', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>What Would Change This Decision</div>
              {explanation.what_would_change.map((item, i) => (
                <div key={i} style={{ background: '#21262d', borderRadius: 8, padding: '10px 16px', marginBottom: 8, fontSize: 13, color: '#e1e4e8', lineHeight: 1.5 }}>
                  → {item}
                </div>
              ))}
            </div>
          )}

          {/* Data Quality */}
          {explanation.data_quality && (
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 12, color: '#8b949e', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>Data Quality</div>
              <div style={{ background: '#0f1117', borderRadius: 8, padding: '12px 16px', display: 'flex', gap: 24, alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 22, fontWeight: 700, color: '#00d4aa' }}>{explanation.data_quality.success_rate}%</div>
                  <div style={{ fontSize: 12, color: '#8b949e' }}>Success Rate</div>
                </div>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 600, color: '#e1e4e8' }}>{explanation.data_quality.quality}</div>
                  <div style={{ fontSize: 12, color: '#8b949e' }}>Quality Rating</div>
                </div>
                <div style={{ fontSize: 13, color: '#8b949e', flex: 1 }}>{explanation.data_quality.note}</div>
              </div>
            </div>
          )}

          {/* Disclaimer */}
          <div style={{ fontSize: 11, color: '#484f58', borderTop: '1px solid #21262d', paddingTop: 16, lineHeight: 1.6 }}>
            {explanation.disclaimer}
          </div>
        </div>
      )}
    </div>
  );
}

function Analyze() {
  const [result,         setResult]         = useState(null);
  const [loading,        setLoading]        = useState(false);
  const [error,          setError]          = useState(null);
  const [saved,          setSaved]          = useState(false);
  const [analyzedSymbol, setAnalyzedSymbol] = useState(null);
  const [forecasts,      setForecasts]      = useState(null);

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
      if (res.data.forecasts && Object.keys(res.data.forecasts).length > 0) {
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
    subject : key.replace('Agent','').replace('Intelligence','').replace('Analysis','').trim(),
    score   : Math.max(val + 100, 0),
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
            <div style={{ fontSize: 13, color: '#484f58' }}>11 agents working — usually takes 30-45 seconds</div>
          </div>
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}

      {result && (
        <>
          <div className="card">
            <div className="card-title">Price History & Forecast</div>
            <PriceChart symbol={analyzedSymbol} forecasts={forecasts} />
          </div>

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

          {/* Full AI Report — collapsible */}
          <FullReport explanation={result.explanation} />

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
"""

with open("dashboard/src/pages/Analyze.js", "w", encoding="utf-8") as f:
    f.write(content.strip())
    print("Analyze.js updated with Full Report section")