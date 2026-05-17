import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { Sprout, LayoutDashboard, Calculator, LineChart, Network, History, LogOut } from 'lucide-react';
import './Navbar.css';

const Navbar = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    // Removed navigate to /login
  };

  return (
    <nav className="glass-panel navbar">
      <div className="navbar-brand">
        <Sprout color="var(--primary-color)" size={28} />
        <h2>AgriPredict</h2>
      </div>
      
      <div className="navbar-links">
        <NavLink to="/dashboard" className={({isActive}) => isActive ? "nav-link active" : "nav-link"}>
          <LayoutDashboard size={20} /> Dashboard
        </NavLink>
        <NavLink to="/predict" className={({isActive}) => isActive ? "nav-link active" : "nav-link"}>
          <Calculator size={20} /> Predict
        </NavLink>
        <NavLink to="/eda" className={({isActive}) => isActive ? "nav-link active" : "nav-link"}>
          <LineChart size={20} /> Analysis
        </NavLink>
        <NavLink to="/workflow" className={({isActive}) => isActive ? "nav-link active" : "nav-link"}>
          <Network size={20} /> Workflow
        </NavLink>
        <NavLink to="/history" className={({isActive}) => isActive ? "nav-link active" : "nav-link"}>
          <History size={20} /> History
        </NavLink>
      </div>

      <div className="navbar-actions">
        <button onClick={handleLogout} className="btn-logout">
          <LogOut size={20} />
          <span>Logout</span>
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
