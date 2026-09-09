import { useQuery } from '@tanstack/react-query'

import { getSkillProfile } from '@/lib/api'

export function useSkillProfile() {
  return useQuery({
    queryKey: ['skill-profile'],
    queryFn: getSkillProfile,
  })
}
