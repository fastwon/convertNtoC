import { useCallback, useEffect, useState } from 'react'
import { getProject, updateProject, type Project } from './api'
import Characters from './Characters'
import Episodes from './Episodes'
import Memory from './Memory'
import { btn, btnPrimary, card, input, label } from './ui'

export default function ProjectDetail({ id, onBack }: { id: string; onBack: () => void }) {
  const [project, setProject] = useState<Project | null>(null)
  const [error, setError] = useState('')
  const [name, setName] = useState('')
  const [style, setStyle] = useState('')
  const [modelRef, setModelRef] = useState('')
  const [font, setFont] = useState('')
  const [bubble, setBubble] = useState('')
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)
  const [charRefresh, setCharRefresh] = useState(0)

  const load = useCallback(() => {
    setError('')
    getProject(id)
      .then((p) => {
        setProject(p)
        setName(p.name)
        setStyle(p.style_prompt)
        setModelRef(p.image_model_ref ?? '')
        const fs = (p.font_settings ?? {}) as Record<string, string>
        setFont(fs.font_family ?? '')
        setBubble(fs.bubble_style ?? '')
      })
      .catch((e: unknown) => setError(String(e)))
  }, [id])
  useEffect(() => {
    load()
  }, [load])

  async function save() {
    setBusy(true)
    setSaved(false)
    setError('')
    try {
      await updateProject(id, {
        name: name.trim(),
        style_prompt: style.trim(),
        image_model_ref: modelRef.trim() || null,
        font_settings: { font_family: font.trim(), bubble_style: bubble.trim() },
      })
      setSaved(true)
      load()
    } catch (e: unknown) {
      setError(String(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section>
      <button style={{ ...btn, marginBottom: 12 }} onClick={onBack}>
        ← 대시보드
      </button>
      <h2>{project ? project.name : '프로젝트'}</h2>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {!project && !error && <p>불러오는 중…</p>}

      {project && (
        <>
          <div style={card}>
            <label style={label}>프로젝트 이름</label>
            <input style={input} value={name} onChange={(e) => setName(e.target.value)} />
          </div>

          <div style={card}>
            <strong>화풍 스타일 (프로젝트 고정 기본값)</strong>
            <p style={{ color: '#888', fontSize: 12, margin: '4px 0 0' }}>
              여기 지정한 화풍이 이후 모든 회차 생성의 기본값으로 고정됩니다.
            </p>
            <label style={label}>스타일 프롬프트</label>
            <textarea
              style={{ ...input, minHeight: 70, resize: 'vertical' }}
              value={style}
              placeholder="예: 로맨스 판타지풍, 부드러운 채색, 큰 눈"
              onChange={(e) => setStyle(e.target.value)}
            />
            <label style={label}>이미지 모델 / LoRA 식별자 (선택 — 이미지 공급자 확정 후 사용)</label>
            <input
              style={input}
              value={modelRef}
              placeholder="예: some-lora-id (미정)"
              onChange={(e) => setModelRef(e.target.value)}
            />
          </div>

          <div style={card}>
            <strong>폰트 · 말풍선 (값만 저장 — 합성은 이후 단계)</strong>
            <label style={label}>폰트</label>
            <input style={input} value={font} placeholder="예: 나눔고딕" onChange={(e) => setFont(e.target.value)} />
            <label style={label}>말풍선 스타일</label>
            <input
              style={input}
              value={bubble}
              placeholder="예: 둥근 / 사각 / 생각풍선"
              onChange={(e) => setBubble(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <button style={btnPrimary} onClick={save} disabled={busy || !name.trim()}>
              저장
            </button>
            {saved && <span style={{ color: 'green' }}>저장됨 ✓</span>}
          </div>

          <Memory projectId={id} refreshKey={charRefresh} />
          <Characters projectId={id} refreshKey={charRefresh} />
          <Episodes projectId={id} onCharactersSaved={() => setCharRefresh((v) => v + 1)} />
        </>
      )}
    </section>
  )
}
