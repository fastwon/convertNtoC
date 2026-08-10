import { useState } from 'react'
import Dashboard from './Dashboard'
import ProjectDetail from './ProjectDetail'
import Settings from './Settings'
import { c } from './ui'

type View = { name: 'dashboard' } | { name: 'project'; id: string } | { name: 'settings' }

export default function App() {
  const [view, setView] = useState<View>({ name: 'dashboard' })

  const navItem = (active: boolean) => ({
    background: active ? c.accentSoft : 'none',
    border: 'none',
    borderRadius: 8,
    cursor: 'pointer',
    fontSize: 14.5,
    padding: '6px 12px',
    color: active ? c.accent : c.muted,
    fontWeight: active ? 700 : 500,
  })

  return (
    <div style={{ minHeight: '100vh', background: c.bg, color: c.text }}>
      <header
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '0 24px',
          height: 56,
          background: c.surface,
          borderBottom: `1px solid ${c.border}`,
          position: 'sticky',
          top: 0,
          zIndex: 10,
        }}
      >
        <button
          onClick={() => setView({ name: 'dashboard' })}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: 17,
            fontWeight: 800,
            letterSpacing: '-0.02em',
            color: c.text,
            marginRight: 8,
            padding: 0,
          }}
        >
          convert<span style={{ color: c.accent }}>N2C</span>
        </button>
        <button
          style={navItem(view.name !== 'settings')}
          onClick={() => setView({ name: 'dashboard' })}
        >
          대시보드
        </button>
        <button style={navItem(view.name === 'settings')} onClick={() => setView({ name: 'settings' })}>
          설정
        </button>
      </header>

      <main style={{ maxWidth: 860, margin: '0 auto', padding: '28px 24px 64px' }}>
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
