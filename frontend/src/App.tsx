import { useState } from 'react'
import Dashboard from './Dashboard'
import ProjectDetail from './ProjectDetail'
import Settings from './Settings'

type View = { name: 'dashboard' } | { name: 'project'; id: string } | { name: 'settings' }

export default function App() {
  const [view, setView] = useState<View>({ name: 'dashboard' })

  const navItem = (active: boolean) => ({
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontSize: 15,
    padding: '4px 8px',
    color: active ? '#2d6cdf' : '#333',
    fontWeight: active ? 700 : 400,
  })

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', color: '#222' }}>
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          padding: '12px 24px',
          borderBottom: '1px solid #eee',
        }}
      >
        <strong style={{ fontSize: 17 }}>convertN2C</strong>
        <button style={navItem(view.name !== 'settings')} onClick={() => setView({ name: 'dashboard' })}>
          대시보드
        </button>
        <button style={navItem(view.name === 'settings')} onClick={() => setView({ name: 'settings' })}>
          설정
        </button>
      </header>

      <main style={{ maxWidth: 820, margin: '0 auto', padding: 24 }}>
        {view.name === 'dashboard' && (
          <Dashboard onOpen={(id) => setView({ name: 'project', id })} />
        )}
        {view.name === 'project' && (
          <ProjectDetail id={view.id} onBack={() => setView({ name: 'dashboard' })} />
        )}
        {view.name === 'settings' && <Settings />}
      </main>
    </div>
  )
}
