// Categorical slots 1-3 from the dataviz skill's validated default palette
// (references/palette.md), fixed order — validated all-pairs CVD-safe via
// scripts/validate_palette.js against a white card surface.
//
// These hexes must stay equal to the design tokens defined in src/index.css
// (@theme) — recharts needs plain hex for SVG fill/stroke, so index.css is
// the canonical source and this file mirrors it rather than resolving var().
export const SERIES_COLORS = {
  technical: '#2a78d6', // --color-accent-500
  communication: '#eb6834',
  completeness: '#1baf7a',
} as const

// Fixed status scale (never reused as a categorical slot) — good/warning/critical
// map to roadmap priority low/medium/high, skill trend improving/declining, and
// the ui/badge.tsx good/warning/critical variants (same hue family, see index.css).
export const STATUS_COLORS = {
  good: '#0ca30c', // --color-success-600
  warning: '#fab219', // --color-warning-600
  critical: '#d03b3b', // --color-danger-600
} as const

// Chrome (gridlines/axes) matches the app's design tokens (--color-border /
// ink-400) rather than the skill's placeholder ink tokens, per the skill's own
// guidance to substitute a design system's own tokens for chrome.
export const CHART_GRID_COLOR = '#e2e8f0' // --color-border
export const CHART_AXIS_COLOR = '#94a3b8' // slate-400 (chrome only, not a UI token)
