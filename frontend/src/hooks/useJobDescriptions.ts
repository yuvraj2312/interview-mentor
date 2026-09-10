import { useQuery } from '@tanstack/react-query'

import { listJobDescriptions } from '@/lib/api'

export function useJobDescriptions() {
  return useQuery({
    queryKey: ['job-descriptions'],
    queryFn: listJobDescriptions,
  })
}
