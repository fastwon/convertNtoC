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
  image: KeySlot
  ready: boolean
}
export type SaveResult = { ok: boolean; message: string; masked: string | null }
export type Slot = 'anthropic' | 'gemini' | 'image'

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
  image_model_ref: string | null
  font_settings: Record<string, unknown> | null
  created_at: string
}
export type ProjectCreate = {
  name: string
  style_prompt?: string
  image_model_ref?: string | null
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
