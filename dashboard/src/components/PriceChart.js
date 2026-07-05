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