import { useCallback, useEffect, useRef, useState, type CSSProperties, type RefObject } from 'react'
import {
  deletePanel,
  generatePanelImage,
  generateStoryboard,
  getPanelPrompt,
  letterPanel,
  letteredImageUrl,
  listPanels,
  panelImageUrl,
  updatePanel,
  uploadPanelImage,
  type Panel,
  type PanelDialogue,
} from './api'
import { badge, btnDanger, btnPrimary, btnSm, c, input, muted } from './ui'

function bubbleStyle(type: PanelDialogue['type']): CSSProperties {
  const base: CSSProperties = {
    position: 'absolute',
    maxWidth: '55%',
    padding: '4px 8px',
    fontSize: 12,
    lineHeight: 1.3,
    cursor: 'move',
    userSelect: 'none',
    touchAction: 'none',
    boxSizing: 'border-box',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
  }
  if (type === 'narration') return { ...base, background: '#fff8e1', border: '2px solid #3c3c3c', borderRadius: 6 }
  if (type === 'thought') return { ...base, background: '#fff', border: '2px dashed #8a8a8a', borderRadius: 9999 }
  return { ...base, background: '#fff', border: '2px solid #141414', borderRadius: 12 }
}

function DraggableBubble({
  d,
  containerRef,
  onMove,
}: {
  d: PanelDialogue
  containerRef: RefObject<HTMLDivElement | null>
  onMove: (x: number, y: number) => void
}) {
  const start = useRef<{ px: number; py: number; x: number; y: number } | null>(null)
  function down(e: React.PointerEvent) {
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
    start.current = { px: e.clientX, py: e.clientY, x: d.x ?? 0, y: d.y ?? 0 }
  }
  function move(e: React.PointerEvent) {
    if (!start.current || !containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    let nx = start.current.x + (e.clientX - start.current.px) / rect.width
    let ny = start.current.y + (e.clientY - start.current.py) / rect.height
    nx = Math.max(0, Math.min(0.95, nx))
    ny = Math.max(0, Math.min(0.95, ny))
    onMove(nx, ny)
  }
  function up() {
    start.current = null
  }
  const label =
    d.type === 'narration' ? '' : d.type === 'thought' ? `${d.speaker} (생각)` : d.speaker
  return (
    <div
      style={{ ...bubbleStyle(d.type ?? 'speech'), left: `${(d.x ?? 0) * 100}%`, top: `${(d.y ?? 0) * 100}%` }}
      onPointerDown={down}
      onPointerMove={move}
      onPointerUp={up}
    >
      {label && <div style={{ fontSize: 10, color: '#5a5a5a', fontWeight: 700 }}>{label}</div>}
      {d.text || '(내용 없음)'}
    </div>
  )
}

const withDefaults = (list: PanelDialogue[]): PanelDialogue[] =>
  list.map((d, i) => ({
    ...d,
    x: d.x ?? 0.06,
    y: d.y ?? Math.min(0.85, 0.06 + (i % 6) * 0.14),
  }))

function PanelCard({ panel, index, onChanged }: { panel: Panel; index: number; onChanged: () => void }) {
  const [scene, setScene] = useState(panel.scene)
  const [busy, setBusy] = useState(false)
  const [imgV, setImgV] = useState(0)
  const [hasImg, setHasImg] = useState(!!panel.image_path)
  const [genning, setGenning] = useState(false)
  const [msg, setMsg] = useState('')
  const [dialogue, setDialogue] = useState<PanelDialogue[]>(withDefaults(panel.dialogue ?? []))
  const [lettering, setLettering] = useState(false)
  const [hasLettered, setHasLettered] = useState(!!panel.lettered_path)
  const [showLettered, setShowLettered] = useState(false)
  const [letterV, setLetterV] = useState(0)
  const [promptText, setPromptText] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const uploadRef = useRef<HTMLInputElement>(null)

  function patchLine(i: number, patch: Partial<PanelDialogue>) {
    setDialogue((ds) => ds.map((d, j) => (j === i ? { ...d, ...patch } : d)))
    setShowLettered(false)
  }
  function addLine() {
    setDialogue((ds) => [...ds, { type: 'speech', speaker: '', text: '새 대사', x: 0.1, y: 0.1 }])
    setShowLettered(false)
  }
  function removeLine(i: number) {
    setDialogue((ds) => ds.filter((_, j) => j !== i))
    setShowLettered(false)
  }

  async function saveScene() {
    setBusy(true)
    setMsg('')
    try {
      await updatePanel(panel.id, { scene })
      setMsg('장면 저장됨')
    } finally {
      setBusy(false)
    }
  }
  async function saveDialogue() {
    setBusy(true)
    setMsg('')
    try {
      await updatePanel(panel.id, { dialogue })
      setMsg('대사·위치 저장됨')
    } finally {
      setBusy(false)
    }
  }
  async function genImage() {
    setGenning(true)
    setMsg('')
    try {
      await generatePanelImage(panel.id)
      setHasImg(true)
      setImgV((v) => v + 1)
      setShowLettered(false)
    } catch (e: unknown) {
      setMsg(String(e instanceof Error ? e.message : e))
    } finally {
      setGenning(false)
    }
  }
  async function onUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (!f) return
    setGenning(true)
    setMsg('')
    try {
      await uploadPanelImage(panel.id, f)
      setHasImg(true)
      setHasLettered(false)
      setShowLettered(false)
      setImgV((v) => v + 1)
      setMsg('이미지 업로드됨')
    } catch (err: unknown) {
      setMsg(String(err instanceof Error ? err.message : err))
    } finally {
      setGenning(false)
      if (uploadRef.current) uploadRef.current.value = ''
    }
  }
  async function copyPrompt() {
    setMsg('')
    try {
      const r = await getPanelPrompt(panel.id)
      setPromptText(r.prompt)
      try {
        await navigator.clipboard.writeText(r.prompt)
        setMsg('프롬프트 복사됨 (아래 상자에도 표시)')
      } catch {
        setMsg('아래 상자의 프롬프트를 복사해 쓰세요')
      }
    } catch (e: unknown) {
      setMsg(String(e instanceof Error ? e.message : e))
    }
  }
  async function doLetter() {
    setLettering(true)
    setMsg('')
    try {
      await updatePanel(panel.id, { dialogue }) // persist positions first
      await letterPanel(panel.id)
      setHasLettered(true)
      setShowLettered(true)
      setLetterV((v) => v + 1)
    } catch (e: unknown) {
      setMsg(String(e instanceof Error ? e.message : e))
    } finally {
      setLettering(false)
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
    <div style={{ border: `1px solid ${c.border}`, borderRadius: 12, padding: 14, marginBottom: 10, background: c.surface }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong style={{ fontSize: 15 }}>컷 {index + 1}</strong>
        <button style={{ ...btnDanger, padding: '4px 10px', fontSize: 13 }} onClick={remove} disabled={busy}>
          컷 삭제
        </button>
      </div>

      {panel.characters && panel.characters.length > 0 && (
        <div style={{ margin: '8px 0', display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {panel.characters.map((ch, i) => (
            <span key={i} style={badge('accent')}>
              {ch.name}
              {ch.appearance_label && ch.appearance_label !== '기본' ? ` · ${ch.appearance_label}` : ''}
            </span>
          ))}
        </div>
      )}

      {/* editing canvas: image + draggable bubbles */}
      <div ref={containerRef} style={{ position: 'relative', width: '100%', maxWidth: 380, margin: '8px auto', background: c.subtle, borderRadius: 8, minHeight: 60 }}>
        {hasImg ? (
          <img
            src={showLettered && hasLettered ? letteredImageUrl(panel.id, letterV) : panelImageUrl(panel.id, imgV)}
            alt={`컷 ${index + 1}`}
            style={{ width: '100%', display: 'block', borderRadius: 8 }}
          />
        ) : (
          <div style={{ padding: 24, textAlign: 'center', color: c.faint, fontSize: 13 }}>이미지 없음</div>
        )}
        {hasImg && !showLettered &&
          dialogue.map((d, i) => (
            <DraggableBubble key={i} d={d} containerRef={containerRef} onMove={(x, y) => patchLine(i, { x, y })} />
          ))}
      </div>
      {hasImg && !showLettered && (
        <div style={{ textAlign: 'center', fontSize: 11, color: c.faint, marginTop: -2 }}>
          말풍선을 끌어서 원하는 위치에 놓으세요
        </div>
      )}

      <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginTop: 10, flexWrap: 'wrap' }}>
        <button style={btnSm} onClick={genImage} disabled={genning}>
          {genning ? '생성 중…' : hasImg ? '이미지 재생성' : '이미지 자동생성'}
        </button>
        <input ref={uploadRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={onUpload} />
        <button style={btnSm} onClick={() => uploadRef.current?.click()} disabled={genning}>
          이미지 업로드
        </button>
        <button style={btnSm} onClick={copyPrompt}>
          프롬프트 복사
        </button>
        <button style={{ ...btnPrimary, padding: '5px 10px', fontSize: 13 }} onClick={doLetter} disabled={lettering || !hasImg}>
          {lettering ? '합성 중…' : '대사 합성'}
        </button>
        {hasLettered && (
          <button style={btnSm} onClick={() => setShowLettered((v) => !v)}>
            {showLettered ? '편집(원본)' : '합성본 보기'}
          </button>
        )}
      </div>
      {msg && (
        <p style={{ textAlign: 'center', fontSize: 12, marginTop: 6, color: msg.includes('실패') || msg.includes('오류') ? c.danger : c.success }}>
          {msg}
        </p>
      )}
      {promptText && (
        <div style={{ marginTop: 6 }}>
          <div style={{ fontSize: 11, color: c.muted }}>
            이 프롬프트 + 캐릭터 참조 이미지를 Gemini 웹에 넣어 만든 뒤, "이미지 업로드"로 넣으세요
          </div>
          <textarea
            readOnly
            style={{ ...input, minHeight: 54, marginTop: 2, background: c.subtle }}
            value={promptText}
            onFocus={(e) => e.currentTarget.select()}
          />
        </div>
      )}

      <div style={{ ...muted, fontSize: 12, marginTop: 12 }}>장면 묘사 (이미지 생성 기준)</div>
      <textarea style={{ ...input, minHeight: 54, marginTop: 4, resize: 'vertical' }} value={scene} onChange={(e) => setScene(e.target.value)} />
      <button style={{ ...btnSm, marginTop: 6 }} onClick={saveScene} disabled={busy}>
        장면 저장
      </button>

      <div style={{ ...muted, fontSize: 12, marginTop: 12 }}>대사 (위 이미지에서 드래그로 위치 조정)</div>
      {dialogue.map((d, i) => (
        <div key={i} style={{ display: 'flex', gap: 4, marginTop: 4 }}>
          <select
            style={{ ...input, width: 66, padding: 6 }}
            value={d.type ?? 'speech'}
            onChange={(e) => {
              const t = e.target.value as PanelDialogue['type']
              patchLine(i, t === 'narration' ? { type: t, speaker: '' } : { type: t })
            }}
          >
            <option value="speech">대사</option>
            <option value="thought">생각</option>
            <option value="narration">지문</option>
          </select>
          {d.type === 'narration' ? (
            <span style={{ width: 74, fontSize: 11, color: c.faint, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              (화자 없음)
            </span>
          ) : (
            <input style={{ ...input, width: 74 }} value={d.speaker} placeholder="화자" onChange={(e) => patchLine(i, { speaker: e.target.value })} />
          )}
          <input style={{ ...input, flex: 1 }} value={d.text} placeholder="내용" onChange={(e) => patchLine(i, { text: e.target.value })} />
          <button style={{ ...btnDanger, padding: '4px 10px', fontSize: 13 }} onClick={() => removeLine(i)}>
            ✕
          </button>
        </div>
      ))}
      <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
        <button style={btnSm} onClick={addLine}>
          + 대사
        </button>
        <button style={btnSm} onClick={saveDialogue} disabled={busy}>
          대사·위치 저장
        </button>
      </div>
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
    if (panels && panels.length > 0 && !confirm('기존 콘티를 새로 생성하면 현재 컷들이 교체됩니다. 계속할까요?')) return
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
        {panels && panels.length > 0 && <span style={muted}>{panels.length}개 컷</span>}
      </div>
      {error && <p style={{ color: c.danger }}>{error}</p>}
      <div style={{ marginTop: 10 }}>
        {panels?.map((p, i) => (
          <PanelCard key={p.id} panel={p} index={i} onChanged={load} />
        ))}
      </div>
    </div>
  )
}
