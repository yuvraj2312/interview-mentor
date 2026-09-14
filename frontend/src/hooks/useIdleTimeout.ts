import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { logout as apiLogout } from '@/lib/api'
import { IDLE_TIMEOUT_MINUTES, IDLE_WARNING_SECONDS } from '@/lib/sessionConfig'
import { useAuthStore } from '@/store/authStore'
import { useLiveInterviewStore } from '@/store/liveInterviewStore'

const ACTIVITY_EVENTS = ['mousedown', 'mousemove', 'keydown', 'scroll', 'touchstart'] as const

// Auto-logs-out an idle user client-side (see ProtectedRoute.tsx for the
// mount point). Elapsed time is computed from a wall-clock timestamp, not a
// tick counter, so it stays correct even when the tab is backgrounded and
// the browser throttles setInterval - the moment the tab regains visibility
// (or the throttled interval eventually fires), Date.now() minus the last
// recorded activity is still accurate. This is what fixes the reported bug
// of a multi-hour abandoned tab still showing the Dashboard as logged in.
export function useIdleTimeout() {
  const navigate = useNavigate()
  const [secondsUntilLogout, setSecondsUntilLogout] = useState<number | null>(null)
  const lastActivityRef = useRef<number>(Date.now())

  const timeoutMs = IDLE_TIMEOUT_MINUTES * 60 * 1000
  const warningMs = IDLE_WARNING_SECONDS * 1000

  const recordActivity = useCallback(() => {
    lastActivityRef.current = Date.now()
    setSecondsUntilLogout(null)
  }, [])

  const logout = useCallback(() => {
    const { refreshToken, clearTokens } = useAuthStore.getState()
    if (refreshToken) {
      apiLogout(refreshToken).catch(() => {})
    }
    clearTokens()
    navigate('/login', { replace: true })
  }, [navigate])

  useEffect(() => {
    for (const event of ACTIVITY_EVENTS) {
      window.addEventListener(event, recordActivity, { passive: true })
    }
    return () => {
      for (const event of ACTIVITY_EVENTS) {
        window.removeEventListener(event, recordActivity)
      }
    }
  }, [recordActivity])

  useEffect(() => {
    const tick = () => {
      // A live interview counts as continuous activity: never idle-timeout
      // mid-interview just because the user is speaking/listening rather
      // than moving the mouse (see liveInterviewStore's docstring).
      if (useLiveInterviewStore.getState().isLive) {
        recordActivity()
        return
      }

      const elapsed = Date.now() - lastActivityRef.current
      if (elapsed >= timeoutMs) {
        logout()
        return
      }
      setSecondsUntilLogout(
        elapsed >= timeoutMs - warningMs ? Math.max(0, Math.ceil((timeoutMs - elapsed) / 1000)) : null,
      )
    }

    tick()
    const interval = window.setInterval(tick, 1000)
    document.addEventListener('visibilitychange', tick)
    return () => {
      window.clearInterval(interval)
      document.removeEventListener('visibilitychange', tick)
    }
  }, [logout, recordActivity, timeoutMs, warningMs])

  return { secondsUntilLogout, stayActive: recordActivity }
}
