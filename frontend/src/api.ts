// ---- shared ----
async function jsonOrThrow<T>(r: Response): Promise<T> {
  if (!r.ok) {
    let msg = `요청 실패 (${r.status})`
    try {
      const d = (await r.json()) as { detail?: string }
      if (d?.detail) msg = d.detail
    } catch {
      /* non-JSON error body */
    }
    throw new Error(msg)
  }
  return r.json() as Promise<T>
}

// ---- settings / keys ----
export type KeySlot = { present: boolean; masked: string | null }
export type SettingsStatus = {
  free_mode: boolean
  active_provider: 'gemini' | 'claude'
  anthropic: KeySlot
  gemini: KeySlot
  image_provider: 'pollinations' | 'gemini'
  ready: boolean
}
export type SaveResult = { ok: boolean; message: string; masked: string | null }
export type Slot = 'anthropic' | 'gemini'

export async function getStatus(): Promise<SettingsStatus> {
  return jsonOrThrow(await fetch('/api/settings/status'))
}

export async function setFreeMode(enabled: boolean): Promise<void> {
  await fetch('/api/settings/free-mode', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  })
}

export async function setImageProvider(provider: 'pollinations' | 'gemini'): Promise<void> {
  await fetch('/api/settings/image-provider', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider }),
  })
}

export async function saveKey(slot: Slot, key: string): Promise<SaveResult> {
  return jsonOrThrow(
    await fetch(`/api/settings/${slot}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key }),
    }),
  )
}

export async function deleteKey(slot: Slot): Promise<void> {
  await fetch(`/api/settings/${slot}`, { method: 'DELETE' })
}

// ---- projects ----
export type Project = {
  id: string
  name: string
  style_prompt: string
  font_settings: Record<string, unknown> | null
  created_at: string
}
export type ProjectCreate = {
  name: string
  style_prompt?: string
  font_settings?: Record<string, unknown> | null
}
export type ProjectPatch = Partial<ProjectCreate>

export async function listProjects(): Promise<Project[]> {
  return jsonOrThrow(await fetch('/api/projects'))
}
export async function createProject(body: ProjectCreate): Promise<Project> {
  return jsonOrThrow(
    await fetch('/api/projects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  )
}
export async function getProject(id: string): Promise<Project> {
  return jsonOrThrow(await fetch(`/api/projects/${id}`))
}
export async function updateProject(id: string, patch: ProjectPatch): Promise<Project> {
  return jsonOrThrow(
    await fetch(`/api/projects/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    }),
  )
}
export async function deleteProject(id: string): Promise<void> {
  const r = await fetch(`/api/projects/${id}`, { method: 'DELETE' })
  if (!r.ok) throw new Error('삭제 실패')
}

// ---- episodes ----
export type Episode = {
  id: string
  project_id: string
  number: number
  raw_text: string
  summary: string | null
  status: string
  created_at: string
}

export async function listEpisodes(projectId: string): Promise<Episode[]> {
  return jsonOrThrow(await fetch(`/api/projects/${projectId}/episodes`))
}
export async function createEpisode(
  projectId: string,
  body: { number?: number; raw_text?: string },
): Promise<Episode> {
  return jsonOrThrow(
    await fetch(`/api/projects/${projectId}/episodes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  )
}
export async function updateEpisodeText(episodeId: string, raw_text: string): Promise<Episode> {
  return jsonOrThrow(
    await fetch(`/api/episodes/${episodeId}/text`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_text }),
    }),
  )
}
export async function deleteEpisode(episodeId: string): Promise<void> {
  const r = await fetch(`/api/episodes/${episodeId}`, { method: 'DELETE' })
  if (!r.ok) throw new Error('회차 삭제 실패')
}

// ---- character extraction ----
export type ExtractedCharacter = {
  name: string
  is_new: boolean
  matched_character_id: string | null
  traits: string
  current_traits: string | null // bank's current description (existing characters)
}
export type ExtractionResult = { provider: string; characters: ExtractedCharacter[] }

export async function extractCharacters(episodeId: string): Promise<ExtractionResult> {
  return jsonOrThrow(
    await fetch(`/api/episodes/${episodeId}/extract-characters`, { method: 'POST' }),
  )
}

// ---- character bank ----
export type Character = {
  id: string
  project_id: string
  name: string
  traits: { description?: string } | null
  ref_image_path: string | null
  created_at: string
}

export type ConfirmItem = {
  name: string
  traits: string
  save: boolean
  matched_character_id?: string | null
}

export async function listCharacters(projectId: string): Promise<Character[]> {
  return jsonOrThrow(await fetch(`/api/projects/${projectId}/characters`))
}
export async function confirmCharacters(
  episodeId: string,
  characters: ConfirmItem[],
): Promise<{ saved: Character[]; updated: Character[] }> {
  return jsonOrThrow(
    await fetch(`/api/episodes/${episodeId}/confirm-characters`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ characters }),
    }),
  )
}
export async function updateCharacter(
  id: string,
  patch: { name?: string; traits?: string },
): Promise<Character> {
  return jsonOrThrow(
    await fetch(`/api/characters/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    }),
  )
}
export async function deleteCharacter(id: string): Promise<void> {
  const r = await fetch(`/api/characters/${id}`, { method: 'DELETE' })
  if (!r.ok) throw new Error('캐릭터 삭제 실패')
}
// ---- appearances (a character's looks over time) ----
export type Appearance = {
  id: string
  character_id: string
  label: string
  description: string
  ref_image_path: string | null
  source_episode_number: number | null
  is_default: boolean
  created_at: string
}

export async function listAppearances(characterId: string): Promise<Appearance[]> {
  return jsonOrThrow(await fetch(`/api/characters/${characterId}/appearances`))
}
export async function createAppearance(
  characterId: string,
  body: { label: string; description?: string; source_episode_number?: number | null },
): Promise<Appearance> {
  return jsonOrThrow(
    await fetch(`/api/characters/${characterId}/appearances`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  )
}
export async function updateAppearance(
  id: string,
  patch: { label?: string; description?: string; source_episode_number?: number | null },
): Promise<Appearance> {
  return jsonOrThrow(
    await fetch(`/api/appearances/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    }),
  )
}
export async function makeDefaultAppearance(id: string): Promise<void> {
  await fetch(`/api/appearances/${id}/default`, { method: 'POST' })
}
export async function deleteAppearance(id: string): Promise<void> {
  const r = await fetch(`/api/appearances/${id}`, { method: 'DELETE' })
  if (!r.ok) {
    const d = (await r.json().catch(() => ({}))) as { detail?: string }
    throw new Error(d.detail ?? '모습 삭제 실패')
  }
}
export async function uploadRefImage(appearanceId: string, file: File): Promise<Appearance> {
  const fd = new FormData()
  fd.append('file', file)
  return jsonOrThrow(
    await fetch(`/api/appearances/${appearanceId}/ref-image`, { method: 'POST', body: fd }),
  )
}
export async function describeAppearanceFromImage(
  appearanceId: string,
): Promise<{ description: string }> {
  return jsonOrThrow(
    await fetch(`/api/appearances/${appearanceId}/describe-from-image`, { method: 'POST' }),
  )
}
// ---- global memory ----
export type Usage = {
  input: number
  output: number
  cache_read: number
  cache_write: number
} | null
export type SummarizeResult = { summary: string; provider: string; usage: Usage }

export async function getWorldBible(projectId: string): Promise<{ world_bible: string }> {
  return jsonOrThrow(await fetch(`/api/projects/${projectId}/world-bible`))
}
export async function setWorldBible(
  projectId: string,
  world_bible: string,
): Promise<{ world_bible: string }> {
  return jsonOrThrow(
    await fetch(`/api/projects/${projectId}/world-bible`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ world_bible }),
    }),
  )
}
export async function previewMemory(
  projectId: string,
  before?: number,
): Promise<{ memory: string; chars: number }> {
  const q = before === undefined ? '' : `?before=${before}`
  return jsonOrThrow(await fetch(`/api/projects/${projectId}/memory${q}`))
}
export async function summarizeEpisode(episodeId: string): Promise<SummarizeResult> {
  return jsonOrThrow(await fetch(`/api/episodes/${episodeId}/summarize`, { method: 'POST' }))
}

// ---- storyboard (콘티) ----
export type PanelCharacter = { name: string; appearance_label: string }
export type DialogueType = 'speech' | 'thought' | 'narration'
export type PanelDialogue = {
  type?: DialogueType
  speaker: string
  text: string
  x?: number // bubble top-left, normalized 0..1
  y?: number
}
export type Panel = {
  id: string
  episode_id: string
  order: number
  scene: string
  characters: PanelCharacter[] | null
  prompt: string
  image_path: string | null
  lettered_path: string | null
  dialogue: PanelDialogue[] | null
  created_at: string
}

export async function generateStoryboard(
  episodeId: string,
): Promise<{ provider: string; panels: Panel[]; usage: Usage }> {
  return jsonOrThrow(await fetch(`/api/episodes/${episodeId}/storyboard`, { method: 'POST' }))
}
export async function listPanels(episodeId: string): Promise<Panel[]> {
  return jsonOrThrow(await fetch(`/api/episodes/${episodeId}/panels`))
}
export async function updatePanel(
  panelId: string,
  patch: { scene?: string; dialogue?: PanelDialogue[] },
): Promise<Panel> {
  return jsonOrThrow(
    await fetch(`/api/panels/${panelId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    }),
  )
}
export async function deletePanel(panelId: string): Promise<void> {
  const r = await fetch(`/api/panels/${panelId}`, { method: 'DELETE' })
  if (!r.ok) throw new Error('컷 삭제 실패')
}
export async function letterPanel(
  panelId: string,
): Promise<{ lettered_path: string; bubbles: number }> {
  return jsonOrThrow(await fetch(`/api/panels/${panelId}/letter`, { method: 'POST' }))
}
export function letteredImageUrl(panelId: string, version: number | string = ''): string {
  return `/api/panels/${panelId}/lettered-image?v=${encodeURIComponent(String(version))}`
}
export async function generatePanelImage(
  panelId: string,
): Promise<{ generator: string; prompt: string; image_path: string }> {
  return jsonOrThrow(await fetch(`/api/panels/${panelId}/image`, { method: 'POST' }))
}
export async function uploadPanelImage(panelId: string, file: File): Promise<{ image_path: string }> {
  const fd = new FormData()
  fd.append('file', file)
  return jsonOrThrow(await fetch(`/api/panels/${panelId}/upload-image`, { method: 'POST', body: fd }))
}
export async function getPanelPrompt(panelId: string): Promise<{ prompt: string }> {
  return jsonOrThrow(await fetch(`/api/panels/${panelId}/prompt`))
}
export function panelImageUrl(panelId: string, version: number | string = ''): string {
  return `/api/panels/${panelId}/image?v=${encodeURIComponent(String(version))}`
}

export type ExportFormat = 'png' | 'pdf' | 'zip'
export type ExportResult = { path: string; folder: string; filename: string }

/** Save the episode export to the user's exports folder (server-side write —
 *  reliable inside the PyWebView desktop shell). Returns the saved location. */
export async function exportEpisode(
  episodeId: string,
  format: ExportFormat,
): Promise<ExportResult> {
  return jsonOrThrow(
    await fetch(`/api/episodes/${episodeId}/export?format=${format}`, { method: 'POST' }),
  )
}

/** Open the exports folder in Windows Explorer. */
export async function openExportsFolder(): Promise<{ folder: string }> {
  return jsonOrThrow(await fetch('/api/exports/open', { method: 'POST' }))
}

export function refImageUrl(appearanceId: string, version: number | string = ''): string {
  // pass a changing `version` (e.g. Date.now()) after re-upload to bust the cache
  return `/api/appearances/${appearanceId}/ref-image?v=${encodeURIComponent(String(version))}`
}

// ---- system / storage ----
export type SystemInfo = {
  data_dir: string
  db_path: string
  db_exists: boolean
  db_size: number
  images_size: number
  backup_size: number
  total_size: number
  counts: { projects: number; episodes: number; characters: number; panels: number }
}

export async function getSystemInfo(): Promise<SystemInfo> {
  return jsonOrThrow(await fetch('/api/system/info'))
}

export async function openDataFolder(): Promise<{ folder: string }> {
  return jsonOrThrow(await fetch('/api/system/open-data-folder', { method: 'POST' }))
}

export async function purgeBackups(): Promise<{ freed: number }> {
  return jsonOrThrow(await fetch('/api/system/purge-backups', { method: 'POST' }))
}

// ---- usage / cost ----
export type UsageOp = {
  operation: string
  label: string
  calls: number
  input: number
  output: number
  images: number
}
export type ProjectUsage = {
  totals: { input: number; output: number; cache_read: number; cache_write: number; images: number }
  by_operation: UsageOp[]
  est_cost_usd: number
  priced: boolean
}

export async function getProjectUsage(projectId: string): Promise<ProjectUsage> {
  return jsonOrThrow(await fetch(`/api/projects/${projectId}/usage`))
}
