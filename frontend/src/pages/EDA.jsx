import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const EDA = () => {
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEDA = async () => {
      try {
        const token = localStorage.getItem('token');
        const headers = { Authorization: `Bearer ${token}` };
        const res = await axios.get('http://localhost:8000/eda/top_countries', { headers });
        setCountries(res.data.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchEDA();
  }, []);

  return (
    <motion.div className="animate-fade-in" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h2>Exploratory Data Analysis</h2>
      
      <div className="glass-panel" style={{ padding: '24px', marginTop: '24px' }}>
        <h3 style={{ marginTop: 0, marginBottom: '20px' }}>Top 20 Countries by Average Yield</h3>
        {loading ? (
          <div>Loading chart...</div>
        ) : (
          <div style={{ height: '500px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={countries} margin={{ bottom: 100 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="country" stroke="var(--text-muted)" angle={-45} textAnchor="end" interval={0} />
                <YAxis stroke="var(--text-muted)" />
                <Tooltip contentStyle={{ backgroundColor: 'var(--surface-dark)' }} />
                <Bar dataKey="avg_yield" fill="var(--primary-color)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default EDA;
