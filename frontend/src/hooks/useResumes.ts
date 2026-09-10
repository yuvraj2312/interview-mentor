import { useQuery } from '@tanstack/react-query'

import { listResumes } from '@/lib/api'

export function useResumes() {
  return useQuery({
    queryKey: ['resumes'],
    queryFn: listResumes,
  })
}
