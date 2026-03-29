/**
 * components/LanguageBreakdown.jsx — Visualization of Programming Languages
 * Uses Chart.js Doughnut chart.
 */

import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

const LanguageBreakdown = ({ languages = [] }) => {
  // If no language data, return null
  if (!languages || languages.length === 0) return null;

  // ── Prepare Data ──────────────────────────────────────
  // Top 5 languages + others
  const topLangs = languages.slice(0, 5);
  const dataValues = topLangs.map(l => l.percent || 10);
  const labels     = topLangs.map(l => l.name);

  const colors = [
    '#6366f1', // Indigo
    '#10b981', // Emerald
    '#f59e0b', // Amber
    '#ef4444', // Red
    '#8b5cf6', // Violet
  ];

  const data = {
    labels,
    datasets: [
      {
        data: dataValues,
        backgroundColor: colors.slice(0, labels.length),
        borderColor: 'rgba(255, 255, 255, 0.05)',
        borderWidth: 2,
        hoverOffset: 15,
      },
    ],
  };

  const options = {
    cutout: '75%',
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#fff',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        displayColors: true,
        callbacks: {
          label: (ctx) => ` ${ctx.label}: ${ctx.formattedValue}%`
        }
      }
    },
    maintainAspectRatio: false,
  };

  return (
    <div className="language-chart-container" style={{ height: '180px', width: '100%', position: 'relative' }}>
      <Doughnut data={data} options={options} />
      <div className="chart-center-label" style={{ 
        position: 'absolute', 
        top: '50%', 
        left: '50%', 
        transform: 'translate(-50%, -50%)',
        textAlign: 'center',
        paddingTop: '5px'
      }}>
        <div style={{ fontSize: '10px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '1px' }}>Core</div>
        <div style={{ fontSize: '16px', fontWeight: '700', color: '#fff' }}>{labels[0]}</div>
      </div>
    </div>
  );
};

export default LanguageBreakdown;
