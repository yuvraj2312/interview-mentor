import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createJobDescription, deleteJobDescription, getJobDescription, updateJobDescription } from '@/lib/api'

export function useCreateJobDescription() {
  return useMutation({
    mutationFn: (rawText: string) => createJobDescription(rawText),
  })
}

export function useJobDescriptionQuery(id: string | undefined) {
  return useQuery({
    queryKey: ['job-description', id],
    queryFn: () => getJobDescription(id!),
    enabled: Boolean(id),
  })
}

export function useUpdateJobDescription(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (structuredData: Record<string, unknown>) => updateJobDescription(id, structuredData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-description', id] })
    },
  })
}

export function useDeleteJobDescription() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteJobDescription(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-descriptions'] })
    },
  })
}
