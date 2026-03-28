/**
 * components/ChatWindow.jsx
 * Main chat area: scrollable message list with auto-scroll and loading indicator.
 */

import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import InputBar from './InputBar';

const ChatWindow = ({ messages, isLoading, onSend }) => {
  const bottomRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      flex: 1,
      overflow: 'hidden',
      background: 'linear-gradient(180deg, #0a0a0f 0%, #0c0c16 100%)',
    }}>
      {/* ── Message List ─────────────────────────────── */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px 0 8px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
      }}>
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Typing indicator while loading */}
        {isLoading && (
          <div className="fade-in" style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '6px 16px',
          }}>
            {/* AI avatar */}
            <div style={{
              width: 34, height: 34, borderRadius: '50%',
              background: 'rgba(255,255,255,0.07)',
              border: '1px solid rgba(255,255,255,0.1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '16px', flexShrink: 0,
            }}>🤖</div>

            {/* Animated dots */}
            <div style={{
              padding: '12px 18px',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: '4px 20px 20px 20px',
            }}>
              <div className="loading-dots">
                <span /><span /><span />
              </div>
            </div>
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={bottomRef} />
      </div>

      {/* ── Input Bar ────────────────────────────────── */}
      <InputBar onSend={onSend} isLoading={isLoading} />
    </div>
  );
};

export default ChatWindow;
