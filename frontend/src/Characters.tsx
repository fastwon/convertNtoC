import { useCallback, useEffect, useRef, useState } from 'react'
import {
  createAppearance,
  deleteAppearance,
  deleteCharacter,
  describeAppearanceFromImage,
  listAppearances,
  listCharacters,
  makeDefaultAppearance,
  refImageUrl,
  updateAppearance,
  updateCharacter,
  uploadRefImage,
  type Appearance,
  type Character,
} from './api'
import { btn, btnDanger, card, errText, input, label, muted, okText, sectionTitle } from './ui'

function AppearanceRow({ ap, onChanged }: { ap: Appearance; onChanged: () => void }) {
  const [labelText, setLabelText] = useState(ap.label)
  const [desc, setDesc] = useState(ap.description)
  const [epNum, setEpNum] = useState(
    ap.source_episode_number === null ? '' : String(ap.source_episode_number),
  )
  const [busy, setBusy] = useState(false)
  const [imgV, setImgV] = useState(0)
  const [hasImg, setHasImg] = useState(!!ap.ref_image_path)
  const fileRef = useRef<HTMLInputElement>(null)

  // sync when the row is reloaded after an external change (외형 추출 등)
  useEffect(() => {
    setDesc(ap.description)
    setLabelText(ap.label)
    setHasImg(!!ap.ref_image_path)
  }, [ap.description, ap.label, ap.ref_image_path])

  async function save() {
    setBusy(true)
    try {
      const n = epNum.trim() === '' ? null : Number(epNum)
      await updateAppearance(ap.id, {
        label: labelText.trim(),
        description: desc,
        source_episode_number: Number.isFinite(n as number) ? n : null,
      })
      onChanged()
    } finally {
      setBusy(false)
    }
  }
  async function remove() {
    if (!confirm(`'${ap.label}' 모습을 삭제할까요?`)) return
    setBusy(true)
    try {
      await deleteAppearance(ap.id)
      onChanged()
    } catch (e: unknown) {
      alert(String(e instanceof Error ? e.message : e))
    } finally {
      setBusy(false)
    }
  }
  async function setDefault() {
    setBusy(true)
    try {
      await makeDefaultAppearance(ap.id)
      onChanged()
    } finally {
      setBusy(false)
    }
  }
  async function onFile(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (!f) return
    setBusy(true)
    try {
      await uploadRefImage(ap.id, f)
      setHasImg(true)
      setImgV((v) => v + 1)
    } catch (err: unknown) {
      alert(String(err instanceof Error ? err.message : err))
    } finally {
      setBusy(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }
  async function extractDesc() {
    setBusy(true)
    try {
      const r = await describeAppearanceFromImage(ap.id)
      setDesc(r.description) // fills the 외형 box; user reviews then saves
    } catch (err: unknown) {
      alert(String(err instanceof Error ? err.message : err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        gap: 10,
        padding: 10,
        border: '1px solid #eee',
        borderRadius: 6,
        marginTop: 8,
        background: ap.is_default ? '#f7fbff' : '#fff',
      }}
    >
      <div style={{ flexShrink: 0, textAlign: 'center', width: 72 }}>
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: 6,
            border: '1px solid #ddd',
            background: '#fafafa',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {hasImg ? (
            <img
              src={refImageUrl(ap.id, imgV)}
              alt={ap.label}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            <span style={{ color: '#ccc', fontSize: 11 }}>없음</span>
          )}
        </div>
        <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={onFile} />
        <button
          style={{ ...btn, marginTop: 4, fontSize: 11, padding: '3px 6px', width: '100%' }}
          onClick={() => fileRef.current?.click()}
          disabled={busy}
        >
          이미지
        </button>
        {hasImg && (
          <button
            style={{ ...btn, marginTop: 4, fontSize: 11, padding: '3px 6px', width: '100%' }}
            onClick={extractDesc}
            disabled={busy}
            title="참조 이미지를 AI가 보고 외형 묘사를 채웁니다"
          >
            외형 추출
          </button>
        )}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <input
            style={{ ...input, flex: 1 }}
            value={labelText}
            placeholder="모습 이름 (예: 기본, 10년 전, 부상 후)"
            onChange={(e) => setLabelText(e.target.value)}
            disabled={busy}
          />
          <input
            style={{ ...input, width: 80 }}
            value={epNum}
            placeholder="회차"
            onChange={(e) => setEpNum(e.target.value)}
            disabled={busy}
          />
          {ap.is_default && (
            <span style={{ fontSize: 11, color: '#1e6fd0', flexShrink: 0 }}>기본</span>
          )}
        </div>
        <div style={{ fontSize: 11, color: '#888', margin: '6px 0 2px' }}>
          외형 (시각 — 이미지 생성에 사용)
        </div>
        <textarea
          style={{ ...input, minHeight: 44, resize: 'vertical' }}
          value={desc}
          placeholder="머리색·눈·복장 등 이 시점의 외형"
          onChange={(e) => setDesc(e.target.value)}
          disabled={busy}
        />
        <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
          <button style={{ ...btn, fontSize: 12 }} onClick={save} disabled={busy || !labelText.trim()}>
            저장
          </button>
          {!ap.is_default && (
            <button style={{ ...btn, fontSize: 12 }} onClick={setDefault} disabled={busy}>
              기본으로
            </button>
          )}
          <button style={{ ...btnDanger, fontSize: 12 }} onClick={remove} disabled={busy}>
            삭제
          </button>
        </div>
      </div>
    </div>
  )
}

function CharacterCard({
  ch,
  refreshKey,
  onChanged,
}: {
  ch: Character
  refreshKey: number
  onChanged: () => void
}) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState(ch.name)
  const [persona, setPersona] = useState(ch.traits?.description ?? '')
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState(false)
  const [looks, setLooks] = useState<Appearance[] | null>(null)
  const [newLabel, setNewLabel] = useState('')

  // sync name/persona when the character is reloaded (인물추출 갱신 등)
  useEffect(() => {
    setName(ch.name)
    setPersona(ch.traits?.description ?? '')
  }, [ch])

  const loadLooks = useCallback(() => {
    listAppearances(ch.id)
      .then(setLooks)
      .catch(() => setLooks([]))
  }, [ch.id])
  // reload looks when opened or an external change happened
  useEffect(() => {
    if (open) loadLooks()
  }, [open, loadLooks, refreshKey])

  async function saveInfo() {
    setBusy(true)
    setSaved(false)
    try {
      await updateCharacter(ch.id, { name: name.trim(), traits: persona })
      setSaved(true)
      onChanged()
    } finally {
      setBusy(false)
    }
  }
  async function removeChar() {
    if (!confirm(`'${ch.name}' 캐릭터와 모든 모습을 삭제할까요?`)) return
    setBusy(true)
    try {
      await deleteCharacter(ch.id)
      onChanged()
    } finally {
      setBusy(false)
    }
  }
  async function addLook() {
    if (!newLabel.trim()) return
    setBusy(true)
    try {
      await createAppearance(ch.id, { label: newLabel.trim() })
      setNewLabel('')
      loadLooks()
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={card}>
      <div
        style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}
        onClick={() => setOpen((v) => !v)}
      >
        <span style={{ color: '#999' }}>{open ? '▼' : '▶'}</span>
        <strong style={{ fontSize: 16 }}>{ch.name}</strong>
        {!open && persona && (
          <span
            style={{
              color: '#888',
              fontSize: 12,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            — {persona}
          </span>
        )}
      </div>

      {open && (
        <div style={{ marginTop: 10 }}>
          <label style={label}>이름</label>
          <input
            style={input}
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={busy}
          />
          <label style={label}>인물 설명 (성격·서사 — 인물 추출로 갱신됨)</label>
          <textarea
            style={{ ...input, minHeight: 48, resize: 'vertical' }}
            value={persona}
            placeholder="성격·역할·서사적 특징"
            onChange={(e) => setPersona(e.target.value)}
            disabled={busy}
          />
          <div style={{ display: 'flex', gap: 8, marginTop: 8, alignItems: 'center' }}>
            <button style={btn} onClick={saveInfo} disabled={busy || !name.trim()}>
              이름·설명 저장
            </button>
            {saved && <span style={okText}>저장됨 ✓</span>}
            <button style={btnDanger} onClick={removeChar} disabled={busy}>
              캐릭터 삭제
            </button>
          </div>

          <div style={{ marginTop: 14, fontSize: 13, fontWeight: 700 }}>
            시점별 모습 (외형)
          </div>
          <div style={{ fontSize: 12, color: '#888' }}>
            현재/과거 회상/부상 후 등 외형을 각각 관리 — 컷 생성 시 골라 쓰입니다.
          </div>
          {looks === null && <p style={{ color: '#aaa', fontSize: 13 }}>불러오는 중…</p>}
          {looks?.map((a) => (
            <AppearanceRow key={a.id} ap={a} onChanged={loadLooks} />
          ))}
          <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
            <input
              style={{ ...input, flex: 1 }}
              value={newLabel}
              placeholder="새 모습 이름 (예: 10년 전, 부상 후, 노년)"
              onChange={(e) => setNewLabel(e.target.value)}
              disabled={busy}
            />
            <button style={btn} onClick={addLook} disabled={busy || !newLabel.trim()}>
              모습 추가
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function Characters({
  projectId,
  refreshKey,
}: {
  projectId: string
  refreshKey: number
}) {
  const [chars, setChars] = useState<Character[] | null>(null)
  const [error, setError] = useState('')

  const refresh = useCallback(() => {
    setError('')
    listCharacters(projectId)
      .then(setChars)
      .catch((e: unknown) => setError(String(e)))
  }, [projectId])

  useEffect(() => {
    refresh()
  }, [refresh, refreshKey])

  return (
    <section>
      <div style={{ ...sectionTitle, marginBottom: 4 }}>
        캐릭터 뱅크{chars ? ` (${chars.length})` : ''}
      </div>
      <p style={{ ...muted, margin: '0 0 12px' }}>
        캐릭터별 성격과 시점별 외형을 관리합니다. 회차에서 인물을 추출해 채워집니다.
      </p>
      {error && <p style={errText}>{error}</p>}
      {!chars && !error && <p style={muted}>불러오는 중…</p>}
      {chars && chars.length === 0 && (
        <p style={muted}>아직 등록된 캐릭터가 없습니다. 회차 탭에서 인물을 추출해 저장해보세요.</p>
      )}
      {chars?.map((ch) => (
        <CharacterCard key={ch.id} ch={ch} refreshKey={refreshKey} onChanged={refresh} />
      ))}
    </section>
  )
}
