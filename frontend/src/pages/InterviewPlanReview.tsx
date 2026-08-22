import { useParams } from 'react-router-dom'

import { useInterviewPlanQuery } from '@/hooks/useInterviewPlan'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

export function InterviewPlanReviewPage() {
  const { planId } = useParams<{ planId: string }>()
  const { data: plan, isLoading } = useInterviewPlanQuery(planId)

  if (isLoading || !plan) {
    return <div className="min-h-svh bg-slate-50 px-6 py-16 text-center text-sm text-slate-500">Loading...</div>
  }

  if (plan.status === 'failed') {
    return (
      <div className="min-h-svh bg-slate-50 px-6 py-16 text-center text-sm text-red-600">
        Plan generation failed: {plan.error_message}
      </div>
    )
  }

  if (plan.status !== 'ready') {
    return (
      <div className="min-h-svh bg-slate-50 px-6 py-16 text-center text-sm text-slate-500">
        Generating your plan...
      </div>
    )
  }

  return (
    <div className="min-h-svh bg-slate-50">
      <main className="mx-auto max-w-2xl px-6 py-16">
        <Card>
          <CardHeader>
            <CardTitle>Your interview plan</CardTitle>
            <CardDescription>
              {plan.format} format - {plan.question_count} questions
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-6">
            <div className="flex gap-8 text-sm">
              <div>
                <p className="font-medium text-slate-900">Candidate level</p>
                <p className="text-slate-600 capitalize">{plan.candidate_level}</p>
              </div>
              <div>
                <p className="font-medium text-slate-900">Difficulty range</p>
                <p className="text-slate-600">
                  {plan.difficulty_min} - {plan.difficulty_max} (of 5)
                </p>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-slate-900">Topic mix</p>
              <ul className="mt-2 flex flex-col gap-1 text-sm text-slate-600">
                {(plan.topic_mix ?? []).map((entry) => (
                  <li key={entry.topic} className="flex justify-between border-b border-slate-100 py-1">
                    <span>{entry.topic}</span>
                    <span>{entry.question_count} question{entry.question_count === 1 ? '' : 's'}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <p className="text-sm font-medium text-slate-900">Rationale</p>
              <p className="mt-1 text-sm text-slate-600">{plan.rationale}</p>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
