import { Link, useNavigate } from 'react-router-dom'

import { logout as logoutRequest } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'

const NAV_LINKS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/analytics', label: 'Analytics' },
  { to: '/sessions', label: 'Sessions' },
  { to: '/roadmap', label: 'Roadmap' },
]

export function AppHeader() {
  const navigate = useNavigate()
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
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
      <div className="flex items-center gap-8">
        <span className="text-lg font-semibold text-slate-900">Interview Mentor</span>
        <nav className="flex items-center gap-4">
          {NAV_LINKS.map((link) => (
            <Link key={link.to} to={link.to} className="text-sm text-slate-600 hover:text-slate-900">
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
      <Button variant="outline" size="sm" onClick={handleLogout}>
        Log out
      </Button>
    </header>
  )
}
