# add_forecast_ui.py

# First add forecast endpoint to API
prices_with_forecast = """
# api/routes/prices.py

from fastapi import APIRouter, HTTPException, Request
from api.limiter import limiter
from api.sanitizer import sanitize_symbol
import yfinance as yf
from utils.logger import get_logger

router = APIRouter()
logger = get_logger("PricesRouter")

ALLOWED_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y"}


@router.get("/prices/{symbol}", summary="Get price history for a stock symbol")
@limiter.limit("20/minute")
async def get_prices(request: Request, symbol: str, period: str = "6mo"):
    symbol = sanitize_symbol(symbol)
    if period not in ALLOWED_PERIODS:
        raise HTTPException(status_code=400, detail=f"Invalid period. Allowed: {ALLOWED_PERIODS}")
    try:
        logger.info(f"Fetching price history for {symbol}")
        ticker = yf.Ticker(symbol)
        hist   = ticker.history(period=period)
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")
        hist = hist.reset_index()
        data = []
        for _, row in hist.iterrows():
            data.append({
                "date"  : str(row["Date"])[:10],
                "close" : round(float(row["Close"]), 2),
                "open"  : round(float(row["Open"]), 2),
                "high"  : round(float(row["High"]), 2),
                "low"   : round(float(row["Low"]), 2),
                "volume": int(row["Volume"]),
            })
        closes      = [d["close"] for d in data]
        start_price = closes[0] if closes else 0
        end_price   = closes[-1] if closes else 0
        change_pct  = round(((end_price - start_price) / start_price) * 100, 2) if start_price else 0
        return {
            "symbol"      : symbol,
            "period"      : period,
            "data"        : data,
            "current"     : end_price,
            "change_pct"  : change_pct,
            "period_high" : round(max(closes), 2) if closes else 0,
            "period_low"  : round(min(closes), 2) if closes else 0,
            "bars"        : len(data)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Price fetch failed for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch price data.")
"""

with open("api/routes/prices.py", "w", encoding="utf-8") as f:
    f.write(prices_with_forecast.strip())
    print("api/routes/prices.py updated")

# Update PriceChart to show forecast data from analysis result
price_chart = """
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
"""

with open("dashboard/src/components/PriceChart.js", "w", encoding="utf-8") as f:
    f.write(price_chart.strip())
    print("PriceChart.js updated with forecast overlay")

# Update Analyze.js to pass forecast data to chart
analyze = """
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
"""

with open("dashboard/src/pages/Analyze.js", "w", encoding="utf-8") as f:
    f.write(analyze.strip())
    print("Analyze.js updated")

print("\nDone! Restart React to see forecast on chart.")