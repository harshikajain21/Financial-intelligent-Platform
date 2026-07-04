import React, { useState, useEffect } from 'react';
import { getWatchlist, removeFromWatchlist, analyzeStock } from '../api';

function Watchlist() {
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(null);

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
      await analyzeStock(symbol);
      alert('Analysis complete for ' + symbol + '. Check Dashboard for results.');
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
          <p style={{ color: '#8b949e', fontSize: 14 }}>Watchlist is empty. Analyze a stock and click Add to Watchlist.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Added</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {watchlist.map(item => (
                <tr key={item.id}>
                  <td><strong>{item.symbol}</strong></td>
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
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Watchlist;