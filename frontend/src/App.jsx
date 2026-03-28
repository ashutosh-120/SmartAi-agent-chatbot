/**
 * App.jsx — Root Application Component (Prompt-5 Enhanced)
 * Layout: Sidebar (left) | Chat (center/right) | AnalysisPanel (right panel)
 */

import { useState } from 'react';
import './index.css';
import Sidebar      from './components/Sidebar';
import ChatWindow   from './components/ChatWindow';
import AnalysisPanel from './components/AnalysisPanel';
import { useChat }  from './hooks/useChat';

function App() {
  const {
    messages, isLoading, sendMessage, analyzeRepo, clearChat,
    analysisData, analysisRepo, isAnalyzing, analysisError, runAnalysis,
  } = useChat();

  // Toggle analysis panel visibility
  const [showAnalysis, setShowAnalysis] = useState(false);

  // When analysis comes in, auto-show panel
  const handleAnalysis = async (repoUrl, careerGoal) => {
    setShowAnalysis(true);
    await runAnalysis(repoUrl, careerGoal);
  };

  return (
    <div className="app-root">
      {/* ── Left Sidebar ─────────────────────────────── */}
      <Sidebar
        onNewChat={clearChat}
        onAnalyze={analyzeRepo}
        onFullAnalysis={handleAnalysis}
        isLoading={isLoading || isAnalyzing}
        messageCount={messages.length}
      />

      {/* ── Center: Chat Area ─────────────────────────── */}
      <div className="chat-area">
        <header className="app-header">
          <div className="header-left">
            <div className="status-dot" />
            <span className="header-status">Connected to SmartAI Backend</span>
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
