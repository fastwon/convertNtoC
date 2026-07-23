import { useCallback, useEffect, useRef, useState } from 'react'
import {
  deleteCharacter,
  listCharacters,
  refImageUrl,
  updateCharacter,
  uploadRefImage,
  type Character,
} from './api'
import { btn, btnDanger, card, input } from './ui'

function CharacterCard({ ch, onChanged }: { ch: Character; onChanged: () => void }) {
  const [name, setName] = useState(ch.name)
  const [traits, setTraits] = useState(ch.traits?.description ?? '')
  const [busy, setBusy] = useState(false)
  const [imgVersion, setImgVersion] = useState(0)
  const [hasImg, setHasImg] = useState(!!ch.ref_image_path)
  const fileRef = useRef<HTMLInputElement>(null)

  async function save() {
    setBusy(true)
    try {
      await updateCharacter(ch.id, { name: name.trim(), traits })
      onChanged()
    } finally {
      setBusy(false)
    }
  }
  async function remove() {
    if (!confirm(`'${ch.name}' 캐릭터를 삭제할까요?`)) return
    setBusy(true)
    try {
      await deleteCharacter(ch.id)
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
      await uploadRefImage(ch.id, f)
      setHasImg(true)
      setImgVersion((v) => v + 1)
    } catch (err: unknown) {
      alert(String(err instanceof Error ? err.message : err))
    } finally {
      setBusy(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  return (
    <div style={{ ...card, display: 'flex', gap: 14 }}>
      <div style={{ flexShrink: 0, textAlign: 'center' }}>
        <div
          style={{
            width: 84,
            height: 84,
            borderRadius: 8,
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
              src={refImageUrl(ch.id, imgVersion)}
              alt={ch.name}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />
          ) : (
            <span style={{ color: '#bbb', fontSize: 12 }}>이미지<br />없음</span>
          )}
        </div>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          style={{ display: 'none' }}
          onChange={onFile}
        />
        <button
          style={{ ...btn, marginTop: 6, fontSize: 12, padding: '4px 8px' }}
          onClick={() => fileRef.current?.click()}
          disabled={busy}
        >
          {hasImg ? '이미지 변경' : '참조 이미지'}
        </button>
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <input style={input} value={name} onChange={(e) => setName(e.target.value)} disabled={busy} />
        <textarea
          style={{ ...input, minHeight: 48, marginTop: 6, resize: 'vertical' }}
          value={traits}
          placeholder="외모·성격 특징"
          onChange={(e) => setTraits(e.target.value)}
          disabled={busy}
        />
        <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
          <button style={btn} onClick={save} disabled={busy || !name.trim()}>
            저장
          </button>
          <button style={btnDanger} onClick={remove} disabled={busy}>
            삭제
          </button>
        </div>
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

  // reload when the bank changes here OR when episodes save new characters
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
