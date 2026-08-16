import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'

import './index.css'
import App from './App.tsx'
import { queryClient } from '@/lib/queryClient'
import { bootstrapSession } from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

bootstrapSession().finally(() => {
  useAuthStore.getState().setBootstrapping(false)
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
