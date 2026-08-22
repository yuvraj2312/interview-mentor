import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { useGenerateInterviewPlan } from '@/hooks/useInterviewPlan'
import type { InterviewPlanFormat } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'

const FORMAT_OPTIONS: { value: InterviewPlanFormat; label: string; description: string }[] = [
  { value: 'quick', label: 'Quick', description: '5 questions - a fast gut-check' },
  { value: 'standard', label: 'Standard', description: '8 questions - a typical full session' },
  { value: 'thorough', label: 'Thorough', description: '12 questions - deep coverage of the role' },
]

export function InterviewPlanCreatePage() {
  const [searchParams] = useSearchParams()
  const skillGapId = searchParams.get('skillGapId') ?? ''
  const navigate = useNavigate()
  const generate = useGenerateInterviewPlan()

  const [format, setFormat] = useState<InterviewPlanFormat>('standard')

  if (!skillGapId) {
    return (
      <div className="min-h-svh bg-slate-50 px-6 py-16 text-center text-sm text-red-600">
        Missing skill gap reference. Go back to your job description review page and compare against a resume first.
      </div>
    )
  }

  async function handleGenerate() {
    const plan = await generate.mutateAsync({ skillGapAnalysisId: skillGapId, format })
    navigate(`/interview-plans/${plan.id}/review`)
  }

  return (
    <div className="min-h-svh bg-slate-50">
      <main className="mx-auto max-w-2xl px-6 py-16">
        <Card>
          <CardHeader>
            <CardTitle>Choose an interview format</CardTitle>
            <CardDescription>This sets how many questions your plan will cover.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-col gap-3">
              {FORMAT_OPTIONS.map((option) => (
                <label
                  key={option.value}
                  className={`flex cursor-pointer flex-col rounded-md border px-4 py-3 ${
                    format === option.value ? 'border-slate-900 bg-slate-100' : 'border-slate-200'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="format"
                      value={option.value}
                      checked={format === option.value}
                      onChange={() => setFormat(option.value)}
                    />
                    <span className="text-sm font-medium text-slate-900">{option.label}</span>
                  </span>
                  <span className="ml-6 text-xs text-slate-500">{option.description}</span>
                </label>
              ))}
            </div>

            {generate.isError && <p className="text-sm text-red-600">Plan generation failed. Please try again.</p>}

            <Button onClick={handleGenerate} disabled={generate.isPending}>
              {generate.isPending ? 'Generating plan...' : 'Generate plan'}
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
