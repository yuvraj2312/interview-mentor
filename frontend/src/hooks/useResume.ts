import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { deleteResume, getResume, updateResume, uploadResume } from '@/lib/api'

const PROCESSING_STATUSES = new Set(['uploaded', 'parsing', 'analyzing'])

export function useUploadResume() {
  return useMutation({
    mutationFn: (file: File) => uploadResume(file),
  })
}

export function useResumeQuery(id: string | undefined) {
  return useQuery({
    queryKey: ['resume', id],
    queryFn: () => getResume(id!),
    enabled: Boolean(id),
    refetchInterval: (query) => (query.state.data && PROCESSING_STATUSES.has(query.state.data.status) ? 2000 : false),
  })
}

export function useUpdateResume(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (structuredData: Record<string, unknown>) => updateResume(id, structuredData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resume', id] })
    },
  })
}

export function useDeleteResume() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => deleteResume(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['resumes'] })
    },
  })
}
