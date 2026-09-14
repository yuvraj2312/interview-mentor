import { useRouteError } from 'react-router-dom'

import { ErrorFallback } from '@/components/ErrorFallback'

// React Router's data-router APIs (createBrowserRouter) catch a route's
// render error internally before it ever reaches a wrapping React
// ErrorBoundary (see components/ErrorBoundary.tsx's own doc comment) -
// showing its own raw, unstyled dev overlay instead unless a route in the
// tree supplies errorElement. Attaching this to the shared root route in
// routes/index.tsx means every route below inherits it, so any route's
// render crash gets the same graceful fallback instead of that raw overlay.
export function RouteErrorBoundary() {
  const error = useRouteError()
  console.error('Unhandled route error:', error)
  return <ErrorFallback />
}
