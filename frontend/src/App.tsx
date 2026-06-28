import { useCallback, useEffect, useState } from 'react'
import { getStatus, type SettingsStatus } from './api'
import Settings from './Settings'

export default function App() {
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

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32, maxWidth: 720, margin: '0 auto' }}>
      <h1>convertN2C</h1>
      <p>소설 → 만화 변환 데스크톱 앱</p>
      {error && <p style={{ color: 'crimson' }}>백엔드 연결 오류: {error}</p>}
      {!status && !error && <p>불러오는 중…</p>}
      {status && <Settings status={status} onChanged={refresh} />}
    </main>
  )
}
