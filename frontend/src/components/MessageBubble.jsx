/**
 * components/MessageBubble.jsx
 * Renders a single chat message — handles user, AI, GitHub, system, and error roles.
 */

import { marked } from 'marked';
import { useMemo } from 'react';

// Configure marked for safe rendering
marked.setOptions({ breaks: true, gfm: true });

/** Format an ISO timestamp to a short local time string. */
const formatTime = (iso) =>
  new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

/** ── GitHub Repo Info Card ──────────────────────────── */
const RepoCard = ({ info }) => (
  <div style={{
    background: 'rgba(88, 166, 255, 0.08)',
    border: '1px solid rgba(88, 166, 255, 0.2)',
    borderRadius: '12px',
    padding: '14px 16px',
    marginBottom: '14px',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  }}>
    {/* Repo name + link */}
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" style={{ color: '#58a6ff', flexShrink: 0 }}>
        <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
      </svg>
      <a
        href={info.url}
        target="_blank"
        rel="noopener noreferrer"
        style={{ color: '#58a6ff', fontWeight: 600, fontSize: '14px', textDecoration: 'none' }}
      >
        {info.full_name}
      </a>
    </div>

    {/* Description */}
    {info.description && (
      <p style={{ color: '#94a3b8', fontSize: '13px' }}>{info.description}</p>
    )}

    {/* Stats row */}
    <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
      {info.language && <Stat icon="🔵" label={info.language} />}
      <Stat icon="⭐" label={`${info.stars.toLocaleString()} stars`} />
      <Stat icon="🍴" label={`${info.forks.toLocaleString()} forks`} />
      <Stat icon="🐛" label={`${info.open_issues} issues`} />
      {info.license && <Stat icon="📄" label={info.license} />}
    </div>

    {/* Topics */}
    {info.topics?.length > 0 && (
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
        {info.topics.slice(0, 6).map((t) => (
          <span key={t} style={{
            fontSize: '11px', padding: '2px 8px',
            background: 'rgba(88, 166, 255, 0.12)',
            color: '#58a6ff', borderRadius: '20px',
            border: '1px solid rgba(88, 166, 255, 0.25)',
          }}>
            {t}
          </span>
        ))}
      </div>
    )}
  </div>
);

const Stat = ({ icon, label }) => (
  <span style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '4px' }}>
    {icon} {label}
  </span>
);

/** ── Welcome System Message ─────────────────────────── */
const WelcomeMessage = () => (
  <div style={{ textAlign: 'center', padding: '40px 20px' }}>
    <div style={{
      width: 64, height: 64, borderRadius: '50%', margin: '0 auto 16px',
      background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontSize: '28px', boxShadow: '0 0 32px rgba(99,102,241,0.4)'
    }}>🤖</div>
    <h2 style={{ fontSize: '22px', fontWeight: 700, marginBottom: '8px' }}>
      <span className="text-gradient">SmartAI Agent</span>
    </h2>
    <p style={{ color: '#94a3b8', fontSize: '14px', maxWidth: '380px', margin: '0 auto 20px' }}>
      Ask me anything, or paste a GitHub repository URL in the sidebar to get an AI-powered analysis.
    </p>
    <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
      {['Explain a concept', 'Review my code', 'Analyze a GitHub repo', 'Debug an error'].map((s) => (
        <span key={s} style={{
          fontSize: '12px', padding: '6px 14px',
          background: 'rgba(99,102,241,0.12)',
          color: '#a5b4fc', borderRadius: '20px',
          border: '1px solid rgba(99,102,241,0.2)',
        }}>
          {s}
        </span>
      ))}
    </div>
  </div>
);

/** ── Main MessageBubble Component ───────────────────── */
const MessageBubble = ({ message }) => {
  // Render markdown safely
  const htmlContent = useMemo(() => {
    if (message.role === 'user' || message.role === 'system' || message.role === 'error') {
      return null;
    }
    return marked.parse(message.content || '');
  }, [message]);

  // ── System / Welcome message ──
  if (message.role === 'system') return <WelcomeMessage />;

  // ── Error message ──
  if (message.role === 'error') {
    return (
      <div className="fade-in" style={{
        margin: '8px 16px',
        padding: '12px 16px',
        background: 'rgba(239,68,68,0.1)',
        border: '1px solid rgba(239,68,68,0.25)',
        borderRadius: '12px',
        color: '#fca5a5',
        fontSize: '13px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
      }}>
        ⚠️ {message.content}
      </div>
    );
  }

  const isUser = message.role === 'user';

  return (
    <div
      className="fade-in"
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        gap: '10px',
        padding: '6px 16px',
        alignItems: 'flex-start',
      }}
    >
      {/* Avatar */}
      <div style={{
        width: 34, height: 34, borderRadius: '50%', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: '16px',
        background: isUser
          ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
          : message.role === 'github'
            ? 'rgba(88, 166, 255, 0.15)'
            : 'rgba(255,255,255,0.07)',
        border: isUser ? 'none' : '1px solid rgba(255,255,255,0.1)',
        boxShadow: isUser ? '0 2px 12px rgba(99,102,241,0.35)' : 'none',
      }}>
        {isUser ? '👤' : message.role === 'github' ? '🐙' : '🤖'}
      </div>

      {/* Bubble */}
      <div style={{ maxWidth: '78%', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {/* Role label */}
        <span style={{
          fontSize: '11px', color: '#475569', fontWeight: 500,
          textAlign: isUser ? 'right' : 'left',
        }}>
          {isUser ? 'You' : message.role === 'github' ? '🐙 GitHub Analysis' : '🤖 SmartAI'}
          {' · '}
          {formatTime(message.timestamp)}
        </span>

        {/* Message content */}
        <div style={{
          padding: isUser ? '10px 14px' : '14px 16px',
          borderRadius: isUser ? '20px 4px 20px 20px' : '4px 20px 20px 20px',
          background: isUser
            ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
            : message.role === 'github'
              ? 'rgba(88,166,255,0.06)'
              : 'rgba(255,255,255,0.05)',
          border: isUser ? 'none' : '1px solid rgba(255,255,255,0.08)',
          color: isUser ? 'white' : '#e2e8f0',
          fontSize: '14px',
          lineHeight: 1.65,
          boxShadow: isUser ? '0 4px 20px rgba(99,102,241,0.3)' : 'var(--shadow-sm)',
          wordBreak: 'break-word',
          whiteSpace: isUser ? 'pre-wrap' : 'normal',
        }}>
          {/* Repo info card (GitHub messages only) */}
          {message.role === 'github' && message.repoInfo && (
            <RepoCard info={message.repoInfo} />
          )}

          {/* Rendered markdown (AI / GitHub) */}
          {!isUser && (
            <div
              className="message-content"
              dangerouslySetInnerHTML={{ __html: htmlContent }}
            />
          )}

          {/* Plain text (user messages) */}
          {isUser && message.content}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;

