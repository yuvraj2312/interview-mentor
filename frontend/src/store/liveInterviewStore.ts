import { create } from 'zustand'

// Ephemeral, unlike authStore/interviewPreferencesStore - deliberately not
// persisted. Lets code outside LiveInterview.tsx (the idle-timeout hook)
// know whether a live interview is in progress, without lifting the whole
// session-socket state out of that page.
interface LiveInterviewState {
  isLive: boolean
  setIsLive: (isLive: boolean) => void
}

export const useLiveInterviewStore = create<LiveInterviewState>((set) => ({
  isLive: false,
  setIsLive: (isLive) => set({ isLive }),
}))
