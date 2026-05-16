import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Clock, Calculator } from 'lucide-react';
import axios from 'axios';

const History = () => {
  const [history, setHistory] = useState({ predictions: [], searches: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get('http://localhost:8000/history', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setHistory(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  return (
    <motion.div className="animate-fade-in" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h2>Activity History</h2>
      
      <div className="glass-panel" style={{ padding: '24px', marginTop: '24px' }}>
        <h3 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Clock size={20} color="var(--secondary-color)"/> Recent Predictions
        </h3>
        
        {loading ? <p>Loading...</p> : (
          history.predictions.length === 0 ? <p style={{ color: 'var(--text-muted)' }}>No predictions made yet.</p> :
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {history.predictions.map(pred => (
              <div key={pred.id} style={{ padding: '16px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 'bold' }}>{pred.data.inputs.crop} in {pred.data.inputs.country} ({pred.data.inputs.year})</div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                    {new Date(pred.timestamp).toLocaleString()}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: 'var(--success)', fontWeight: 'bold' }}>{Math.round(pred.data.predicted_yield_hg_ha).toLocaleString()} hg/ha</div>
                  <div style={{ fontSize: '0.85rem' }}>{pred.data.yield_level} Level</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default History;
