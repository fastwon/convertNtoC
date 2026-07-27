import { useCallback, useEffect, useState } from 'react'
import {
  deletePanel,
  generateStoryboard,
  listPanels,
  updatePanel,
  type Panel,
} from './api'
import { btn, btnDanger, btnPrimary, input } from './ui'

function PanelCard({ panel, index, onChanged }: { panel: Panel; index: number; onChanged: () => void }) {
  const [scene, setScene] = useState(panel.scene)
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)

  async function save() {
    setBusy(true)
    setSaved(false)
    try {
      await updatePanel(panel.id, { scene })
      setSaved(true)
    } finally {
      setBusy(false)
    }
  }
  async function remove() {
    if (!confirm(`컷 ${index + 1}을 삭제할까요?`)) return
    setBusy(true)
    try {
      await deletePanel(panel.id)
      onChanged()
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ border: '1px solid #e3e3e3', borderRadius: 8, padding: 12, marginBottom: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong>컷 {index + 1}</strong>
        <div style={{ display: 'flex', gap: 6 }}>
          {saved && <span style={{ color: 'green', fontSize: 12, alignSelf: 'center' }}>저장됨 ✓</span>}
          <button style={{ ...btn, fontSize: 12 }} onClick={save} disabled={busy}>
            저장
          </button>
          <button style={{ ...btnDanger, fontSize: 12 }} onClick={remove} disabled={busy}>
            삭제
          </button>
        </div>
      </div>

      {panel.characters && panel.characters.length > 0 && (
        <div style={{ margin: '6px 0', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {panel.characters.map((c, i) => (
            <span
              key={i}
              style={{
                fontSize: 12,
                background: '#eef4ff',
                color: '#2456a6',
                borderRadius: 4,
                padding: '1px 6px',
              }}
            >
              {c.name}
              {c.appearance_label && c.appearance_label !== '기본' ? ` · ${c.appearance_label}` : ''}
            </span>
          ))}
        </div>
      )}

      <div style={{ fontSize: 12, color: '#888', marginTop: 4 }}>장면 묘사 (이미지 생성 기준)</div>
      <textarea
        style={{ ...input, minHeight: 48, marginTop: 2, resize: 'vertical' }}
        value={scene}
        onChange={(e) => setScene(e.target.value)}
        disabled={busy}
      />

      {panel.dialogue && panel.dialogue.length > 0 && (
        <div style={{ marginTop: 6 }}>
          {panel.dialogue.map((d, i) => (
            <div key={i} style={{ fontSize: 13, color: '#333' }}>
              <b>{d.speaker || '나레이션'}:</b> {d.text}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default function Storyboard({ episodeId }: { episodeId: string }) {
  const [panels, setPanels] = useState<Panel[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    listPanels(episodeId)
      .then(setPanels)
      .catch((e: unknown) => setError(String(e)))
  }, [episodeId])
  useEffect(() => {
    load()
  }, [load])

  async function generate() {
    if (panels && panels.length > 0 && !confirm('기존 콘티를 새로 생성하면 현재 컷들이 교체됩니다. 계속할까요?'))
      return
    setBusy(true)
    setError('')
    try {
      const res = await generateStoryboard(episodeId)
      setPanels(res.panels)
    } catch (e: unknown) {
      setError(String(e instanceof Error ? e.message : e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <button style={btnPrimary} onClick={generate} disabled={busy}>
          {busy ? '콘티 생성 중…' : panels && panels.length > 0 ? '콘티 다시 생성' : '콘티 생성'}
        </button>
        {panels && panels.length > 0 && (
          <span style={{ color: '#888', fontSize: 13 }}>{panels.length}개 컷</span>
        )}
        <span style={{ color: '#aaa', fontSize: 12 }}>(이미지 생성은 다음 단계에서 추가됩니다)</span>
      </div>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      <div style={{ marginTop: 10 }}>
        {panels?.map((p, i) => (
          <PanelCard key={p.id} panel={p} index={i} onChanged={load} />
        ))}
      </div>
    </div>
  )
}
