import React, { useState, useEffect, useRef } from 'react';
import { searchStocks } from '../api';

function SearchBar({ onSearch, loading }) {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [exchange, setExchange] = useState('NSE');
  const [showDrop, setShowDrop] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (query.length < 2) { setSuggestions([]); return; }
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      searchStocks(query)
        .then(res => { setSuggestions(res.data.results || []); setShowDrop(true); })
        .catch(() => setSuggestions([]));
    }, 300);
  }, [query]);

  const handleSelect = (stock) => {
    setQuery(stock.name);
    setSuggestions([]);
    setShowDrop(false);
    onSearch(stock.symbol, exchange);
  };

  const handleSubmit = () => {
    if (!query.trim()) return;
    setShowDrop(false);
    onSearch(query.trim(), exchange);
  };

  const marketLabel = (market) => {
    const labels = { US: 'US', IN: 'India', KR: 'Korea', JP: 'Japan', CN: 'China', DE: 'Germany', UK: 'UK', FR: 'France', NL: 'Netherlands', CH: 'Switzerland', TW: 'Taiwan' };
    return labels[market] || market;
  };

  return (
    <div style={{ position: 'relative', marginBottom: 24 }}>
      <div className="search-bar">
        <input
          className="search-input"
          placeholder="Search by company name or ticker e.g. Apple, Reliance, TSLA..."
          value={query}
          onChange={e => { setQuery(e.target.value); setShowDrop(true); }}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          onFocus={() => suggestions.length > 0 && setShowDrop(true)}
        />
        <select
          value={exchange}
          onChange={e => setExchange(e.target.value)}
          style={{ background: '#161b22', border: '1px solid #21262d', borderRadius: 8, padding: '0 12px', color: '#e1e4e8', fontSize: 14, cursor: 'pointer' }}
        >
          <option value="NSE">NSE (India)</option>
          <option value="BSE">BSE (India)</option>
          <option value="US">US</option>
        </select>
        <button className="btn btn-primary" onClick={handleSubmit} disabled={loading || !query.trim()}>
          {loading ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>

      {showDrop && suggestions.length > 0 && (
        <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, background: '#161b22', border: '1px solid #21262d', borderRadius: 8, zIndex: 100, maxHeight: 300, overflowY: 'auto', marginTop: 4 }}>
          {suggestions.map((s, i) => (
            <div
              key={i}
              onClick={() => handleSelect(s)}
              style={{ padding: '10px 16px', cursor: 'pointer', borderBottom: '1px solid #21262d22', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
              onMouseEnter={e => e.currentTarget.style.background = '#21262d'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <div>
                <div style={{ color: '#e1e4e8', fontSize: 14, fontWeight: 600 }}>{s.name}</div>
                <div style={{ color: '#8b949e', fontSize: 12 }}>{s.symbol}</div>
              </div>
              <span style={{ background: '#21262d', padding: '2px 8px', borderRadius: 4, fontSize: 11, color: '#8b949e' }}>
                {marketLabel(s.market)}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SearchBar;