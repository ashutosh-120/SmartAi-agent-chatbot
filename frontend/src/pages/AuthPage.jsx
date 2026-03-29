import React, { useState } from 'react'
import { supabase } from '../lib/supabase'
import { GitBranch, Mail, Lock, AlertCircle, Loader2 } from 'lucide-react'
import './AuthPage.css'

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const [success, setSuccess] = useState(null)

  const handleAuth = async (e) => {
    e.preventDefault()
    if (!supabase) {
      setError('Production Configuration Error: Supabase client is not initialized. Please check your Render environment variables (VITE_SUPABASE_URL/VITE_SUPABASE_ANON_KEY).')
      return;
    }
    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      if (isLogin) {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        })
        if (error) throw error
      } else {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            emailRedirectTo: window.location.origin,
          },
        })
        if (error) throw error
        
        // Success path for Registration
        setSuccess('Successfully registered! Please log in to continue.')
        setIsLogin(true) // Switch to login tab
        setPassword('')  // Clear password
        
        // Force sign out just in case auto-login happened (common if email confirm is off)
        await supabase.auth.signOut()
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleGithubLogin = async () => {
    if (!supabase) {
      setError('Configuration Error: Supabase client is not initialized.')
      return;
    }
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'github',
        options: {
          redirectTo: window.location.origin,
        },
      })
      if (error) throw error
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card glass">
        <div className="auth-header">
          <div className="auth-logo text-gradient">SmartAI Agent</div>
          <div className="auth-subtitle">Elevate your developer journey with AI</div>
        </div>

        <div className="auth-tabs">
          <button 
            className={`auth-tab ${isLogin ? 'active' : ''}`}
            onClick={() => setIsLogin(true)}
          >
            Login
          </button>
          <button 
            className={`auth-tab ${!isLogin ? 'active' : ''}`}
            onClick={() => setIsLogin(false)}
          >
            Register
          </button>
        </div>

        {error && (
          <div className="auth-error">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="auth-success">
            <GitBranch size={18} />
            <span>{success}</span>
          </div>
        )}

        <form className="auth-form" onSubmit={handleAuth}>
          <div className="form-group">
            <label>Email Address</label>
            <div style={{ position: 'relative' }}>
              <Mail 
                size={18} 
                style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} 
              />
              <input 
                type="email" 
                className="auth-input" 
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={{ paddingLeft: 44, width: '100%' }}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Password</label>
            <div style={{ position: 'relative' }}>
              <Lock 
                size={18} 
                style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} 
              />
              <input 
                type="password" 
                className="auth-input" 
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{ paddingLeft: 44, width: '100%' }}
                required
              />
            </div>
          </div>

          <button type="submit" className="btn btn-primary auth-btn" disabled={loading}>
            {loading ? <Loader2 size={20} className="animate-spin" /> : (isLogin ? 'Sign In' : 'Create Account')}
          </button>
        </form>

        <div className="auth-divider">
          <span>OR CONTINUE WITH</span>
        </div>

        <button className="btn btn-github auth-btn" onClick={handleGithubLogin}>
          <GitBranch size={20} />
          <span>GitHub</span>
        </button>

        <div className="auth-footer">
          {isLogin ? (
            <p>New here? <span className="text-gradient" style={{ cursor: 'pointer', fontWeight: '600' }} onClick={() => setIsLogin(false)}>Create an account</span></p>
          ) : (
            <p>Already have an account? <span className="text-gradient" style={{ cursor: 'pointer', fontWeight: '600' }} onClick={() => setIsLogin(true)}>Sign in instead</span></p>
          )}
        </div>
      </div>
    </div>
  )
}

export default AuthPage
