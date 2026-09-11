import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  CartesianGrid
} from 'recharts';

export default function SiteAnalyticsModal({ site, onClose }) {
  if (!site) return null;

  // 12-month synthetic curve derived from site solar GHI & wind telemetry
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const baseSolar = (site.solar_ghi || 5.5) * 20;
  const baseWind = (site.wind_speed_100m || 6.8) * 15;

  const timeSeriesData = months.map((m, idx) => {
    const sFactor = [6, 7].includes(idx) ? 0.75 : [2, 3, 4].includes(idx) ? 1.15 : 1.0;
    const wFactor = [5, 6, 7].includes(idx) ? 1.3 : 0.85;
    const solar = Math.round(baseSolar * sFactor);
    const wind = Math.round(baseWind * wFactor);
    return {
      month: m,
      Solar: solar,
      Wind: wind,
      HybridCombined: solar + wind
    };
  });

  // Financial & Technology Comparison Data
  const financialData = [
    { tech: 'Solar PV', lcoe: 36.5, capex: 145 },
    { tech: 'Wind Farm', lcoe: 41.0, capex: 185 },
    { tech: 'Hybrid System', lcoe: 33.8, capex: 290 }
  ];

  // MCDM 5-Factor Radar/Bar Data
  const factorData = [
    { factor: 'Resource (35%)', score: 8.8 },
    { factor: 'Terrain (25%)', score: 7.9 },
    { factor: 'Infra (15%)', score: 8.4 },
    { factor: 'Environment (15%)', score: 9.1 },
    { factor: 'Economic (10%)', score: 8.0 }
  ];

  return (
    <div style={backdropStyle}>
      <div style={modalWindowStyle}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '18px', color: '#f8fafc' }}>
              📊 Site Analytics & Performance Telemetry: {site.site_name}
            </h2>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>
              Module 11 Live Interactive Analytics Engine
            </span>
          </div>
          <button onClick={onClose} style={closeBtnStyle}>✕</button>
        </div>

        {/* Grid of Charts */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          {/* Chart 1: 12-Month Generation Time-Series */}
          <div style={chartBoxStyle}>
            <h4 style={chartTitleStyle}>⚡ 12-Month Generation Curve (GWh)</h4>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={timeSeriesData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Area type="monotone" dataKey="Solar" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.4} />
                <Area type="monotone" dataKey="Wind" stackId="1" stroke="#38bdf8" fill="#38bdf8" fillOpacity={0.4} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Chart 2: LCOE vs CAPEX Financial Tradeoff */}
          <div style={chartBoxStyle}>
            <h4 style={chartTitleStyle}>💰 Technology LCOE ($/MWh) vs CAPEX ($M)</h4>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={financialData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="tech" stroke="#64748b" fontSize={11} />
                <YAxis stroke="#64748b" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Bar dataKey="lcoe" name="LCOE ($/MWh)" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="capex" name="CAPEX ($M)" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 3: MCDM 5-Factor Suitability Breakdown */}
        <div style={{ ...chartBoxStyle, marginTop: '16px' }}>
          <h4 style={chartTitleStyle}>🎯 MCDM 5-Factor Weighted Criteria Performance (Scale: 0-10)</h4>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={factorData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis type="number" domain={[0, 10]} stroke="#64748b" fontSize={11} />
              <YAxis dataKey="factor" type="category" stroke="#64748b" fontSize={11} width={130} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155' }} />
              <Bar dataKey="score" fill="#38bdf8" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

const backdropStyle = {
  position: 'fixed',
  inset: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.75)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 200,
  padding: '16px'
};

const modalWindowStyle = {
  backgroundColor: '#0a101d',
  border: '1px solid #1e293b',
  borderRadius: '12px',
  width: '100%',
  maxWidth: '900px',
  maxHeight: '90vh',
  overflowY: 'auto',
  padding: '24px'
};

const chartBoxStyle = {
  backgroundColor: '#0d1526',
  border: '1px solid #142033',
  borderRadius: '8px',
  padding: '12px'
};

const chartTitleStyle = {
  margin: '0 0 10px 0',
  fontSize: '13px',
  color: '#e2e8f0'
};

const closeBtnStyle = {
  background: 'transparent',
  border: 'none',
  color: '#94a3b8',
  fontSize: '18px',
  cursor: 'pointer'
};