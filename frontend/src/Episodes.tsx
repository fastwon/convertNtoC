import { useCallback, useEffect, useState } from 'react'
import {
  createEpisode,
  deleteEpisode,
  listEpisodes,
  updateEpisodeText,
  type Episode,
} from './api'
import { btn, btnDanger, btnPrimary, card, input, label } from './ui'

function EpisodeRow({ ep, onChanged }: { ep: Episode; onChanged: () => void }) {
  const [open, setOpen] = useState(false)
  const [text, setText] = useState(ep.raw_text)
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)

  async function save() {
    setBusy(true)
    setSaved(false)
    try {
      await updateEpisodeText(ep.id, text)
      setSaved(true)
      onChanged()
    } finally {
      setBusy(false)
    }
  }
  async function remove() {
    if (!confirm(`${ep.number}화를 삭제할까요?`)) return
    setBusy(true)
    try {
      await deleteEpisode(ep.id)
      onChanged()
    } finally {
      setBusy(false)
    }
  }

  const chars = ep.raw_text.length
  return (
    <div style={card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <strong>{ep.number}화</strong>
          <span style={{ color: '#999', fontSize: 12, marginLeft: 8 }}>
            {chars.toLocaleString()}자 · {ep.status}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button style={btn} onClick={() => setOpen((v) => !v)}>
            {open ? '접기' : '본문'}
          </button>
          <button style={btnDanger} onClick={remove} disabled={busy}>
            삭제
          </button>
        </div>
      </div>
      {open && (
        <div style={{ marginTop: 10 }}>
          <textarea
            style={{ ...input, minHeight: 160, resize: 'vertical', fontFamily: 'inherit' }}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="소설 본문을 붙여넣으세요"
          />
          <div style={{ marginTop: 8, display: 'flex', gap: 10, alignItems: 'center' }}>
            <button style={btnPrimary} onClick={save} disabled={busy}>
              본문 저장
            </button>
            {saved && <span style={{ color: 'green' }}>저장됨 ✓</span>}
            <span style={{ color: '#aaa', fontSize: 12 }}>
              (인물 추출은 다음 단계에서 추가됩니다)
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

export default function Episodes({ projectId }: { projectId: string }) {
  const [episodes, setEpisodes] = useState<Episode[] | null>(null)
  const [error, setError] = useState('')
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)

  const refresh = useCallback(() => {
    setError('')
    listEpisodes(projectId)
      .then(setEpisodes)
      .catch((e: unknown) => setError(String(e)))
  }, [projectId])
  useEffect(() => {
    refresh()
  }, [refresh])

  const nextNumber = (episodes?.reduce((m, e) => Math.max(m, e.number), 0) ?? 0) + 1

  async function add() {
    setBusy(true)
    setError('')
    try {
      await createEpisode(projectId, { raw_text: text })
      setText('')
      refresh()
    } catch (e: unknown) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section style={{ marginTop: 24 }}>
      <h3>회차 (Episode)</h3>

      <div style={card}>
        <strong>새 회차 업로드</strong>
        <label style={label}>{nextNumber}화 본문 (텍스트 붙여넣기)</label>
        <textarea
          style={{ ...input, minHeight: 120, resize: 'vertical', fontFamily: 'inherit' }}
          value={text}
          placeholder="소설 본문을 붙여넣으세요"
          onChange={(e) => setText(e.target.value)}
          disabled={busy}
        />
        <div style={{ marginTop: 10 }}>
          <button style={btnPrimary} onClick={add} disabled={busy}>
            {nextNumber}화 추가
          </button>
        </div>
      </div>

      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {!episodes && !error && <p>불러오는 중…</p>}
      {episodes && episodes.length === 0 && (
        <p style={{ color: '#888' }}>아직 회차가 없습니다. 위에서 1화를 올려보세요.</p>
      )}
      {episodes?.map((ep) => (
        <EpisodeRow key={ep.id} ep={ep} onChanged={refresh} />
      ))}
    </section>
  )
}
