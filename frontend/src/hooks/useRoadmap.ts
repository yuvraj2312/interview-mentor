import { useQuery } from '@tanstack/react-query'

import { getRoadmap } from '@/lib/api'

export function useRoadmap() {
  return useQuery({
    queryKey: ['roadmap'],
    queryFn: getRoadmap,
  })
}
