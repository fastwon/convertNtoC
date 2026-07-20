import type { CSSProperties } from 'react'

export const card: CSSProperties = {
  border: '1px solid #ddd',
  borderRadius: 10,
  padding: 16,
  marginBottom: 12,
}

export const btn: CSSProperties = {
  padding: '8px 14px',
  borderRadius: 6,
  border: '1px solid #bbb',
  background: '#f6f6f6',
  cursor: 'pointer',
}

export const btnPrimary: CSSProperties = {
  ...btn,
  background: '#2d6cdf',
  borderColor: '#2d6cdf',
  color: '#fff',
}

export const btnDanger: CSSProperties = {
  ...btn,
  color: '#c0392b',
  borderColor: '#e0b4ae',
}

export const input: CSSProperties = {
  width: '100%',
  padding: 8,
  borderRadius: 6,
  border: '1px solid #ccc',
  boxSizing: 'border-box',
}

export const label: CSSProperties = {
  display: 'block',
  fontSize: 13,
  color: '#555',
  margin: '10px 0 4px',
}
