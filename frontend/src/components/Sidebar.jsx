/**
 * components/Sidebar.jsx — Enhanced Sidebar (Prompt-5)
 * Adds: Full Analysis section with career goal selector, updated branding.
 */

import { useState } from 'react';
import GitHubInput from './GitHubInput';

const CAREER_GOALS = [
  'Auto-detect (Best Match)',
  'AI / Machine Learning Engineer',
  'Full Stack Web Developer',
  'Cloud / DevOps Engineer',
  'Mobile App Developer',
  'Data Engineer',
  'Backend / API Developer',
];

const Sidebar = ({ onNewChat, onAnalyze, onFullAnalysis, isLoading, messageCount, onClose }) => {
  const [repoUrl, setRepoUrl]       = useState('');
  const [careerGoal, setCareerGoal] = useState(CAREER_GOALS[0]);

  // Real-time validation
  const parts = repoUrl.trim().replace(/\/$/, '').split('/');
  const isProfile = parts.length === 4 && parts[2] === 'github.com';
  const isRepo = (parts.length >= 5 && parts[2] === 'github.com') || (parts.length === 2 && !repoUrl.includes('://'));
  const isValid = isRepo && !isProfile;

  const handleFullAnalysis = () => {
    if (!isValid || isLoading) return;
    const goal = careerGoal === CAREER_GOALS[0] ? null : careerGoal;
    onFullAnalysis(repoUrl.trim(), goal);
  };

  return (
    <aside className="sidebar">
      {/* ── Brand ──────────────────────────────────────── */}
      <div className="sidebar-brand">
        <div className="brand-icon">🤖</div>
        <div>
          <h1 className="brand-name"><span className="text-gradient">SmartAI</span></h1>
          <p className="brand-sub">Skill & Roadmap Analyzer</p>
        </div>
        <button className="btn btn-ghost sidebar-close" onClick={onClose}>
          ✕
        </button>
      </div>

      {/* ── New Chat ────────────────────────────────────── */}
      <button onClick={onNewChat} className="btn btn-ghost new-chat-btn">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        New Chat
        {messageCount > 1 && (
          <span className="msg-count">{messageCount - 1} msg{messageCount !== 2 ? 's' : ''}</span>
        )}
      </button>

      <div className="sidebar-divider" />

      {/* ── Full Analysis Pipeline ──────────────────────── */}
      <div className="sidebar-section">
        <div className="section-label">
          <span>🔬</span> Full Analysis
        </div>
        <p className="section-hint">GitHub → Skills → Trends → Roadmap</p>

        <input
          className="url-input"
          type="url"
          placeholder="https://github.com/owner/repo"
          value={repoUrl}
          onChange={e => setRepoUrl(e.target.value)}
          disabled={isLoading}
        />

        {isProfile && (
          <p style={{ fontSize: '10px', color: '#f59e0b', marginTop: '-4px' }}>
            ⚠️ Profile URL detected. Need /owner/repo
          </p>
        )}

        <select
          className="career-select"
          value={careerGoal}
          onChange={e => setCareerGoal(e.target.value)}
          disabled={isLoading}
        >
          {CAREER_GOALS.map(g => (
            <option key={g} value={g}>{g}</option>
          ))}
        </select>

        <button
          className="btn btn-primary analyze-btn"
          onClick={handleFullAnalysis}
          disabled={isLoading || !isValid}
        >
          {isLoading ? (
            <><span className="spinner-sm" /> Analyzing…</>
          ) : (
            <><span>🚀</span> Run Full Analysis</>
          )}
        </button>
      </div>

      <div className="sidebar-divider" />

      {/* ── Quick GitHub Q&A ───────────────────────────── */}
      <div className="sidebar-section">
        <div className="section-label">
          <span>⚡</span> Quick AI Q&A
        </div>
        <p className="section-hint">Ask anything about a GitHub repo.</p>
        <GitHubInput onAnalyze={onAnalyze} isLoading={isLoading} />
      </div>

      <div className="sidebar-divider" />

      {/* ── Features ───────────────────────────────────── */}
      <div className="capabilities">
        <p className="cap-label">CAPABILITIES</p>
        {[
          { icon: '🧠', label: 'Skill extraction engine' },
          { icon: '📊', label: 'Market trend matching' },
          { icon: '🗺️', label: 'AI roadmap generation' },
          { icon: '💬', label: 'Multi-turn chat' },
          { icon: '🔍', label: 'GitHub repo analysis' },
          { icon: '⚡', label: 'Gemini 2.0 Flash' },
        ].map(({ icon, label }) => (
          <div key={label} className="cap-item">
            <span>{icon}</span> {label}
          </div>
        ))}
      </div>
    </aside>
  );
};

export default Sidebar;
