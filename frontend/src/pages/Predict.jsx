import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Sprout, Calculator, MapPin, Calendar, CloudRain, Thermometer, Bug, ArrowRight, CheckCircle2, AlertTriangle, Info, XCircle } from 'lucide-react';
import axios from 'axios';
import './Predict.css';

// Countries that exist in the training dataset
const VALID_COUNTRIES = [
  'Albania','Algeria','Angola','Argentina','Armenia','Australia','Austria',
  'Azerbaijan','Bahamas','Bahrain','Bangladesh','Belarus','Belgium','Botswana',
  'Brazil','Bulgaria','Burkina Faso','Burundi','Cameroon','Canada',
  'Central African Republic','Chile','Colombia','Croatia','Denmark',
  'Dominican Republic','Ecuador','Egypt','El Salvador','Eritrea','Estonia',
  'Finland','France','Germany','Ghana','Greece','Guatemala','Guinea','Guyana',
  'Haiti','Honduras','Hungary','India','Indonesia','Iraq','Ireland','Italy',
  'Jamaica','Japan','Kazakhstan','Kenya','Latvia','Lebanon','Lesotho','Libya',
  'Lithuania','Madagascar','Malawi','Malaysia','Mali','Mauritania','Mauritius',
  'Mexico','Montenegro','Morocco','Mozambique','Namibia','Nepal','Netherlands',
  'New Zealand','Nicaragua','Niger','Norway','Pakistan','Papua New Guinea',
  'Peru','Poland','Portugal','Qatar','Romania','Rwanda','Saudi Arabia',
  'Senegal','Slovenia','South Africa','Spain','Sri Lanka','Sudan','Suriname',
  'Sweden','Switzerland','Tajikistan','Thailand','Tunisia','Turkey','Uganda',
  'Ukraine','United Kingdom','Uruguay','Zambia','Zimbabwe'
];

const Predict = () => {
  const [formData, setFormData] = useState({
    crop: 'Rice, paddy',
    country: 'India',
    year: 2024,
    rainfall: 1200,
    pesticide: 150,
    temperature: 28
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const crops = ['Maize', 'Potatoes', 'Rice, paddy', 'Sorghum', 'Soybeans', 'Wheat', 'Cassava', 'Sweet potatoes', 'Plantains and others', 'Yams'];

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    // Parse numeric fields properly so they are sent as numbers not strings
    const numericFields = ['year', 'rainfall', 'pesticide', 'temperature'];
    setFormData(prev => ({
      ...prev,
      [name]: numericFields.includes(name) ? parseFloat(value) : value
    }));
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    
    try {
      const token = localStorage.getItem('token');
      const payload = {
        ...formData,
        year: parseInt(formData.year, 10),
        rainfall: parseFloat(formData.rainfall),
        pesticide: parseFloat(formData.pesticide),
        temperature: parseFloat(formData.temperature),
      };
      const response = await axios.post('http://localhost:8000/predict', payload, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setResult(response.data);
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Prediction failed. Please try again.';
      setError(String(detail));
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (text) => {
    if (text.includes("IRRIGATION") || text.includes("EXCELLENT")) return <CheckCircle2 color="var(--success)" />;
    if (text.includes("CLIMATE") || text.includes("FERTILIZER")) return <AlertTriangle color="var(--warning)" />;
    return <Info color="var(--info)" />;
  };

  return (
    <motion.div 
      className="predict-container animate-fade-in"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }}
    >
      <div className="predict-grid">
        {/* Form Section */}
        <div className="glass-panel p-6">
          <div className="section-header">
            <Calculator size={24} color="var(--primary-color)" />
            <h2>Input Parameters</h2>
          </div>
          
          {error && (
            <div style={{ display:'flex', alignItems:'center', gap:8, background:'rgba(239,83,80,0.12)', border:'1px solid rgba(239,83,80,0.4)', borderRadius:8, padding:'10px 14px', marginBottom:16 }}>
              <XCircle size={18} color="var(--danger)" />
              <span style={{ color:'#ff8a80', fontSize:'0.9rem' }}>{error}</span>
            </div>
          )}

          <form onSubmit={handlePredict} className="predict-form">
            <div className="form-group">
              <label><MapPin size={16}/> Country</label>
              <select name="country" value={formData.country} onChange={handleChange} className="input-field">
                {VALID_COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label><Sprout size={16}/> Crop Type</label>
              <select name="crop" value={formData.crop} onChange={handleChange} className="input-field">
                {crops.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label><Calendar size={16}/> Year</label>
              <input type="number" name="year" value={formData.year} onChange={handleChange} className="input-field" min="1990" max="2050" />
            </div>

            <div className="form-group">
              <label><CloudRain size={16}/> Rainfall (mm/year)</label>
              <input type="range" name="rainfall" min="50" max="3500" value={formData.rainfall} onChange={handleChange} className="slider" />
              <div className="slider-value">{formData.rainfall} mm</div>
            </div>

            <div className="form-group">
              <label><Thermometer size={16}/> Avg Temperature (°C)</label>
              <input type="range" name="temperature" min="-5" max="45" value={formData.temperature} onChange={handleChange} className="slider" />
              <div className="slider-value">{formData.temperature} °C</div>
            </div>

            <div className="form-group">
              <label><Bug size={16}/> Pesticide Usage (tonnes)</label>
              <input type="range" name="pesticide" min="0" max="10000" value={formData.pesticide} onChange={handleChange} className="slider" />
              <div className="slider-value">{formData.pesticide} tonnes</div>
            </div>

            <button type="submit" className="btn-primary full-width mt-4" disabled={loading}>
              {loading ? 'Analyzing...' : <>Calculate Yield <ArrowRight size={18} /></>}
            </button>
          </form>
        </div>

        {/* Results Section */}
        <div className="results-panel">
          {result ? (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}>
              <div className="glass-panel p-6 text-center highlight-card">
                <h3>Predicted Yield</h3>
                <div className="yield-value">
                  <span className="number">{(result.predicted_yield_hg_ha).toLocaleString(undefined, {maximumFractionDigits:0})}</span>
                  <span className="unit">hg/ha</span>
                </div>
                <div className="yield-secondary">
                  ~ {result.predicted_yield_tonnes_ha.toFixed(2)} Tonnes / Hectare
                </div>
                <div className={`yield-badge ${result.yield_level.toLowerCase()}`}>
                  {result.yield_level} Yield Level
                </div>
              </div>

              <div className="glass-panel p-6 mt-6">
                <h3>GenAI Advisory Layer</h3>
                <div className="recommendations-list">
                  {result.recommendations.map((rec, idx) => (
                    <div key={idx} className="recommendation-item">
                      <div className="rec-icon">{getSeverityIcon(rec)}</div>
                      <div className="rec-text">{rec}</div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          ) : (
            <div className="glass-panel p-6 empty-state">
              <Sprout size={64} color="var(--surface-dark)" />
              <p>Enter parameters and calculate to see yield prediction and AI advisory.</p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default Predict;
