import { useCallback, useEffect, useState } from 'react'
import {
  deleteKey,
  getStatus,
  getSystemInfo,
  openDataFolder,
  purgeBackups,
  saveKey,
  setFreeMode,
  setImageProvider,
  type SettingsStatus,
  type Slot,
  type SystemInfo,
} from './api'
import { badge, btn, btnDanger, btnPrimary, c, card, errText, input, muted, okText, pageTitle, sectionTitle } from './ui'

function fmtBytes(n: number): string {
  if (n < 1024) return `${n} B`
  const u = ['KB', 'MB', 'GB', 'TB']
  let v = n / 1024
  let i = 0
  while (v >= 1024 && i < u.length - 1) {
    v /= 1024
    i++
  }
  return `${v.toFixed(v < 10 ? 1 : 0)} ${u[i]}`
}

function StorageSection() {
  const [info, setInfo] = useState<SystemInfo | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')

  const load = useCallback(() => {
    setError('')
    getSystemInfo()
      .then(setInfo)
      .catch((e: unknown) => setError(String(e)))
  }, [])
  useEffect(() => {
    load()
  }, [load])

  async function purge() {
    if (!info) return
    if (!confirm('재업로드로 생긴 이전 이미지 백업(panels/old)을 모두 삭제할까요?\n현재 사용 중인 이미지는 그대로 유지됩니다.')) return
    setBusy(true)
    setMsg('')
    try {
      const r = await purgeBackups()
      setMsg(`백업 ${fmtBytes(r.freed)} 정리됨`)
      load()
    } catch (e: unknown) {
      setMsg(String(e instanceof Error ? e.message : e))
    } finally {
      setBusy(false)
    }
  }

  const row = (k: string, v: React.ReactNode) => (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '5px 0', borderBottom: `1px solid ${c.border}`, fontSize: 13 }}>
      <span style={{ color: c.muted }}>{k}</span>
      <span style={{ color: c.text, fontWeight: 500 }}>{v}</span>
    </div>
  )

  return (
    <div style={card}>
      <div style={sectionTitle}>스토리지</div>
      {error && <p style={errText}>{error}</p>}
      {!info && !error && <p style={muted}>불러오는 중…</p>}
      {info && (
        <>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', margin: '10px 0' }}>
            <span style={badge('muted')}>프로젝트 {info.counts.projects}</span>
            <span style={badge('muted')}>회차 {info.counts.episodes}</span>
            <span style={badge('muted')}>캐릭터 {info.counts.characters}</span>
            <span style={badge('muted')}>컷 {info.counts.panels}</span>
          </div>
          {row('총 사용량', fmtBytes(info.total_size))}
          {row('이미지', fmtBytes(info.images_size))}
          {row('데이터베이스', fmtBytes(info.db_size))}
          {row('백업(정리 가능)', fmtBytes(info.backup_size))}
          <div style={{ ...muted, fontSize: 12, margin: '10px 0 4px' }}>데이터 폴더</div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
            <code style={{ fontSize: 12, background: c.subtle, border: `1px solid ${c.border}`, borderRadius: 6, padding: '4px 8px', wordBreak: 'break-all', flex: 1, minWidth: 0 }}>
              {info.data_dir}
            </code>
            <button style={btn} onClick={() => openDataFolder().catch(() => {})}>
              폴더 열기
            </button>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 12 }}>
            <button style={btnDanger} onClick={purge} disabled={busy || info.backup_size === 0}>
              백업 정리 ({fmtBytes(info.backup_size)})
            </button>
            {msg && <span style={okText}>{msg}</span>}
          </div>
          <p style={{ ...muted, fontSize: 12, marginTop: 8, marginBottom: 0 }}>
            프로젝트 삭제는 대시보드에서 할 수 있어요. 삭제 시 그 프로젝트의 이미지·데이터가 모두
            제거됩니다.
          </p>
        </>
      )}
    </div>
  )
}

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
          <span style={okText}>저장됨 {masked}</span>
        ) : (
          <span style={{ color: c.faint, fontSize: 13 }}>미설정</span>
        )}
      </div>
      <p style={{ ...muted, margin: '6px 0' }}>{hint}</p>
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
      {msg && <p style={{ ...(msg.ok ? okText : errText), marginTop: 8 }}>{msg.text}</p>}
    </div>
  )
}

export default function Settings() {
  const [status, setStatus] = useState<SettingsStatus | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const refresh = useCallback(() => {
    setError('')
    getStatus()
      .then(setStatus)
      .catch((e: unknown) => setError(String(e)))
  }, [])
  useEffect(() => {
    refresh()
  }, [refresh])

  async function toggleFree(enabled: boolean) {
    setBusy(true)
    try {
      await setFreeMode(enabled)
      refresh()
    } finally {
      setBusy(false)
    }
  }

  async function changeImageProvider(provider: 'pollinations' | 'gemini') {
    setBusy(true)
    try {
      await setImageProvider(provider)
      refresh()
    } finally {
      setBusy(false)
    }
  }

  if (error) return <p style={errText}>설정 로드 오류: {error}</p>
  if (!status) return <p style={muted}>불러오는 중…</p>

  return (
    <section>
      <h2 style={pageTitle}>설정 · API 키</h2>

      <div style={card}>
        <label style={{ display: 'flex', gap: 10, alignItems: 'center', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={status.free_mode}
            disabled={busy}
            onChange={(e) => toggleFree(e.target.checked)}
          />
          <span>
            <strong>무료 버전 사용 (Gemini)</strong>
            <span style={{ color: '#888', fontSize: 13, marginLeft: 8 }}>
              끄면 Claude(유료·고품질) 사용
            </span>
          </span>
        </label>
        <p style={{ marginTop: 10, fontSize: 13, color: status.ready ? c.success : '#c47f00' }}>
          {status.ready
            ? `사용 준비 완료 ✓ (현재: ${status.active_provider === 'gemini' ? '무료 Gemini' : 'Claude'})`
            : status.free_mode
              ? '무료 모드입니다. 아래 Gemini 키를 입력하세요.'
              : 'Claude 모드입니다. 아래 Anthropic 키를 입력하세요.'}
        </p>
      </div>

      <KeyRow
        label="Gemini API 키 (무료)"
        slot="gemini"
        present={status.gemini.present}
        masked={status.gemini.masked}
        hint="무료 모드용. Google AI Studio(aistudio.google.com/apikey)에서 무료 발급. 저장 시 실제 호출로 검증합니다."
        onChanged={refresh}
      />
      <KeyRow
        label="Anthropic API 키 (Claude)"
        slot="anthropic"
        present={status.anthropic.present}
        masked={status.anthropic.masked}
        hint="Claude 모드용. 저장 시 models.list 호출로 검증합니다."
        onChanged={refresh}
      />
      <div style={card}>
        <strong>이미지 생성 공급자</strong>
        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <label style={{ display: 'flex', gap: 8, alignItems: 'flex-start', cursor: 'pointer' }}>
            <input
              type="radio"
              name="imgprov"
              checked={status.image_provider === 'pollinations'}
              disabled={busy}
              onChange={() => changeImageProvider('pollinations')}
            />
            <span>
              <b>Pollinations (무료)</b>
              <span style={{ color: '#888', fontSize: 13, marginLeft: 6 }}>
                키 불필요. 캐릭터 일관성은 약함.
              </span>
            </span>
          </label>
          <label style={{ display: 'flex', gap: 8, alignItems: 'flex-start', cursor: 'pointer' }}>
            <input
              type="radio"
              name="imgprov"
              checked={status.image_provider === 'gemini'}
              disabled={busy}
              onChange={() => changeImageProvider('gemini')}
            />
            <span>
              <b>Gemini 이미지 (유료)</b>
              <span style={{ color: '#888', fontSize: 13, marginLeft: 6 }}>
                Gemini 키 사용. Google Cloud 결제 등록 필요. 품질·일관성 더 좋음.
              </span>
            </span>
          </label>
        </div>
        <p style={{ color: '#999', fontSize: 12, marginTop: 8, marginBottom: 0 }}>
          Pollinations는 키가 필요 없고, Gemini 이미지는 위 Gemini 키를 그대로 사용합니다.
        </p>
      </div>

      <p style={{ color: c.faint, fontSize: 12 }}>
        키는 OS 자격증명 저장소에만 저장되며, 화면에는 마스킹되어 표시됩니다.
      </p>

      <StorageSection />
    </section>
  )
}
