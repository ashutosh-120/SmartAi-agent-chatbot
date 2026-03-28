/**
 * components/InputBar.jsx
 * Bottom chat input: auto-growing textarea + animated send button.
 */

import { useState, useRef, useEffect } from 'react';

const InputBar = ({ onSend, isLoading }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef(null);

  // Auto-grow textarea height as user types
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
  }, [text]);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    // Send on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const canSend = text.trim().length > 0 && !isLoading;

  return (
    <div style={{
      padding: '12px 16px 16px',
      borderTop: '1px solid rgba(255,255,255,0.07)',
      background: 'rgba(10,10,15,0.8)',
      backdropFilter: 'blur(20px)',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'flex-end',
        gap: '10px',
        background: 'rgba(255,255,255,0.05)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '16px',
        padding: '10px 12px',
        transition: 'border-color 0.2s',
      }}
        onFocus={() => {}}
        onBlur={() => {}}
      >
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={isLoading ? 'SmartAI is thinking...' : 'Ask anything, or paste a question... (Enter to send, Shift+Enter for newline)'}
          disabled={isLoading}
          rows={1}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: '#f1f5f9',
            fontSize: '14px',
            fontFamily: 'Inter, sans-serif',
            resize: 'none',
            lineHeight: 1.6,
            maxHeight: '160px',
            overflowY: 'auto',
            padding: 0,
          }}
        />

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={!canSend}
          title="Send message (Enter)"
          style={{
            width: 38, height: 38,
            borderRadius: '12px',
            border: 'none',
            cursor: canSend ? 'pointer' : 'not-allowed',
            background: canSend
              ? 'linear-gradient(135deg, #6366f1, #8b5cf6)'
              : 'rgba(255,255,255,0.07)',
            color: 'white',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
            transition: 'all 0.2s',
            transform: canSend ? 'scale(1)' : 'scale(0.95)',
            boxShadow: canSend ? '0 0 20px rgba(99,102,241,0.4)' : 'none',
            animation: canSend ? 'pulse-glow 2s infinite' : 'none',
          }}
        >
          {isLoading ? (
            /* Spinner */
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" strokeOpacity="0.3" />
              <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round">
                <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="0.8s" repeatCount="indefinite" />
              </path>
            </svg>
          ) : (
            /* Send arrow */
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          )}
        </button>
      </div>

      {/* Footer hint */}
      <p style={{ textAlign: 'center', color: '#334155', fontSize: '11px', marginTop: '8px' }}>
        SmartAI can make mistakes. Verify important information.
      </p>
    </div>
  );
};

export default InputBar;
