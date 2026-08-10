import { useCallback, useEffect, useState } from 'react'
import { getProject, updateProject, type Project } from './api'
import Characters from './Characters'
import Episodes from './Episodes'
import Memory from './Memory'
import { btnGhost, btnPrimary, c, card, input, label, okText, pageTitle, tabBar, tabBtn } from './ui'

type Tab = 'episodes' | 'characters' | 'world' | 'settings'

const TABS: { key: Tab; label: string }[] = [
  { key: 'episodes', label: '회차' },
  { key: 'characters', label: '캐릭터' },
  { key: 'world', label: '세계관' },
  { key: 'settings', label: '설정' },
]

export default function ProjectDetail({ id, onBack }: { id: string; onBack: () => void }) {
  const [project, setProject] = useState<Project | null>(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<Tab>('episodes')
  const [name, setName] = useState('')
  const [style, setStyle] = useState('')
  const [font, setFont] = useState('맑은 고딕')
  const [fontScale, setFontScale] = useState('보통')
  const [bubble, setBubble] = useState('둥근')
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
        const fs = (p.font_settings ?? {}) as Record<string, string>
        setFont(fs.font_family || '맑은 고딕')
        setFontScale(fs.font_scale || '보통')
        setBubble(fs.bubble_style || '둥근')
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
        font_settings: { font_family: font, font_scale: fontScale, bubble_style: bubble },
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
      <button style={{ ...btnGhost, padding: '4px 8px', marginBottom: 10, marginLeft: -8 }} onClick={onBack}>
        ← 대시보드
      </button>
      <h2 style={pageTitle}>{project ? project.name : '프로젝트'}</h2>
      {error && <p style={{ color: c.danger }}>{error}</p>}
      {!project && !error && <p style={{ color: c.muted }}>불러오는 중…</p>}

      {project && (
        <>
          <div style={tabBar}>
            {TABS.map((t) => (
              <button key={t.key} style={tabBtn(tab === t.key)} onClick={() => setTab(t.key)}>
                {t.label}
              </button>
            ))}
          </div>

          {tab === 'episodes' && (
            <Episodes projectId={id} onCharactersSaved={() => setCharRefresh((v) => v + 1)} />
          )}
          {tab === 'characters' && <Characters projectId={id} refreshKey={charRefresh} />}
          {tab === 'world' && <Memory projectId={id} refreshKey={charRefresh} />}

          {tab === 'settings' && (
            <>
              <div style={card}>
                <label style={label}>프로젝트 이름</label>
                <input style={input} value={name} onChange={(e) => setName(e.target.value)} />
              </div>

              <div style={card}>
                <strong>화풍 스타일 (프로젝트 고정 기본값)</strong>
                <p style={{ color: c.muted, fontSize: 12.5, margin: '4px 0 0' }}>
                  여기 지정한 화풍이 이후 모든 회차 생성의 기본값으로 고정됩니다.
                </p>
                <label style={label}>스타일 프롬프트</label>
                <textarea
                  style={{ ...input, minHeight: 70, resize: 'vertical' }}
                  value={style}
                  placeholder="예: 로맨스 판타지풍, 부드러운 채색, 큰 눈"
                  onChange={(e) => setStyle(e.target.value)}
                />
              </div>

              <div style={card}>
                <strong>폰트 · 말풍선</strong>
                <p style={{ color: c.muted, fontSize: 12.5, margin: '4px 0 0' }}>
                  대사 합성(말풍선 렌더링)에 적용됩니다. 변경 후 각 컷에서 <b>대사 합성</b>을 다시
                  눌러야 반영돼요.
                </p>
                <label style={label}>폰트</label>
                <select style={input} value={font} onChange={(e) => setFont(e.target.value)}>
                  {['맑은 고딕', '굴림', '돋움', '바탕', '나눔고딕'].map((f) => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
                </select>
                <label style={label}>글자 크기</label>
                <select style={input} value={fontScale} onChange={(e) => setFontScale(e.target.value)}>
                  {['작게', '보통', '크게'].map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
                <label style={label}>말풍선 스타일 (대사용)</label>
                <select style={input} value={bubble} onChange={(e) => setBubble(e.target.value)}>
                  {['둥근', '사각', '굵은 테두리'].map((b) => (
                    <option key={b} value={b}>
                      {b}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <button style={btnPrimary} onClick={save} disabled={busy || !name.trim()}>
                  설정 저장
                </button>
                {saved && <span style={okText}>저장됨 ✓</span>}
              </div>
            </>
          )}
        </>
      )}
    </section>
  )
}
