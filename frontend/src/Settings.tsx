import { useState } from 'react'
import { deleteKey, saveKey, type SettingsStatus, type Slot } from './api'

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
    <div style={{ border: '1px solid #ddd', borderRadius: 8, padding: 16, marginBottom: 12 }}>
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
          type="password"
          value={value}
          placeholder="키 입력"
          onChange={(e) => setValue(e.target.value)}
          disabled={busy}
          style={{ flex: 1, padding: 8 }}
        />
        <button onClick={save} disabled={busy || !value}>
          저장·검증
        </button>
        {present && (
          <button onClick={remove} disabled={busy}>
            삭제
          </button>
        )}
      </div>
      {msg && (
        <p style={{ color: msg.ok ? 'green' : 'crimson', marginTop: 8 }}>{msg.text}</p>
      )}
    </div>
  )
}

export default function Settings(props: { status: SettingsStatus; onChanged: () => void }) {
  const { status, onChanged } = props
  return (
    <section>
      <h2>설정 · API 키</h2>
      <p style={{ color: status.ready ? 'green' : 'crimson' }}>
        {status.ready ? '사용 준비 완료 ✓' : 'Anthropic 키를 입력해야 사용할 수 있습니다'}
      </p>
      <KeyRow
        label="Anthropic API 키"
        slot="anthropic"
        present={status.anthropic.present}
        masked={status.anthropic.masked}
        hint="Claude 호출용. 저장 시 models.list 호출로 유효성을 검증합니다."
        onChanged={onChanged}
      />
      <KeyRow
        label="이미지 API 키"
        slot="image"
        present={status.image.present}
        masked={status.image.masked}
        hint="이미지 생성용. 공급자 확정(P6) 전까지는 저장만 합니다."
        onChanged={onChanged}
      />
      <p style={{ color: '#999', fontSize: 12 }}>
        키는 OS 자격증명 저장소에만 저장되며, 화면에는 마스킹되어 표시됩니다.
      </p>
    </section>
  )
}
