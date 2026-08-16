import { useNavigate } from 'react-router-dom'

import { logout as logoutRequest } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'
import { Button } from '@/components/ui/button'

export function DashboardPage() {
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
    <div className="min-h-svh bg-slate-50">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
        <span className="text-lg font-semibold text-slate-900">Interview Mentor</span>
        <Button variant="outline" size="sm" onClick={handleLogout}>
          Log out
        </Button>
      </header>
      <main className="mx-auto max-w-3xl px-6 py-16 text-center">
        <h1 className="text-2xl font-semibold text-slate-900">Welcome</h1>
        <p className="mt-2 text-sm text-slate-500">
          Your interview sessions and progress will show up here in a later phase.
        </p>
      </main>
    </div>
  )
}
