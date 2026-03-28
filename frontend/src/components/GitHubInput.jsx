/**
 * components/GitHubInput.jsx
 * GitHub repository URL input with optional custom question.
 */

import { useState } from 'react';

const GitHubInput = ({ onAnalyze, isLoading }) => {
  const [repoUrl, setRepoUrl]   = useState('');
  const [question, setQuestion] = useState('');
  const [expanded, setExpanded] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!repoUrl.trim() || isLoading) return;
    onAnalyze(repoUrl.trim(), question.trim());
    setRepoUrl('');
    setQuestion('');
    setExpanded(false);
  };

  const parts = repoUrl.trim().replace(/\/$/, '').split('/');
  const isProfile = parts.length === 4 && parts[2] === 'github.com'; // ['https:', '', 'github.com', 'user']
  const isRepo = (parts.length >= 5 && parts[2] === 'github.com') || (parts.length === 2 && !repoUrl.includes('://'));
  const isValid = isRepo && !isProfile;

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {/* URL Input */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        background: 'rgba(255,255,255,0.05)',
        border: `1px solid ${isValid ? 'rgba(88,166,255,0.4)' : 'rgba(255,255,255,0.1)'}`,
        borderRadius: '10px',
        padding: '8px 10px',
        transition: 'border-color 0.2s',
      }}>
        {/* GitHub icon */}
        <svg width="16" height="16" viewBox="0 0 16 16" fill="rgba(88,166,255,0.7)" style={{ flexShrink: 0 }}>
          <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
        </svg>
        <input
          type="url"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          placeholder="https://github.com/owner/repo"
          style={{
            flex: 1, background: 'transparent', border: 'none', outline: 'none',
            color: '#f1f5f9', fontSize: '12px', fontFamily: 'Inter, sans-serif',
          }}
        />
        {/* Toggle custom question */}
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          title="Add a custom question"
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: expanded ? '#6366f1' : '#475569', fontSize: '14px',
            transition: 'color 0.2s', padding: '0 2px',
          }}
        >
          ✏️
        </button>
      </div>

      {/* Profile URL Warning */}
      {isProfile && (
        <p style={{ fontSize: '11px', color: '#f59e0b', margin: '2px 0 4px', padding: '0 4px' }}>
          ⚠️ This looks like a profile. Please provide a repository URL (e.g. /owner/repo).
        </p>
      )}

      {/* Optional question input */}
      {expanded && (
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a specific question about the repo..."
          style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '10px',
            padding: '8px 12px',
            color: '#f1f5f9',
            fontSize: '12px',
            fontFamily: 'Inter, sans-serif',
            outline: 'none',
          }}
        />
      )}

      {/* Analyze Button */}
      <button
        type="submit"
        disabled={!isValid || isLoading}
        className="btn btn-primary"
        style={{ fontSize: '12px', padding: '9px 14px' }}
      >
        {isLoading ? (
          <>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" strokeOpacity="0.3"/>
              <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round">
                <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="0.8s" repeatCount="indefinite"/>
              </path>
            </svg>
            Analyzing...
          </>
        ) : (
          <>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            Analyze Repo
          </>
        )}
      </button>
    </form>
  );
};

export default GitHubInput;
