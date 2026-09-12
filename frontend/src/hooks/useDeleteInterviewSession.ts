import { useMutation, useQueryClient } from '@tanstack/react-query'

import { deleteInterviewSession } from '@/lib/api'

export function useDeleteInterviewSession() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteInterviewSession(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interview-sessions'] })
    },
  })
}
