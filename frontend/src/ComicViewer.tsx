import { useEffect, useState } from 'react'
import { letteredImageUrl, listPanels, panelImageUrl, type Panel } from './api'

/** Webtoon-style reader: the episode's finished cuts stacked vertically. */
export default function ComicViewer({ episodeId }: { episodeId: string }) {
  const [panels, setPanels] = useState<Panel[] | null>(null)
  const [ver] = useState(() => Date.now()) // cache-bust once per open

  useEffect(() => {
    listPanels(episodeId)
      .then(setPanels)
      .catch(() => setPanels([]))
  }, [episodeId])

  // finished cut = lettered image if present, else the raw generated image
  const src = (p: Panel): string | null =>
    p.lettered_path ? letteredImageUrl(p.id, ver) : p.image_path ? panelImageUrl(p.id, ver) : null

  return (
    <div style={{ background: '#141414', padding: '16px 0', borderRadius: 8, marginTop: 8 }}>
      <div style={{ maxWidth: 480, margin: '0 auto', padding: '0 8px' }}>
        {!panels && <p style={{ color: '#999', textAlign: 'center' }}>불러오는 중…</p>}
        {panels && panels.length === 0 && (
          <p style={{ color: '#999', textAlign: 'center' }}>
            먼저 콘티를 생성하고 컷 이미지를 만들어 주세요.
          </p>
        )}
        {panels?.map((p) => {
          const s = src(p)
          return s ? (
            <img
              key={p.id}
              src={s}
              alt={`컷 ${p.order + 1}`}
              style={{ width: '100%', display: 'block', marginBottom: 6, borderRadius: 3 }}
            />
          ) : (
            <div
              key={p.id}
              style={{
                color: '#888',
                textAlign: 'center',
                padding: 24,
                marginBottom: 6,
                border: '1px dashed #444',
                borderRadius: 4,
                fontSize: 13,
              }}
            >
              컷 {p.order + 1}: 이미지 없음
            </div>
          )
        })}
      </div>
    </div>
  )
}
