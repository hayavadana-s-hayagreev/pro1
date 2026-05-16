import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sprout, Lock, User, Leaf } from 'lucide-react';
import { motion } from 'framer-motion';
import axios from 'axios';
import './Login.css';

const Login = () => {
  const [username, setUsername] = useState('semicolon');
  const [password, setPassword] = useState('semicolon123');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axios.post('http://localhost:8000/auth/token', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      localStorage.setItem('token', response.data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError('Invalid username or password. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-bg-overlay"></div>
      
      <motion.div 
        className="glass-panel login-card"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="login-header">
          <motion.div 
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="logo-container"
          >
            <Sprout size={48} color="var(--primary-color)" />
          </motion.div>
          <h1>AgriPredict</h1>
          <p>Next-Gen Crop Yield Estimator</p>
        </div>

        {error && <div className="error-alert">{error}</div>}

        <form onSubmit={handleLogin} className="login-form">
          <div className="input-group">
            <User className="input-icon" size={20} />
            <input 
              type="text" 
              placeholder="Username" 
              className="input-field with-icon"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          
          <div className="input-group">
            <Lock className="input-icon" size={20} />
            <input 
              type="password" 
              placeholder="Password" 
              className="input-field with-icon"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="btn-primary login-btn" disabled={isLoading}>
            {isLoading ? 'Authenticating...' : 'Sign In to Platform'}
          </button>
        </form>

        <div className="login-footer">
          <Leaf size={14} color="var(--success)" />
          <span>Test credentials provided for assessment</span>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;
