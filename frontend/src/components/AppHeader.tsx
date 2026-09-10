import { GraduationCap } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { logout as logoutRequest } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const NAV_LINKS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/analytics', label: 'Analytics' },
  { to: '/sessions', label: 'Sessions' },
  { to: '/roadmap', label: 'Roadmap' },
]

export function AppHeader() {
  const navigate = useNavigate()
  const location = useLocation()
  const refreshToken = useAuthStore((state) => state.refreshToken)
  const clearTokens = useAuthStore((state) => state.clearTokens)

  async function handleLogout() {
    if (refreshToken) {
      await logoutRequest(refreshToken).catch(() => {
        // Even if the server call fails (e.g. token already expired),
        // clear local state so the user is logged out client-side.
      })
    }
    clearTokens()
    navigate('/login', { replace: true })
  }

  return (
    <header className="sticky top-0 z-10 border-b border-border bg-surface/95 backdrop-blur">
      <div className="flex items-center justify-between overflow-x-auto px-6 py-3">
        <div className="flex items-center gap-8">
          <Link to="/dashboard" className="flex items-center gap-2">
            <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-ink-900 text-white">
              <GraduationCap className="size-4" />
            </span>
            <span className="text-base font-semibold text-ink-900">Interview Mentor</span>
          </Link>
          <nav className="flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const isActive = location.pathname.startsWith(link.to)
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={cn(
                    'whitespace-nowrap border-b-2 px-2 py-1 text-sm transition-colors',
                    isActive
                      ? 'border-accent-500 font-medium text-ink-900'
                      : 'border-transparent text-ink-400 hover:text-ink-900',
                  )}
                >
                  {link.label}
                </Link>
              )
            })}
          </nav>
        </div>
        <Button variant="outline" size="sm" onClick={handleLogout}>
          Log out
        </Button>
      </div>
    </header>
  )
}
