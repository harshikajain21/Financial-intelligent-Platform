# add_chart.py

chart_component = """
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine } from 'recharts';
import axios from 'axios';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: '#161b22', border: '1px solid #21262d', borderRadius: 8, padding: '10px 14px' }}>
        <div style={{ color: '#8b949e', fontSize: 12, marginBottom: 4 }}>{label}</div>
        <div style={{ color: '#00d4aa', fontSize: 16, fontWeight: 700 }}>${payload[0].value.toFixed(2)}</div>
      </div>
    );
  }
  return null;
};

function PriceChart({ symbol }) {
  const [data, setData] = useState([]);
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState('6mo');

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    axios.get('http://localhost:8000/api/v1/prices/' + symbol + '?period=' + period)
      .then(res => {
        setData(res.data.data || []);
        setMeta(res.data);
      })
      .catch(() => setError('Could not load price data'))
      .finally(() => setLoading(false));
  }, [symbol, period]);

  const periods = [
    { label: '1M', value: '1mo' },
    { label: '3M', value: '3mo' },
    { label: '6M', value: '6mo' },
    { label: '1Y', value: '1y' },
  ];

  const isPositive = meta?.change_pct >= 0;
  const lineColor = isPositive ? '#00d4aa' : '#f85149';

  // Show only every Nth date label to avoid crowding
  const tickInterval = Math.floor(data.length / 6);

  if (loading) return (
    <div style={{ padding: 40, textAlign: 'center', color: '#8b949e', fontSize: 14 }}>
      Loading price chart...
    </div>
  );

  if (error) return (
    <div style={{ padding: 20, color: '#f85149', fontSize: 13 }}>{error}</div>
  );

  return (
    <div>
      {/* Stats row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 24 }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#fff' }}>${meta?.current?.toFixed(2)}</div>
            <div style={{ fontSize: 12, color: '#8b949e' }}>Current Price</div>
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, color: isPositive ? '#00d4aa' : '#f85149' }}>
              {isPositive ? '+' : ''}{meta?.change_pct?.toFixed(2)}%
            </div>
            <div style={{ fontSize: 12, color: '#8b949e' }}>Period Change</div>
          </div>
          <div>
            <div style={{ fontSize: 14, color: '#00d4aa' }}>${meta?.period_high?.toFixed(2)}</div>
            <div style={{ fontSize: 12, color: '#8b949e' }}>Period High</div>
          </div>
          <div>
            <div style={{ fontSize: 14, color: '#f85149' }}>${meta?.period_low?.toFixed(2)}</div>
            <div style={{ fontSize: 12, color: '#8b949e' }}>Period Low</div>
          </div>
        </div>

        {/* Period selector */}
        <div style={{ display: 'flex', gap: 4 }}>
          {periods.map(p => (
            <button
              key={p.value}
              onClick={() => setPeriod(p.value)}
              style={{
                padding: '4px 10px',
                borderRadius: 6,
                border: 'none',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
                background: period === p.value ? '#00d4aa' : '#21262d',
                color: period === p.value ? '#0f1117' : '#8b949e',
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#21262d" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: '#484f58', fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            interval={tickInterval}
            tickFormatter={val => val.slice(5)}
          />
          <YAxis
            tick={{ fill: '#484f58', fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={val => '$' + val}
            domain={['auto', 'auto']}
            width={55}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="close"
            stroke={lineColor}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: lineColor }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default PriceChart;
"""

with open("dashboard/src/components/PriceChart.js", "w", encoding="utf-8") as f:
    f.write(chart_component.strip())
    print("PriceChart.js written")

# Update Analyze.js to include the chart
analyze_content = """
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
  const [analyzedSymbol, setAnalyzedSymbol] = useState(null);

  const handleSearch = async (symbol, exchange) => {
    setLoading(true);
    setError(null);
    setResult(null);
    setSaved(false);
    setAnalyzedSymbol(null);
    try {
      const res = await analyzeStock(symbol, exchange);
      setResult(res.data);
      setAnalyzedSymbol(res.data.symbol);
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
          {/* Price Chart */}
          <div className="card">
            <div className="card-title">Price History</div>
            <PriceChart symbol={analyzedSymbol} />
          </div>

          {/* Decision hero card */}
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

with open("dashboard/src/pages/Analyze.js", "w", encoding="utf-8") as f:
    f.write(analyze_content.strip())
    print("Analyze.js updated with price chart")

print("\nDone! Restart React to see the chart.")