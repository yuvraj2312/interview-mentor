// Categorical slots 1-3 from the dataviz skill's validated default palette
// (references/palette.md), fixed order — validated all-pairs CVD-safe via
// scripts/validate_palette.js against a white card surface.
export const SERIES_COLORS = {
  technical: '#2a78d6',
  communication: '#eb6834',
  completeness: '#1baf7a',
} as const

// Fixed status scale (never reused as a categorical slot) — good/warning/critical
// map to roadmap priority low/medium/high and skill trend improving/declining.
export const STATUS_COLORS = {
  good: '#0ca30c',
  warning: '#fab219',
  critical: '#d03b3b',
} as const

// Chrome (gridlines/axes) matches the app's existing slate palette rather than
// the skill's placeholder ink tokens, per the skill's own guidance to substitute
// a design system's own tokens for chrome.
export const CHART_GRID_COLOR = '#e2e8f0' // slate-200
export const CHART_AXIS_COLOR = '#94a3b8' // slate-400
