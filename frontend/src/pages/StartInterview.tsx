import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { FormatStep } from '@/components/wizard/FormatStep'
import { JobDescriptionStep } from '@/components/wizard/JobDescriptionStep'
import { ReadyStep } from '@/components/wizard/ReadyStep'
import { ResumeStep } from '@/components/wizard/ResumeStep'
import { SkillGapStep } from '@/components/wizard/SkillGapStep'
import { StepIndicator } from '@/components/wizard/StepIndicator'
import { Button } from '@/components/ui/button'
import { useComputeSkillGap } from '@/hooks/useSkillGap'
import { useGenerateInterviewPlan } from '@/hooks/useInterviewPlan'
import { useStartInterviewSession } from '@/hooks/useInterviewSession'
import type { InterviewPlanFormat, InterviewPlanOut, JobDescriptionOut, ResumeOut } from '@/lib/api'

const STEPS = [
  { label: 'Resume' },
  { label: 'Job description' },
  { label: 'Skill gap' },
  { label: 'Format' },
  { label: 'Ready' },
]

export function StartInterviewPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1)

  const [activeResumeId, setActiveResumeId] = useState<string | null>(null)
  const [resume, setResume] = useState<ResumeOut | null>(null)

  const [activeJdId, setActiveJdId] = useState<string | null>(null)
  const [jd, setJd] = useState<JobDescriptionOut | null>(null)

  const [format, setFormat] = useState<InterviewPlanFormat>('standard')
  const [plan, setPlan] = useState<InterviewPlanOut | null>(null)

  const skillGap = useComputeSkillGap()
  const generatePlan = useGenerateInterviewPlan()
  const startSession = useStartInterviewSession()

  const skillGapKeyRef = useRef<string | null>(null)
  useEffect(() => {
    if (resume?.status === 'ready' && jd?.status === 'ready') {
      const key = `${resume.id}:${jd.id}`
      if (skillGapKeyRef.current !== key) {
        skillGapKeyRef.current = key
        skillGap.mutate({ resumeId: resume.id, jobDescriptionId: jd.id })
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resume?.id, resume?.status, jd?.id, jd?.status])

  async function handleGeneratePlan() {
    if (!skillGap.data) return
    const generated = await generatePlan.mutateAsync({ skillGapAnalysisId: skillGap.data.id, format })
    setPlan(generated)
    setStep(5)
  }

  async function handleStart() {
    if (!plan) return
    const result = await startSession.mutateAsync(plan.id)
    navigate(`/interview-sessions/${result.session_id}/live`)
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-ink-900">Start a new interview</h1>
        <p className="mt-1 text-sm text-ink-400">A few quick steps to build your tailored interview plan.</p>
      </div>

      <div className="mb-8">
        <StepIndicator steps={STEPS} currentStep={step} />
      </div>

      {step === 1 && (
        <ResumeStep
          activeId={activeResumeId}
          onSelectExisting={(id) => setActiveResumeId(id)}
          onUploaded={(id) => setActiveResumeId(id)}
          onContinue={(r) => {
            setResume(r)
            setStep(2)
          }}
        />
      )}

      {step === 2 && (
        <JobDescriptionStep
          activeId={activeJdId}
          onSelectExisting={(id) => setActiveJdId(id)}
          onCreated={(id) => setActiveJdId(id)}
          onContinue={(j) => {
            setJd(j)
            setStep(3)
          }}
        />
      )}

      {step === 3 && <SkillGapStep isPending={skillGap.isPending} isError={skillGap.isError} data={skillGap.data} />}

      {step === 4 && (
        <FormatStep
          format={format}
          onFormatChange={setFormat}
          onGenerate={handleGeneratePlan}
          isGenerating={generatePlan.isPending}
          isError={generatePlan.isError}
        />
      )}

      {step === 5 && plan && (
        <ReadyStep plan={plan} onStart={handleStart} isStarting={startSession.isPending} isError={startSession.isError} />
      )}

      <div className="mt-6 flex items-center justify-between">
        <Button variant="outline" onClick={() => setStep((s) => Math.max(1, s - 1))} disabled={step === 1}>
          Back
        </Button>
        {step === 3 && (
          <Button onClick={() => setStep(4)} disabled={!skillGap.data}>
            Next
          </Button>
        )}
      </div>
    </main>
  )
}
