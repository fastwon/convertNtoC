import { useCallback, useEffect, useState } from 'react'
import { getWorldBible, previewMemory, setWorldBible } from './api'
import { btn, btnPrimary, card, input, label } from './ui'

export default function Memory({
  projectId,
  refreshKey,
}: {
  projectId: string
  refreshKey: number
}) {
  const [world, setWorld] = useState('')
  const [loaded, setLoaded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [preview, setPreview] = useState<string | null>(null)
  const [previewChars, setPreviewChars] = useState(0)

  const load = useCallback(() => {
    setError('')
    getWorldBible(projectId)
      .then((d) => {
        setWorld(d.world_bible)
        setLoaded(true)
      })
      .catch((e: unknown) => setError(String(e)))
  }, [projectId])

  useEffect(() => {
    load()
  }, [load])

  // if the preview is open, refresh it when characters/episodes change
  useEffect(() => {
    if (preview === null) return
    previewMemory(projectId)
      .then((d) => {
        setPreview(d.memory)
        setPreviewChars(d.chars)
      })
      .catch(() => undefined)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshKey])

  async function save() {
    setBusy(true)
    setSaved(false)
    try {
      await setWorldBible(projectId, world)
      setSaved(true)
      if (preview !== null) await showPreview()
    } catch (e: unknown) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  async function showPreview() {
    setBusy(true)
    try {
      const d = await previewMemory(projectId)
      setPreview(d.memory)
      setPreviewChars(d.chars)
    } catch (e: unknown) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section style={{ marginTop: 24 }}>
      <h3>글로벌 메모리</h3>
      <p style={{ color: '#888', fontSize: 13, marginTop: 0 }}>
        화풍 + 세계관 + 캐릭터 뱅크 + 지난 회차 요약이 매 회차 작업에 자동 주입됩니다.
      </p>

      <div style={card}>
        <strong>세계관</strong>
        <label style={label}>작품의 배경·설정·규칙 (자유 서술)</label>
        <textarea
          style={{ ...input, minHeight: 90, resize: 'vertical' }}
          value={world}
          placeholder="예: 마법이 금지된 근미래 도시국가. 주인공들은 지하 조직에 속해 있다."
          onChange={(e) => setWorld(e.target.value)}
          disabled={busy || !loaded}
        />
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 10 }}>
          <button style={btnPrimary} onClick={save} disabled={busy || !loaded}>
            세계관 저장
          </button>
          {saved && <span style={{ color: 'green' }}>저장됨 ✓</span>}
          <button style={btn} onClick={showPreview} disabled={busy}>
            {preview === null ? '주입되는 메모리 보기' : '메모리 새로고침'}
          </button>
          {preview !== null && (
            <button style={btn} onClick={() => setPreview(null)}>
              닫기
            </button>
          )}
        </div>
      </div>

      {error && <p style={{ color: 'crimson' }}>{error}</p>}

      {preview !== null && (
        <div style={card}>
          <strong>실제 주입되는 컨텍스트</strong>
          <span style={{ color: '#888', fontSize: 12, marginLeft: 8 }}>
            {previewChars.toLocaleString()}자 (LLM system 프리픽스로 전송·캐시됨)
          </span>
          <pre
            style={{
              marginTop: 8,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              background: '#fafafa',
              border: '1px solid #eee',
              borderRadius: 6,
              padding: 10,
              maxHeight: 320,
              overflow: 'auto',
              fontSize: 12,
            }}
          >
            {preview}
          </pre>
        </div>
      )}
    </section>
  )
}
