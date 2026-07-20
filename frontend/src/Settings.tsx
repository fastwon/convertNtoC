import { useCallback, useEffect, useState } from 'react'
import { deleteKey, getStatus, saveKey, type SettingsStatus, type Slot } from './api'
import { btnDanger, btnPrimary, card, input } from './ui'

function KeyRow(props: {
  label: string
  slot: Slot
  present: boolean
  masked: string | null
  hint: string
  onChanged: () => void
}) {
  const { label, slot, present, masked, hint, onChanged } = props
  const [value, setValue] = useState('')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)

  async function save() {
    setBusy(true)
    setMsg(null)
    try {
      const res = await saveKey(slot, value)
      setMsg({ ok: res.ok, text: res.message })
      if (res.ok) {
        setValue('')
        onChanged()
      }
    } catch (e: unknown) {
      setMsg({ ok: false, text: String(e) })
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    setBusy(true)
    setMsg(null)
    try {
      await deleteKey(slot)
      onChanged()
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong>{label}</strong>
        {present ? (
          <span style={{ color: 'green' }}>저장됨 {masked}</span>
        ) : (
          <span style={{ color: '#999' }}>미설정</span>
        )}
      </div>
      <p style={{ color: '#666', fontSize: 13, margin: '6px 0' }}>{hint}</p>
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          style={input}
          type="password"
          value={value}
          placeholder="키 입력"
          onChange={(e) => setValue(e.target.value)}
          disabled={busy}
        />
        <button style={btnPrimary} onClick={save} disabled={busy || !value}>
          저장·검증
        </button>
        {present && (
          <button style={btnDanger} onClick={remove} disabled={busy}>
            삭제
          </button>
        )}
      </div>
      {msg && <p style={{ color: msg.ok ? 'green' : 'crimson', marginTop: 8 }}>{msg.text}</p>}
    </div>
  )
}

export default function Settings() {
  const [status, setStatus] = useState<SettingsStatus | null>(null)
  const [error, setError] = useState('')

  const refresh = useCallback(() => {
    setError('')
    getStatus()
      .then(setStatus)
      .catch((e: unknown) => setError(String(e)))
  }, [])
  useEffect(() => {
    refresh()
  }, [refresh])

  if (error) return <p style={{ color: 'crimson' }}>설정 로드 오류: {error}</p>
  if (!status) return <p>불러오는 중…</p>

  return (
    <section>
      <h2>설정 · API 키</h2>
      <p style={{ color: status.ready ? 'green' : '#c47f00' }}>
        {status.ready
          ? '사용 준비 완료 ✓'
          : 'LLM 기능(이후 단계)에는 Anthropic 키가 필요합니다. 지금은 없어도 개발/미리보기 가능.'}
      </p>
      <KeyRow
        label="Anthropic API 키"
        slot="anthropic"
        present={status.anthropic.present}
        masked={status.anthropic.masked}
        hint="Claude 호출용. 저장 시 models.list 호출로 유효성을 검증합니다. (무료 Gemini 옵션은 이후 단계에서 추가)"
        onChanged={refresh}
      />
      <KeyRow
        label="이미지 API 키"
        slot="image"
        present={status.image.present}
        masked={status.image.masked}
        hint="이미지 생성용. 공급자 확정(이후 단계) 전까지는 저장만 합니다."
        onChanged={refresh}
      />
      <p style={{ color: '#999', fontSize: 12 }}>
        키는 OS 자격증명 저장소에만 저장되며, 화면에는 마스킹되어 표시됩니다.
      </p>
    </section>
  )
}
