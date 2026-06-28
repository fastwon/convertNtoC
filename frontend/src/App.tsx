import { useEffect, useState } from 'react'

type Health = { status: string; app: string }

export default function App() {
  const [state, setState] = useState<'loading' | 'ok' | 'error'>('loading')
  const [detail, setDetail] = useState('')

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json() as Promise<Health>)
      .then((d) => {
        setState('ok')
        setDetail(`${d.app} · ${d.status}`)
      })
      .catch((e: unknown) => {
        setState('error')
        setDetail(String(e))
      })
  }, [])

  return (
    <main style={{ fontFamily: 'system-ui, sans-serif', padding: 32 }}>
      <h1>convertN2C</h1>
      <p>소설 → 만화 변환 데스크톱 앱 (P0 스캐폴딩)</p>
      {state === 'loading' && <p>백엔드 연결 확인 중…</p>}
      {state === 'ok' && <p style={{ color: 'green' }}>백엔드 연결됨 ✓ ({detail})</p>}
      {state === 'error' && <p style={{ color: 'crimson' }}>백엔드 연결 실패: {detail}</p>}
    </main>
  )
}
