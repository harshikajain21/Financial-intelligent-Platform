import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { BarChart2, Search, BookMarked, Activity } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import Analyze from './pages/Analyze';
import Watchlist from './pages/Watchlist';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <aside className="sidebar">
          <div className="logo">
            <Activity size={24} color="#00d4aa" />
            <span>FinIntel</span>
          </div>
          <nav className="nav">
            <NavLink to="/" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'} end>
              <BarChart2 size={18} />
              <span>Dashboard</span>
            </NavLink>
            <NavLink to="/analyze" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
              <Search size={18} />
              <span>Analyze</span>
            </NavLink>
            <NavLink to="/watchlist" className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
              <BookMarked size={18} />
              <span>Watchlist</span>
            </NavLink>
          </nav>
          <div className="sidebar-footer">
            <span>Financial Intelligence Platform</span>
            <span>v0.1.0</span>
          </div>
        </aside>
        <main className="main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/analyze" element={<Analyze />} />
            <Route path="/watchlist" element={<Watchlist />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;