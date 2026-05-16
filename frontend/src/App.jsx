import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Predict from './pages/Predict';
import EDA from './pages/EDA';
import Workflow from './pages/Workflow';
import History from './pages/History';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <BrowserRouter>
      <div className="app-wrapper">
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/*" element={
            <ProtectedRoute>
              <>
                <Navbar />
                <div className="container" style={{ marginTop: '80px' }}>
                  <Routes>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/predict" element={<Predict />} />
                    <Route path="/eda" element={<EDA />} />
                    <Route path="/workflow" element={<Workflow />} />
                    <Route path="/history" element={<History />} />
                  </Routes>
                </div>
              </>
            </ProtectedRoute>
          } />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
