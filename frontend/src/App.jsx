/**
 * App.jsx — Root Application Component
 * Routes between AuthPage (logged out) and main app (logged in)
 */

import { useState } from 'react';
import './index.css';
import Sidebar       from './components/Sidebar';
import ChatWindow    from './components/ChatWindow';
import AnalysisPanel from './components/AnalysisPanel';
import AuthPage      from './pages/AuthPage';
import { useChat }   from './hooks/useChat';
import { useAuth }   from './hooks/useAuth.jsx';

function App() {
  const { user, loading, signOut } = useAuth();

  const {
    messages, isLoading, sendMessage, analyzeRepo, clearChat,
    analysisData, analysisRepo, isAnalyzing, analysisError, runAnalysis,
    history, isHistoryLoading, loadAnalysis,
  } = useChat();

  const [showAnalysis, setShowAnalysis] = useState(false);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);

  const handleAnalysis = async (repoUrl, careerGoal) => {
    setShowAnalysis(true);
    setShowMobileSidebar(false);
    await runAnalysis(repoUrl, careerGoal);
  };

  const handleLoadHistory = (item) => {
    loadAnalysis(item);
    setShowAnalysis(true);
    setShowMobileSidebar(false);
  };

  // ── Loading state while Supabase checks the session ──
  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100dvh', alignItems: 'center', justifyContent: 'center', background: 'var(--bg-primary)' }}>
        <div className="spinner large" />
      </div>
    );
  }

  // ── Not logged in → show Auth page ──
  if (!user) {
    return <AuthPage />;
  }

  // ── Logged in → show the main app ──
  return (
    <div className={`app-root ${showMobileSidebar ? 'sidebar-open' : ''} ${showAnalysis ? 'pane-open' : ''}`}>
      {/* ── Mobile Backdrop ──────────────────────────── */}
      <div
        className="mobile-backdrop"
        onClick={() => { setShowMobileSidebar(false); setShowAnalysis(false); }}
      />

      {/* ── Left Sidebar ─────────────────────────────── */}
      <Sidebar
        onNewChat={clearChat}
        onAnalyze={(url) => { analyzeRepo(url); setShowMobileSidebar(false); }}
        onFullAnalysis={handleAnalysis}
        isLoading={isLoading || isAnalyzing}
        messageCount={messages.length}
        showMobile={showMobileSidebar}
        onClose={() => setShowMobileSidebar(false)}
        user={user}
        onSignOut={signOut}
        history={history}
        isHistoryLoading={isHistoryLoading}
        onLoadAnalysis={handleLoadHistory}
      />

      {/* ── Center: Chat Area ─────────────────────────── */}
      <div className="chat-area">
        <header className="app-header">
          <div className="header-left">
            <button
              className="btn btn-ghost menu-toggle"
              onClick={() => setShowMobileSidebar(v => !v)}
            >
              ☰
            </button>
            <div className="status-dot" />
            <span className="header-status">SmartAI Developer Intelligence</span>
          </div>
          <div className="header-right">
            <span className="model-badge">Gemini 2.0 Flash</span>
            {analysisData && (
              <button
                className="btn btn-ghost analysis-toggle"
                onClick={() => setShowAnalysis(v => !v)}
              >
                {showAnalysis ? '◀ Hide' : '▶ Analysis'}
              </button>
            )}
          </div>
        </header>

        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onSend={sendMessage}
        />
      </div>

      {/* ── Right: Analysis Panel (slide in when visible) */}
      {showAnalysis && (
        <div className="analysis-pane">
          {isAnalyzing ? (
            <div className="analysis-loading">
              <div className="spinner large" />
              <p>Running full analysis…</p>
              <p className="analysis-steps">
                Fetching repo → Extracting skills → Matching trends → Generating roadmap
              </p>
            </div>
          ) : analysisError ? (
            <div className="analysis-error">
              <span>❌</span>
              <p>{analysisError}</p>
            </div>
          ) : (
            <AnalysisPanel data={analysisData} repoName={analysisRepo} />
          )}
        </div>
      )}
    </div>
  );
}

export default App;
