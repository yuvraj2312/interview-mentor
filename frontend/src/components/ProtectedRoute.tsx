import { Navigate, Outlet } from 'react-router-dom'

import { useAuthStore } from '@/store/authStore'

export function ProtectedRoute() {
  const accessToken = useAuthStore((state) => state.accessToken)
  const isBootstrapping = useAuthStore((state) => state.isBootstrapping)

  if (isBootstrapping) {
    return (
      <div className="flex min-h-svh items-center justify-center text-sm text-slate-500">Loading…</div>
    )
  }

  if (!accessToken) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
