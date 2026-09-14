// Idle-session config, deploy-time-tunable via env vars (same convention as
// VITE_API_BASE_URL in lib/api.ts) rather than hardcoded, so ops can adjust
// per environment without a code change.
export const IDLE_TIMEOUT_MINUTES = Number(import.meta.env.VITE_IDLE_TIMEOUT_MINUTES ?? 30)
export const IDLE_WARNING_SECONDS = Number(import.meta.env.VITE_IDLE_WARNING_SECONDS ?? 60)
