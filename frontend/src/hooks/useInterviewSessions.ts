import { useQuery } from '@tanstack/react-query'

import { listInterviewSessions } from '@/lib/api'

export function useInterviewSessions() {
  return useQuery({
    queryKey: ['interview-sessions'],
    queryFn: listInterviewSessions,
  })
}
