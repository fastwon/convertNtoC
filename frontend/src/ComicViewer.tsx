import { useEffect, useState } from 'react'
import {
  exportEpisode,
  letteredImageUrl,
  listPanels,
  openExportsFolder,
  panelImageUrl,
  type ExportFormat,
  type Panel,
} from './api'

/** Webtoon-style reader: the episode's finished cuts stacked vertically. */
export default function ComicViewer({ episodeId }: { episodeId: string }) {
  const [panels, setPanels] = useState<Panel[] | null>(null)
  const [ver] = useState(() => Date.now()) // cache-bust once per open
  const [exporting, setExporting] = useState<ExportFormat | null>(null)
  const [exportErr, setExportErr] = useState('')
  const [savedPath, setSavedPath] = useState('')

  useEffect(() => {
    listPanels(episodeId)
      .then(setPanels)
      .catch(() => setPanels([]))
  }, [episodeId])

  // finished cut = lettered image if present, else the raw generated image
  const src = (p: Panel): string | null =>
    p.lettered_path ? letteredImageUrl(p.id, ver) : p.image_path ? panelImageUrl(p.id, ver) : null

  async function doExport(format: ExportFormat) {
    setExporting(format)
    setExportErr('')
    setSavedPath('')
    try {
      const res = await exportEpisode(episodeId, format)
      setSavedPath(res.path)
    } catch (e: unknown) {
      setExportErr(String(e instanceof Error ? e.message : e))
    } finally {
      setExporting(null)
    }
  }

  const hasImage = !!panels?.some((p) => p.lettered_path || p.image_path)
  const expBtn = (fmt: ExportFormat, text: string) => (
    <button
      onClick={() => doExport(fmt)}
      disabled={!hasImage || exporting !== null}
      style={{
        background: '#2a2a2a',
        color: '#eee',
        border: '1px solid #444',
        borderRadius: 5,
        padding: '5px 12px',
        cursor: hasImage && exporting === null ? 'pointer' : 'not-allowed',
        fontSize: 13,
      }}
    >
      {exporting === fmt ? '내보내는 중…' : text}
    </button>
  )

  return (
    <div style={{ background: '#141414', padding: '16px 0', borderRadius: 8, marginTop: 8 }}>
      <div
        style={{
          maxWidth: 480,
          margin: '0 auto 12px',
          padding: '0 8px',
          display: 'flex',
          gap: 8,
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <span style={{ color: '#999', fontSize: 12, marginRight: 4 }}>내보내기</span>
        {expBtn('png', '세로 이미지(PNG)')}
        {expBtn('pdf', 'PDF')}
        {expBtn('zip', '컷 묶음(ZIP)')}
        {exportErr && <span style={{ color: '#f88', fontSize: 12 }}>{exportErr}</span>}
      </div>
      {savedPath && (
        <div
          style={{
            maxWidth: 480,
            margin: '-4px auto 12px',
            padding: '8px 10px',
            display: 'flex',
            gap: 10,
            alignItems: 'center',
            flexWrap: 'wrap',
            background: '#1c2a1c',
            border: '1px solid #2f4a2f',
            borderRadius: 6,
          }}
        >
          <span style={{ color: '#bfe6bf', fontSize: 12, wordBreak: 'break-all', flex: 1 }}>
            저장됨: {savedPath}
          </span>
          <button
            onClick={() => openExportsFolder().catch(() => {})}
            style={{
              background: '#2f4a2f',
              color: '#eaffea',
              border: '1px solid #3f5f3f',
              borderRadius: 5,
              padding: '5px 12px',
              cursor: 'pointer',
              fontSize: 13,
              flexShrink: 0,
            }}
          >
            폴더 열기
          </button>
        </div>
      )}
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
