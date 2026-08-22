import { useMutation, useQuery } from '@tanstack/react-query'

import { generateInterviewPlan, getInterviewPlan, type InterviewPlanFormat } from '@/lib/api'

export function useGenerateInterviewPlan() {
  return useMutation({
    mutationFn: ({ skillGapAnalysisId, format }: { skillGapAnalysisId: string; format: InterviewPlanFormat }) =>
      generateInterviewPlan(skillGapAnalysisId, format),
  })
}

export function useInterviewPlanQuery(id: string | undefined) {
  return useQuery({
    queryKey: ['interview-plan', id],
    queryFn: () => getInterviewPlan(id!),
    enabled: Boolean(id),
  })
}
