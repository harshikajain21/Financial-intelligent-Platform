import React, { useState, useEffect } from 'react';
import { getDashboard } from '../api';
import axios from 'axios';

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
    // Wake up backend first
    axios.get('https://financial-ntelligent-platform.onrender.com/api/v1/health')
      .then(() => {
        getDashboard()
          .then(res => setData(res.data))
          .catch(() => setError('Failed to load dashboard'))
          .finally(() => setLoading(false));
      })
      .catch(() => setError('Backend is waking up, please wait 30 seconds and refresh'));
  };


  useEffect(() => { fetch(); }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;
  if (error) return <div className="error-msg">{error}</div>;

  const buys = data?.results?.filter(r => r.final_decision === 'BUY').length || 0;
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