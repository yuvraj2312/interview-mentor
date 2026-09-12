import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

interface InterviewPreferencesState {
  ttsEnabled: boolean
  sttEnabled: boolean
  hasSeenCameraNotice: boolean
  // Session ids that have already been through the pre-session camera/mic
  // check screen. The check screen is a one-time gate before a session
  // starts - once passed, it must never re-trigger for that session again
  // (e.g. via the browser back button after leaving a live session).
  checkedSessionIds: string[]
  setTtsEnabled: (value: boolean) => void
  setSttEnabled: (value: boolean) => void
  markCameraNoticeSeen: () => void
  markSessionChecked: (sessionId: string) => void
  hasCheckedSession: (sessionId: string) => boolean
}

export const useInterviewPreferencesStore = create<InterviewPreferencesState>()(
  persist(
    (set, get) => ({
      ttsEnabled: true,
      sttEnabled: true,
      hasSeenCameraNotice: false,
      checkedSessionIds: [],
      setTtsEnabled: (value) => set({ ttsEnabled: value }),
      setSttEnabled: (value) => set({ sttEnabled: value }),
      markCameraNoticeSeen: () => set({ hasSeenCameraNotice: true }),
      markSessionChecked: (sessionId) =>
        set((s) => (s.checkedSessionIds.includes(sessionId) ? s : { checkedSessionIds: [...s.checkedSessionIds, sessionId] })),
      hasCheckedSession: (sessionId) => get().checkedSessionIds.includes(sessionId),
    }),
    {
      name: 'interview-mentor-voice-prefs',
      // sessionStorage, not localStorage: these are session-scoped preferences,
      // not account-wide settings - they should reset for a brand-new session.
      storage: createJSONStorage(() => sessionStorage),
    },
  ),
)
