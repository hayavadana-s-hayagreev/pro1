import React from 'react';
import { motion } from 'framer-motion';
import { Database, FileCode2, GitBranch, Cpu, LineChart, Cpu as Brain } from 'lucide-react';

const Workflow = () => {
  const steps = [
    { icon: <Database />, title: '1. Raw Dataset', desc: 'FAO stat data containing crop yield, rainfall, pesticides, and temp (1990-2013).' },
    { icon: <FileCode2 />, title: '2. Feature Engineering', desc: 'Creation of interaction terms, ratios, rolling means, and label encoding.' },
    { icon: <GitBranch />, title: '3. Temporal Split', desc: 'Train: 1990-2009 | Test: 2010-2013 to respect time series nature.' },
    { icon: <Cpu />, title: '4. Model Training & HPO', desc: 'Train 5 models. Linear Regression, Random Forest, XGBoost, LightGBM, CatBoost with Optuna.' },
    { icon: <LineChart />, title: '5. FastAPI Backend', desc: 'Deployment of the best model (LinearRegression: R²=0.993) via REST API.' },
    { icon: <Brain />, title: '6. GenAI Advisory', desc: 'Rule-based expert system generates actionable insights based on prediction.' }
  ];

  return (
    <motion.div className="animate-fade-in" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <h2>System Architecture & Workflow</h2>
      <p style={{ color: 'var(--text-muted)' }}>Understanding the ML Pipeline</p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginTop: '32px' }}>
        {steps.map((step, idx) => (
          <motion.div 
            key={idx} 
            className="glass-panel" 
            style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '24px' }}
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: idx * 0.1 }}
          >
            <div style={{ background: 'rgba(46,125,50,0.2)', padding: '16px', borderRadius: '50%', color: 'var(--primary-color)' }}>
              {step.icon}
            </div>
            <div>
              <h3 style={{ margin: '0 0 8px 0' }}>{step.title}</h3>
              <p style={{ margin: 0, color: 'var(--text-muted)' }}>{step.desc}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default Workflow;
