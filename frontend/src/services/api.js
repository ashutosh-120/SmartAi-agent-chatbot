/**
 * services/api.js — Axios API Client
 * Centralises all HTTP calls to the FastAPI backend.
 * Base URL reads from VITE_API_URL env var for deployment flexibility.
 */

import axios from 'axios';

// ── Base URL: env var for prod, localhost for dev ──────────
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/** Axios instance with default config */
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 90000, // 90s — Gemini roadmap generation can take ~30-60s
});

// ──────────────────────────────────────────
//  Chat API
// ──────────────────────────────────────────

/**
 * Send a message to Gemini AI (multi-turn).
 * @param {string} message  - User's message.
 * @param {Array}  history  - Previous conversation turns.
 */
export const chatWithAI = async (message, history = []) => {
  const response = await apiClient.post('/api/chat', { message, history });
  return response.data;
};

// ──────────────────────────────────────────
//  GitHub Quick Analyze (AI Q&A)
// ──────────────────────────────────────────

/**
 * Analyze a GitHub repo with AI (natural language Q&A).
 * @param {string} repoUrl  - Full GitHub URL.
 * @param {string} question - Optional custom question.
 */
export const analyzeGitHubRepo = async (repoUrl, question = '') => {
  const response = await apiClient.post('/api/github/analyze', {
    repo_url: repoUrl,
    question: question || undefined,
  });
  return response.data;
};

// ──────────────────────────────────────────
//  Full Analysis Pipeline  ← NEW
// ──────────────────────────────────────────

/**
 * Run the complete analysis pipeline:
 *   GitHub repo → skills → market trends → Gemini roadmap
 *
 * @param {string} repoUrl    - GitHub repository URL.
 * @param {string} careerGoal - Optional target career (e.g. "AI / Machine Learning Engineer").
 * @returns {Promise<{
 *   skills: string[], matched_skills: string[], missing_skills: string[],
 *   career_paths: string[], roadmap: string, skill_score: number,
 *   confidence_score: number, skill_level: string, suggested_paths: Array,
 *   skill_categories: object, frameworks: string[], languages: string[],
 *   project_type: string, complexity: string, repo_name: string
 * }>}
 */
export const runFullAnalysis = async (repoUrl, careerGoal = null) => {
  const payload = { repo_url: repoUrl };
  if (careerGoal) payload.career_goal = careerGoal;

  const response = await apiClient.post('/analyze', payload);
  return response.data;
};

// ──────────────────────────────────────────
//  Skill Extraction (standalone)
// ──────────────────────────────────────────

/**
 * Extract skills from a repo without running the full pipeline.
 * @param {string} repoUrl - GitHub URL.
 */
export const extractSkills = async (repoUrl) => {
  const response = await apiClient.post('/api/github/skills', { repo_url: repoUrl });
  return response.data;
};

// ──────────────────────────────────────────
//  Health Check
// ──────────────────────────────────────────

export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};
