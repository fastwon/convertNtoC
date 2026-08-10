import type { CSSProperties } from 'react'

// ---- palette (light, clean — one accent) --------------------------------
export const c = {
  bg: '#f5f6f8',
  surface: '#ffffff',
  subtle: '#fafbfc',
  border: '#e7e9ee',
  borderStrong: '#d6d9e0',
  text: '#1c2024',
  muted: '#666c76',
  faint: '#969ba4',
  accent: '#3b63f0',
  accentSoft: '#eef1fe',
  danger: '#d0463f',
  dangerSoft: '#fbeceb',
  success: '#1c8a4e',
  successSoft: '#e9f6ee',
}

// ---- surfaces -----------------------------------------------------------
export const card: CSSProperties = {
  background: c.surface,
  border: `1px solid ${c.border}`,
  borderRadius: 12,
  padding: 18,
  marginBottom: 14,
  boxShadow: '0 1px 2px rgba(20, 25, 35, 0.04)',
}

/** lighter nested container (rows inside a card) */
export const subCard: CSSProperties = {
  background: c.subtle,
  border: `1px solid ${c.border}`,
  borderRadius: 9,
  padding: 12,
}

// ---- buttons ------------------------------------------------------------
const btnBase: CSSProperties = {
  padding: '8px 14px',
  borderRadius: 8,
  border: '1px solid transparent',
  fontSize: 14,
  fontWeight: 500,
  lineHeight: 1.2,
  cursor: 'pointer',
  whiteSpace: 'nowrap',
}

export const btn: CSSProperties = {
  ...btnBase,
  background: c.surface,
  borderColor: c.borderStrong,
  color: c.text,
}

export const btnPrimary: CSSProperties = {
  ...btnBase,
  background: c.accent,
  color: '#fff',
}

export const btnDanger: CSSProperties = {
  ...btnBase,
  background: c.surface,
  borderColor: c.dangerSoft,
  color: c.danger,
}

export const btnGhost: CSSProperties = {
  ...btnBase,
  background: 'transparent',
  color: c.muted,
}

/** compact button for dense toolbars */
export const btnSm: CSSProperties = {
  ...btn,
  padding: '5px 10px',
  fontSize: 13,
}

// ---- form fields --------------------------------------------------------
export const input: CSSProperties = {
  width: '100%',
  padding: '9px 11px',
  borderRadius: 8,
  border: `1px solid ${c.borderStrong}`,
  boxSizing: 'border-box',
  fontSize: 14,
  background: c.surface,
  color: c.text,
  fontFamily: 'inherit',
}

export const label: CSSProperties = {
  display: 'block',
  fontSize: 12.5,
  fontWeight: 600,
  color: c.muted,
  margin: '12px 0 5px',
}

// ---- typography ---------------------------------------------------------
export const pageTitle: CSSProperties = {
  fontSize: 22,
  fontWeight: 700,
  color: c.text,
  margin: '0 0 18px',
  letterSpacing: '-0.01em',
}

export const sectionTitle: CSSProperties = {
  fontSize: 15,
  fontWeight: 700,
  color: c.text,
}

export const muted: CSSProperties = { color: c.muted, fontSize: 13 }
export const faint: CSSProperties = { color: c.faint, fontSize: 12 }
export const okText: CSSProperties = { color: c.success, fontSize: 13, fontWeight: 500 }
export const errText: CSSProperties = { color: c.danger, fontSize: 13 }

// ---- badge --------------------------------------------------------------
type BadgeKind = 'accent' | 'muted' | 'success' | 'danger'
export function badge(kind: BadgeKind = 'muted'): CSSProperties {
  const map: Record<BadgeKind, [string, string]> = {
    accent: [c.accentSoft, c.accent],
    muted: ['#eef0f3', c.muted],
    success: [c.successSoft, c.success],
    danger: [c.dangerSoft, c.danger],
  }
  const [bg, fg] = map[kind]
  return {
    display: 'inline-block',
    background: bg,
    color: fg,
    fontSize: 11.5,
    fontWeight: 600,
    padding: '2px 8px',
    borderRadius: 999,
    flexShrink: 0,
  }
}

// ---- tabs ---------------------------------------------------------------
export const tabBar: CSSProperties = {
  display: 'flex',
  gap: 4,
  borderBottom: `1px solid ${c.border}`,
  marginBottom: 18,
}

export function tabBtn(active: boolean): CSSProperties {
  return {
    background: 'none',
    border: 'none',
    borderBottom: `2px solid ${active ? c.accent : 'transparent'}`,
    color: active ? c.text : c.muted,
    fontWeight: active ? 700 : 500,
    fontSize: 14.5,
    padding: '10px 14px',
    marginBottom: -1,
    cursor: 'pointer',
  }
}
