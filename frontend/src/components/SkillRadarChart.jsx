/**
 * components/SkillRadarChart.jsx — Visualization of Skill Depth
 * Uses Chart.js to render a professional Radar chart.
 */

import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

const SkillRadarChart = ({ categories = {}, globalScore = 0 }) => {
  // ── Prepare Data ──────────────────────────────────────
  // We want 5-7 main axes for the radar
  const labels = Object.keys(categories).slice(0, 7);
  
  // If no categories, use defaults or return null
  if (labels.length < 3) return null;

  const dataValues = labels.map(cat => {
    // Basic scoring logic: more skills in a category = higher score (capped at 100)
    // We also factor in the global score to make it look realistic
    const skillCount = categories[cat]?.length || 0;
    const baseScore = globalScore > 0 ? globalScore : 50;
    return Math.min(baseScore + (skillCount * 5), 100);
  });

  const data = {
    labels,
    datasets: [
      {
        label: 'Skill Depth',
        data: dataValues,
        backgroundColor: 'rgba(99, 102, 241, 0.2)',
        borderColor: '#6366f1',
        borderWidth: 2,
        pointBackgroundColor: '#6366f1',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: '#6366f1',
      },
    ],
  };

  const options = {
    scales: {
      r: {
        angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        pointLabels: {
          color: '#94a3b8',
          font: { size: 10, weight: '600' }
        },
        ticks: { display: false, stepSize: 20 },
        suggestedMin: 0,
        suggestedMax: 100
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1e293b',
        titleColor: '#fff',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        padding: 10,
        displayColors: false
      }
    },
    maintainAspectRatio: false,
  };

  return (
    <div className="radar-chart-container" style={{ height: '240px', width: '100%', position: 'relative' }}>
      <Radar data={data} options={options} />
    </div>
  );
};

export default SkillRadarChart;
