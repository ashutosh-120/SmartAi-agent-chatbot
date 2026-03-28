/**
 * components/AnalysisPanel.jsx — Full Analysis Display Panel
 * Shows the complete analysis result: skill score, skills, missing skills,
 * career paths, and the Gemini-generated roadmap timeline.
 */

import { useState } from 'react';
import SkillCard from './SkillCard';
import CareerPaths from './CareerPaths';
import RoadmapTimeline from './RoadmapTimeline';

const TABS = [
  { id: 'skills',   icon: '🧠', label: 'Skills'         },
  { id: 'missing',  icon: '⚡', label: 'Missing Skills'  },
  { id: 'careers',  icon: '🎯', label: 'Career Paths'   },
  { id: 'roadmap',  icon: '🗺️', label: 'Roadmap'        },
];

/** Circular score ring component */
const ScoreRing = ({ score = 0, level = 'beginner' }) => {
  const color    = score >= 70 ? '#6fcf97' : score >= 40 ? '#f0a060' : '#eb5757';
  const levelClr = score >= 70 ? '#6fcf97' : score >= 40 ? '#f0a060' : '#eb5757';
  const pct      = Math.min(score, 100);

  return (
    <div className="score-ring-wrap">
      <svg viewBox="0 0 100 100" className="score-ring-svg">
        <circle cx="50" cy="50" r="42" fill="none" stroke="#1e2a38" strokeWidth="10" />
        <circle
          cx="50" cy="50" r="42" fill="none"
          stroke={color} strokeWidth="10"
          strokeDasharray={`${pct * 2.638} 263.8`}
          strokeLinecap="round"
          style={{ transform: 'rotate(-90deg)', transformOrigin: 'center', transition: 'stroke-dasharray 1s ease' }}
        />
      </svg>
      <div className="score-ring-label">
        <span className="score-number" style={{ color }}>{score}</span>
        <span className="score-text">/ 100</span>
      </div>
      <span className="score-level" style={{ color: levelClr }}>{level}</span>
    </div>
  );
};

const AnalysisPanel = ({ data, repoName }) => {
  const [activeTab, setActiveTab] = useState('skills');

  if (!data) return null;

  const {
    skills = [], matched_skills = [], missing_skills = [],
    career_paths = [], roadmap = '', skill_score = 0,
    confidence_score = 0, skill_level = 'beginner',
    skill_categories = {}, suggested_paths = [],
    frameworks = [], languages = [], project_type = '',
    complexity = '', roadmap_error = null,
  } = data;

  return (
    <div className="analysis-panel">
      {/* Header */}
      <div className="analysis-header">
        <div className="analysis-repo-info">
          <span className="analysis-icon">📦</span>
          <div>
            <h2 className="analysis-repo-name">{repoName || 'Repository Analysis'}</h2>
            <div className="analysis-meta">
              <span className="meta-pill">{project_type}</span>
              <span className="meta-pill">{complexity} complexity</span>
              <span className="meta-pill confidence">
                {(confidence_score * 100).toFixed(0)}% confidence
              </span>
            </div>
          </div>
        </div>
        <ScoreRing score={skill_score} level={skill_level} />
      </div>

      {/* Quick stats */}
      <div className="analysis-stats">
        {[
          { label: 'Skills Found',  value: skills.length,         icon: '🧠' },
          { label: 'Market Match',  value: matched_skills.length, icon: '✅' },
          { label: 'Skills to Add', value: missing_skills.length, icon: '⚡' },
          { label: 'Career Paths',  value: career_paths.length,   icon: '🎯' },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <span className="stat-icon">{s.icon}</span>
            <span className="stat-value">{s.value}</span>
            <span className="stat-label">{s.label}</span>
          </div>
        ))}
      </div>

      {/* Tab nav */}
      <div className="tab-nav">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
          >
            <span>{tab.icon}</span> {tab.label}
            {tab.id === 'skills'  && <span className="tab-count">{skills.length}</span>}
            {tab.id === 'missing' && <span className="tab-count">{missing_skills.length}</span>}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="tab-content">

        {activeTab === 'skills' && (
          <div>
            <div className="languages-row">
              <strong>Languages:</strong>
              {languages.map((l, i) => <SkillCard key={i} skill={l} category="Languages" />)}
              {frameworks.slice(0, 5).map((f, i) => <SkillCard key={i} skill={f} category="Frameworks" />)}
            </div>
            <div className="skills-by-category">
              {Object.entries(skill_categories).map(([cat, catSkills]) => (
                <div key={cat} className="skill-category-group">
                  <h4 className="category-label">{cat}</h4>
                  <div className="skill-tags-row">
                    {catSkills.map((s, i) => (
                      <SkillCard key={i} skill={s} category={cat} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'missing' && (
          <div>
            <p className="section-subtitle">
              These skills will help you reach your career goal faster:
            </p>
            <div className="missing-skills-grid">
              {missing_skills.length === 0 ? (
                <p className="empty-state">🎉 You have great coverage for market trends!</p>
              ) : (
                missing_skills.map((skill, i) => (
                  <div key={i} className="missing-skill-item">
                    <span className="missing-skill-num">#{i + 1}</span>
                    <span className="missing-skill-name">{skill}</span>
                    <span className="missing-skill-badge">Learn</span>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'careers' && (
          <CareerPaths paths={suggested_paths} missingSkills={missing_skills} />
        )}

        {activeTab === 'roadmap' && (
          <div>
            {roadmap_error && (
              <div className="roadmap-error-notice">
                ⚠️ Roadmap generation hit a rate limit. Try again in a moment.
              </div>
            )}
            {roadmap ? (
              <RoadmapTimeline roadmap={roadmap} />
            ) : (
              <div className="empty-state">
                {roadmap_error
                  ? 'Roadmap will appear here once generated.'
                  : 'No roadmap generated yet.'}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisPanel;
