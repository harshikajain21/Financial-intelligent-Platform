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