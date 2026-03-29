import React from 'react'
import { LayoutDashboard, MessageSquare, History, User, LogOut, Github } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const Dashboard = () => {
  const { user, signOut } = useAuth()

  return (
    <div className="dashboard-container" style={{ display: 'flex', height: '100dvh', overflow: 'hidden' }}>
      {/* Mini Sidebar */}
      <aside className="glass" style={{ width: 80, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '24px 0', gap: 32 }}>
        <div className="text-gradient" style={{ fontWeight: 800, fontSize: 24 }}>AI</div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24, flex: 1 }}>
          <LayoutDashboard size={24} className="text-gradient" style={{ cursor: 'pointer' }} />
          <MessageSquare size={24} style={{ color: 'var(--text-secondary)', cursor: 'pointer' }} />
          <History size={24} style={{ color: 'var(--text-secondary)', cursor: 'pointer' }} />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <User size={24} style={{ color: 'var(--text-secondary)', cursor: 'pointer' }} />
          <LogOut size={24} onClick={signOut} style={{ color: 'var(--accent-danger)', cursor: 'pointer' }} />
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, padding: 40, overflowY: 'auto' }}>
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 40 }}>
          <div>
            <h1 className="text-gradient" style={{ fontSize: 32, fontWeight: 700 }}>Developer Intelligence</h1>
            <p style={{ color: 'var(--text-secondary)' }}>Welcome back, {user?.email}</p>
          </div>
          <button className="btn btn-primary" style={{ padding: '12px 24px' }}>
            Analyze New Repo
          </button>
        </header>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 24 }}>
          {/* Placeholder for Skill Radar Chart */}
          <div className="glass" style={{ height: 400, borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <p style={{ color: 'var(--text-secondary)' }}>Skill Visualization Coming Soon...</p>
          </div>

          {/* Placeholder for Language Distribution */}
          <div className="glass" style={{ height: 400, borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <p style={{ color: 'var(--text-secondary)' }}>Language Breakdown Coming Soon...</p>
          </div>
        </div>

        <section style={{ marginTop: 40 }}>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 20 }}>Recent Analyses</h2>
          <div className="glass" style={{ padding: 40, textAlign: 'center', borderRadius: 'var(--radius-lg)' }}>
             <p style={{ color: 'var(--text-secondary)' }}>No analysis history found. Start by analyzing a repository!</p>
          </div>
        </section>
      </main>
    </div>
  )
}

export default Dashboard
