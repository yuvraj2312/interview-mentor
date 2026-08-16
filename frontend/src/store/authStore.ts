import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthTokens {
  accessToken: string
  refreshToken: string
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  isBootstrapping: boolean
  setTokens: (tokens: AuthTokens) => void
  clearTokens: () => void
  setBootstrapping: (value: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      isBootstrapping: true,
      setTokens: ({ accessToken, refreshToken }) => set({ accessToken, refreshToken }),
      clearTokens: () => set({ accessToken: null, refreshToken: null }),
      setBootstrapping: (value) => set({ isBootstrapping: value }),
    }),
    {
      name: 'interview-mentor-auth',
      // Only the refresh token is persisted. The access token is short-lived
      // and kept in memory only; it is re-derived on boot via /auth/refresh.
      partialize: (state) => ({ refreshToken: state.refreshToken }),
    },
  ),
)
