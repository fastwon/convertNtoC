export type KeySlot = { present: boolean; masked: string | null }
export type SettingsStatus = { anthropic: KeySlot; image: KeySlot; ready: boolean }
export type SaveResult = { ok: boolean; message: string; masked: string | null }

export type Slot = 'anthropic' | 'image'

export async function getStatus(): Promise<SettingsStatus> {
  const r = await fetch('/api/settings/status')
  if (!r.ok) throw new Error('상태 조회 실패')
  return r.json() as Promise<SettingsStatus>
}

export async function saveKey(slot: Slot, key: string): Promise<SaveResult> {
  const r = await fetch(`/api/settings/${slot}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ key }),
  })
  return r.json() as Promise<SaveResult>
}

export async function deleteKey(slot: Slot): Promise<void> {
  await fetch(`/api/settings/${slot}`, { method: 'DELETE' })
}
