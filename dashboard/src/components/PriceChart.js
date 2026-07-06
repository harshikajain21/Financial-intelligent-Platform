import React, { useState, useEffect } from 'react';
import {
  ComposedChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, ReferenceLine, Area
} from 'recharts';
import axios from 'axios';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: '#161b22', border: '1px solid #21262d', borderRadius: 8, padding: '10px 14px' }}>
        <div style={{ color: '#8b949e', fontSize: 12, marginBottom: 4 }}>{label}</div>
        {payload.map((p, i) => (
          <div key={i} style={{ color: p.color, fontSize: 14, fontWeight: 600 }}>
            {p.name}: ${p.value?.toFixed(2)}
          </div>
        ))}
      </div>
    );
  }
  return null;
};

function PriceChart({ symbol, forecasts }) {
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
        const priceData = res.data.data || [];
        setMeta(res.data);

        // Add forecast points after last real price
        let combined = priceData.map(d => ({ ...d, type: 'actual' }));

        if (forecasts) {
          const lastDate = priceData.length > 0 ? priceData[priceData.length - 1].date : null;
          const horizons = [
            { key: '7d',  label: '+7d',  days: 7  },
            { key: '30d', label: '+30d', days: 30 },
            { key: '90d', label: '+90d', days: 90 },
          ];
          horizons.forEach(h => {
            if (forecasts[h.key]) {
              combined.push({
                date     : h.label,
                close    : null,
                forecast : forecasts[h.key].price,
                lower    : forecasts[h.key].lower,
                upper    : forecasts[h.key].upper,
                type     : 'forecast'
              });
            }
          });
        }

        setData(combined);
      })
      .catch(() => setError('Could not load price data'))
      .finally(() => setLoading(false));
  }, [symbol, period, forecasts]);

  const periods = [
    { label: '1M', value: '1mo' },
    { label: '3M', value: '3mo' },
    { label: '6M', value: '6mo' },
    { label: '1Y', value: '1y' },
  ];

  const isPositive = meta?.change_pct >= 0;
  const lineColor  = isPositive ? '#00d4aa' : '#f85149';
  const tickInterval = Math.floor(data.length / 6);

  if (loading) return <div style={{ padding: 40, textAlign: 'center', color: '#8b949e', fontSize: 14 }}>Loading chart...</div>;
  if (error)   return <div style={{ padding: 20, color: '#f85149', fontSize: 13 }}>{error}</div>;

  return (
    <div>
      {/* Stats row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
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
          {forecasts?.['30d'] && (
            <div>
              <div style={{ fontSize: 14, color: forecasts['30d'].change_pct >= 0 ? '#00d4aa' : '#f85149', fontWeight: 600 }}>
                {forecasts['30d'].change_pct >= 0 ? '+' : ''}{forecasts['30d'].change_pct?.toFixed(2)}%
              </div>
              <div style={{ fontSize: 12, color: '#8b949e' }}>30d Forecast</div>
            </div>
          )}
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {periods.map(p => (
            <button key={p.value} onClick={() => setPeriod(p.value)} style={{
              padding: '4px 10px', borderRadius: 6, border: 'none', fontSize: 12,
              fontWeight: 600, cursor: 'pointer',
              background: period === p.value ? '#00d4aa' : '#21262d',
              color: period === p.value ? '#0f1117' : '#8b949e',
            }}>
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={240}>
        <ComposedChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#21262d" vertical={false} />
          <XAxis
            dataKey="date" tick={{ fill: '#484f58', fontSize: 11 }}
            tickLine={false} axisLine={false}
            interval={tickInterval}
            tickFormatter={val => val.startsWith('+') ? val : val.slice(5)}
          />
          <YAxis
            tick={{ fill: '#484f58', fontSize: 11 }} tickLine={false}
            axisLine={false} tickFormatter={val => '$' + val}
            domain={['auto', 'auto']} width={55}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Actual price line */}
          <Line
            type="monotone" dataKey="close" name="Price"
            stroke={lineColor} strokeWidth={2}
            dot={false} activeDot={{ r: 4, fill: lineColor }}
            connectNulls={false}
          />

          {/* Forecast line */}
          <Line
            type="monotone" dataKey="forecast" name="Forecast"
            stroke="#a371f7" strokeWidth={2} strokeDasharray="6 3"
            dot={{ r: 4, fill: '#a371f7' }} activeDot={{ r: 5 }}
            connectNulls={true}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {forecasts && (
        <div style={{ display: 'flex', gap: 16, marginTop: 12, flexWrap: 'wrap' }}>
          {Object.entries(forecasts).map(([horizon, data]) => (
            <div key={horizon} style={{ background: '#0f1117', borderRadius: 8, padding: '10px 14px', flex: 1, minWidth: 120 }}>
              <div style={{ fontSize: 11, color: '#8b949e', marginBottom: 4, textTransform: 'uppercase' }}>
                {horizon} Forecast
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#fff' }}>${data.price?.toFixed(2)}</div>
              <div style={{ fontSize: 12, color: data.change_pct >= 0 ? '#00d4aa' : '#f85149' }}>
                {data.change_pct >= 0 ? '+' : ''}{data.change_pct?.toFixed(2)}%
              </div>
              <div style={{ fontSize: 11, color: '#484f58', marginTop: 2 }}>
                ${data.lower?.toFixed(0)} - ${data.upper?.toFixed(0)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default PriceChart;