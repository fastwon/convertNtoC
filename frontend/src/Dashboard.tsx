import { useCallback, useEffect, useState } from 'react'
import { createProject, deleteProject, listProjects, type Project } from './api'
import { btn, btnDanger, btnPrimary, card, input, label } from './ui'

export default function Dashboard({ onOpen }: { onOpen: (id: string) => void }) {
  const [projects, setProjects] = useState<Project[] | null>(null)
  const [error, setError] = useState('')
  const [name, setName] = useState('')
  const [style, setStyle] = useState('')
  const [busy, setBusy] = useState(false)

  const refresh = useCallback(() => {
    setError('')
    listProjects()
      .then(setProjects)
      .catch((e: unknown) => setError(String(e)))
  }, [])
  useEffect(() => {
    refresh()
  }, [refresh])

  async function create() {
    if (!name.trim()) return
    setBusy(true)
    setError('')
    try {
      await createProject({ name: name.trim(), style_prompt: style.trim() })
      setName('')
      setStyle('')
      refresh()
    } catch (e: unknown) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  async function remove(id: string, pname: string) {
    if (!confirm(`'${pname}' 프로젝트를 삭제할까요?\n회차·캐릭터·이미지가 모두 삭제됩니다.`)) return
    setBusy(true)
    try {
      await deleteProject(id)
      refresh()
    } finally {
      setBusy(false)
    }
  }

  return (
    <section>
      <h2>대시보드</h2>

      <div style={card}>
        <strong>새 프로젝트</strong>
        <label style={label}>프로젝트 이름</label>
        <input
          style={input}
          value={name}
          placeholder="예: A소설 웹툰화"
          onChange={(e) => setName(e.target.value)}
          disabled={busy}
        />
        <label style={label}>화풍 스타일 (선택 — 나중에 수정 가능)</label>
        <textarea
          style={{ ...input, minHeight: 60, resize: 'vertical' }}
          value={style}
          placeholder="예: 로맨스 판타지풍, 부드러운 채색, 큰 눈"
          onChange={(e) => setStyle(e.target.value)}
          disabled={busy}
        />
        <div style={{ marginTop: 10 }}>
          <button style={btnPrimary} onClick={create} disabled={busy || !name.trim()}>
            프로젝트 생성
          </button>
        </div>
      </div>

      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {!projects && !error && <p>불러오는 중…</p>}
      {projects && projects.length === 0 && (
        <p style={{ color: '#888' }}>아직 프로젝트가 없습니다. 위에서 하나 만들어보세요.</p>
      )}

      {projects?.map((p) => (
        <div key={p.id} style={{ ...card, display: 'flex', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 700, fontSize: 16 }}>{p.name}</div>
            <div style={{ color: '#777', fontSize: 13, marginTop: 4 }}>
              화풍: {p.style_prompt ? p.style_prompt.slice(0, 60) : '(미지정)'}
            </div>
            <div style={{ color: '#aaa', fontSize: 12, marginTop: 2 }}>
              {new Date(p.created_at).toLocaleString()}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', flexShrink: 0 }}>
            <button style={btn} onClick={() => onOpen(p.id)}>
              열기
            </button>
            <button style={btnDanger} onClick={() => remove(p.id, p.name)} disabled={busy}>
              삭제
            </button>
          </div>
        </div>
      ))}
    </section>
  )
}
