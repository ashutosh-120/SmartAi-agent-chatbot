/**
 * hooks/useChat.js — Chat + Analysis State Management Hook
 * Manages messages, analysis results, loading states, and error handling.
 */

import { useState, useCallback } from 'react';
import { chatWithAI, analyzeGitHubRepo, runFullAnalysis } from '../services/api';

const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;

const createMessage = (role, content, extra = {}) => ({
  id: generateId(),
  role,
  content,
  timestamp: new Date().toISOString(),
  ...extra,
});

export const useChat = () => {
  const [messages, setMessages]         = useState([createMessage('system', 'welcome')]);
  const [isLoading, setIsLoading]       = useState(false);
  const [error, setError]               = useState(null);

  // ── Full analysis state (for AnalysisPanel) ──────────────
  const [analysisData, setAnalysisData]   = useState(null);
  const [analysisRepo, setAnalysisRepo]   = useState('');
  const [isAnalyzing, setIsAnalyzing]     = useState(false);
  const [analysisError, setAnalysisError] = useState(null);

  // ──────────────────────────────────────────
  //  1. Chat with Gemini (multi-turn)
  // ──────────────────────────────────────────
  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isLoading) return;
    setError(null);
    const userMessage = createMessage('user', text);
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const history = messages
        .filter(m => m.role === 'user' || m.role === 'assistant')
        .map(m => ({ role: m.role === 'assistant' ? 'model' : 'user', content: m.content }));

      const data = await chatWithAI(text, history);
      setMessages(prev => [...prev, createMessage('assistant', data.reply, { model: data.model })]);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Something went wrong.';
      setError(msg);
      setMessages(prev => [...prev, createMessage('error', msg)]);
    } finally {
      setIsLoading(false);
    }
  }, [messages, isLoading]);

  // ──────────────────────────────────────────
  //  2. Quick GitHub AI Q&A (old analyze)
  // ──────────────────────────────────────────
  const analyzeRepo = useCallback(async (repoUrl, question = '') => {
    if (!repoUrl.trim() || isLoading) return;
    setError(null);
    setMessages(prev => [...prev, createMessage('user',
      question ? `Analyze: ${repoUrl}\n\nQuestion: ${question}` : `Analyze GitHub repo: ${repoUrl}`
    )]);
    setIsLoading(true);

    try {
      const data = await analyzeGitHubRepo(repoUrl, question);
      setMessages(prev => [...prev, createMessage('github', data.ai_analysis, {
        repoInfo: data.repo_info,
        readmePreview: data.readme_preview,
      })]);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Failed to analyze repository.';
      setError(msg);
      setMessages(prev => [...prev, createMessage('error', msg)]);
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  // ──────────────────────────────────────────
  //  3. Full Analysis Pipeline ← NEW
  //     GitHub URL → skills → trends → roadmap
  // ──────────────────────────────────────────
  const runAnalysis = useCallback(async (repoUrl, careerGoal = null) => {
    if (!repoUrl.trim() || isAnalyzing) return;
    setAnalysisError(null);
    setAnalysisData(null);
    setAnalysisRepo(repoUrl);
    setIsAnalyzing(true);

    // Show in-chat loading message
    const userMsg = createMessage('user',
      `🔍 Full analysis: ${repoUrl}${careerGoal ? `\n🎯 Goal: ${careerGoal}` : ''}`
    );
    setMessages(prev => [...prev, userMsg]);

    try {
      const data = await runFullAnalysis(repoUrl, careerGoal);
      setAnalysisData(data);
      setAnalysisRepo(data.repo_name || repoUrl);

      // Brief summary in chat
      setMessages(prev => [...prev, createMessage('analysis', 'analysis_complete', {
        skillScore:  data.skill_score,
        skillLevel:  data.skill_level,
        skillCount:  data.skills?.length || 0,
        repoName:    data.repo_name,
        careerPaths: data.career_paths?.slice(0, 3),
      })]);
    } catch (err) {
      let msg = 'Analysis failed.';
      if (err.response) {
        // Server responded with an error code (4xx, 5xx)
        msg = err.response.data?.detail || `Server error: ${err.response.status}`;
      } else if (err.request) {
        // Request was made but no response was received (Network Error)
        msg = 'Connection failed. Ensure the backend server is running and check your network.';
        if (err.code === 'ECONNABORTED') msg = 'Request timed out. The repository might be too large.';
      } else {
        msg = err.message;
      }
      setAnalysisError(msg);
      setMessages(prev => [...prev, createMessage('error', `Analysis failed: ${msg}`)]);
    } finally {
      setIsAnalyzing(false);
    }
  }, [isAnalyzing]);

  // ──────────────────────────────────────────
  //  Clear chat / reset analysis
  // ──────────────────────────────────────────
  const clearChat = useCallback(() => {
    setMessages([createMessage('system', 'welcome')]);
    setError(null);
    setAnalysisData(null);
    setAnalysisRepo('');
    setAnalysisError(null);
  }, []);

  return {
    // Chat
    messages, isLoading, error, sendMessage, analyzeRepo, clearChat,
    // Full analysis
    analysisData, analysisRepo, isAnalyzing, analysisError, runAnalysis,
  };
};
