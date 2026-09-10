import { Outlet } from 'react-router-dom'

import { AppHeader } from '@/components/AppHeader'

export function AppLayout() {
  return (
    <div className="min-h-svh bg-surface-muted">
      <AppHeader />
      <Outlet />
    </div>
  )
}
