import { useMutation, useQuery } from '@tanstack/react-query'

import { computeSkillGap, getSkillGap } from '@/lib/api'

export function useComputeSkillGap() {
  return useMutation({
    mutationFn: ({ resumeId, jobDescriptionId }: { resumeId: string; jobDescriptionId: string }) =>
      computeSkillGap(resumeId, jobDescriptionId),
  })
}

export function useSkillGapQuery(id: string | undefined) {
  return useQuery({
    queryKey: ['skill-gap', id],
    queryFn: () => getSkillGap(id!),
    enabled: Boolean(id),
  })
}
