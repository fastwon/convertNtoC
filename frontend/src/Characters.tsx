import { useCallback, useEffect, useRef, useState } from 'react'
import {
  createAppearance,
  deleteAppearance,
  deleteCharacter,
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
import { btn, btnDanger, card, input } from './ui'

function AppearanceRow({ ap, onChanged }: { ap: Appearance; onChanged: () => void }) {
  const [label, setLabel] = useState(ap.label)
  const [desc, setDesc] = useState(ap.description)
  const [epNum, setEpNum] = useState(
    ap.source_episode_number === null ? '' : String(ap.source_episode_number),
  )
  const [busy, setBusy] = useState(false)
  const [imgV, setImgV] = useState(0)
  const [hasImg, setHasImg] = useState(!!ap.ref_image_path)
  const fileRef = useRef<HTMLInputElement>(null)

  async function save() {
    setBusy(true)
    try {
      const n = epNum.trim() === '' ? null : Number(epNum)
      await updateAppearance(ap.id, {
        label: label.trim(),
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
      <div style={{ flexShrink: 0, textAlign: 'center' }}>
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
          style={{ ...btn, marginTop: 4, fontSize: 11, padding: '3px 6px' }}
          onClick={() => fileRef.current?.click()}
          disabled={busy}
        >
          이미지
        </button>
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <input
            style={{ ...input, flex: 1 }}
            value={label}
            placeholder="모습 이름 (예: 기본, 10년 전, 부상 후)"
            onChange={(e) => setLabel(e.target.value)}
            disabled={busy}
          />
          <input
            style={{ ...input, width: 90 }}
            value={epNum}
            placeholder="회차"
            onChange={(e) => setEpNum(e.target.value)}
            disabled={busy}
          />
          {ap.is_default && (
            <span style={{ fontSize: 11, color: '#1e6fd0', flexShrink: 0 }}>기본</span>
          )}
        </div>
        <textarea
          style={{ ...input, minHeight: 40, marginTop: 6, resize: 'vertical' }}
          value={desc}
          placeholder="이 시점의 외모·특징"
          onChange={(e) => setDesc(e.target.value)}
          disabled={busy}
        />
        <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
          <button style={{ ...btn, fontSize: 12 }} onClick={save} disabled={busy || !label.trim()}>
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

function CharacterCard({ ch, onChanged }: { ch: Character; onChanged: () => void }) {
  const [name, setName] = useState(ch.name)
  const [busy, setBusy] = useState(false)
  const [looks, setLooks] = useState<Appearance[] | null>(null)
  const [newLabel, setNewLabel] = useState('')

  const loadLooks = useCallback(() => {
    listAppearances(ch.id)
      .then(setLooks)
      .catch(() => setLooks([]))
  }, [ch.id])
  useEffect(() => {
    loadLooks()
  }, [loadLooks])

  async function saveName() {
    setBusy(true)
    try {
      await updateCharacter(ch.id, { name: name.trim() })
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
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input
          style={{ ...input, flex: 1, fontWeight: 700 }}
          value={name}
          onChange={(e) => setName(e.target.value)}
          disabled={busy}
        />
        <button style={btn} onClick={saveName} disabled={busy || !name.trim()}>
          이름 저장
        </button>
        <button style={btnDanger} onClick={removeChar} disabled={busy}>
          삭제
        </button>
      </div>

      <div style={{ marginTop: 6, fontSize: 12, color: '#888' }}>
        시점별 모습 — 회상·성장·부상 등 다른 모습을 추가하면 컷 생성 시 골라 쓸 수 있습니다.
      </div>

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
    <section style={{ marginTop: 24 }}>
      <h3>캐릭터 뱅크</h3>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      {!chars && !error && <p>불러오는 중…</p>}
      {chars && chars.length === 0 && (
        <p style={{ color: '#888' }}>
          아직 등록된 캐릭터가 없습니다. 아래 회차에서 인물을 추출해 저장해보세요.
        </p>
      )}
      {chars?.map((ch) => (
        <CharacterCard key={ch.id} ch={ch} onChanged={refresh} />
      ))}
    </section>
  )
}
