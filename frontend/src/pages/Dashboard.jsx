import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sprout, Globe, Activity, TrendingUp } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import axios from 'axios';

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [trends, setTrends] = useState([]);
  const [topCrops, setTopCrops] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEDA = async () => {
      try {
        const token = localStorage.getItem('token');
        const headers = { Authorization: `Bearer ${token}` };
        
        const [sumRes, trendRes, cropRes] = await Promise.all([
          axios.get('http://localhost:8000/eda/summary', { headers }),
          axios.get('http://localhost:8000/eda/yearly_trend', { headers }),
          axios.get('http://localhost:8000/eda/crop_yield', { headers })
        ]);
        
        setSummary(sumRes.data.data);
        setTrends(trendRes.data.data);
        setTopCrops(cropRes.data.data.sort((a,b) => b.avg_yield - a.avg_yield).slice(0, 5));
      } catch (e) {
        console.error("Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };
    fetchEDA();
  }, []);

  if (loading) return <div className="p-6 text-center">Loading Dashboard...</div>;

  return (
    <motion.div className="animate-fade-in" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2>Dashboard Overview</h2>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ background: 'rgba(46, 125, 50, 0.2)', padding: '12px', borderRadius: '12px' }}>
            <Activity color="var(--primary-light)" size={28} />
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Dataset Size</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{summary?.total_records.toLocaleString()}</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ background: 'rgba(245, 176, 65, 0.2)', padding: '12px', borderRadius: '12px' }}>
            <Sprout color="var(--secondary-color)" size={28} />
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Crops Tracked</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{summary?.unique_crops}</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ background: 'rgba(14, 165, 233, 0.2)', padding: '12px', borderRadius: '12px' }}>
            <Globe color="var(--info)" size={28} />
          </div>
          <div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Countries</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{summary?.unique_countries}</div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '24px' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ marginTop: 0, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={20} color="var(--primary-color)" /> Global Yield Trend
          </h3>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends}>
                <defs>
                  <linearGradient id="colorYield" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--primary-color)" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="var(--primary-color)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="year" stroke="var(--text-muted)" />
                <YAxis stroke="var(--text-muted)" />
                <Tooltip contentStyle={{ backgroundColor: 'var(--surface-dark)', borderColor: 'var(--primary-color)' }} />
                <Area type="monotone" dataKey="avg_yield" stroke="var(--primary-color)" fillOpacity={1} fill="url(#colorYield)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ marginTop: 0, marginBottom: '20px' }}>Top Crops</h3>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topCrops} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis type="number" stroke="var(--text-muted)" />
                <YAxis dataKey="crop" type="category" stroke="var(--text-muted)" width={80} />
                <Tooltip contentStyle={{ backgroundColor: 'var(--surface-dark)' }} />
                <Bar dataKey="avg_yield" fill="var(--secondary-color)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default Dashboard;
