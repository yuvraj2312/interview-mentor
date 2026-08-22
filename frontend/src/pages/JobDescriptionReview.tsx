import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useJobDescriptionQuery, useUpdateJobDescription } from '@/hooks/useJobDescription'
import { useComputeSkillGap } from '@/hooks/useSkillGap'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

function LowConfidenceBadge({ field, flagged }: { field: string; flagged: string[] }) {
  const isFlagged = flagged.some((f) => f.startsWith(field))
  if (!isFlagged) return null
  return (
    <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
      Please review
    </span>
  )
}

export function JobDescriptionReviewPage() {
  const { jdId } = useParams<{ jdId: string }>()
  const { data: jd, isLoading } = useJobDescriptionQuery(jdId)
  const update = useUpdateJobDescription(jdId!)
  const computeGap = useComputeSkillGap()

  const [requiredText, setRequiredText] = useState('')
  const [preferredText, setPreferredText] = useState('')
  const [seniority, setSeniority] = useState('')
  const [resumeId, setResumeId] = useState('')

  useEffect(() => {
    if (jd?.structured_data) {
      const data = jd.structured_data as {
        required_skills?: string[]
        preferred_skills?: string[]
        seniority_level?: string
      }
      setRequiredText((data.required_skills ?? []).join(', '))
      setPreferredText((data.preferred_skills ?? []).join(', '))
      setSeniority(data.seniority_level ?? '')
    }
  }, [jd?.structured_data])

  if (isLoading || !jd) {
    return <div className="min-h-svh bg-slate-50 px-6 py-16 text-center text-sm text-slate-500">Loading...</div>
  }

  const flagged = jd.low_confidence_fields ?? []

  async function handleSave() {
    await update.mutateAsync({
      required_skills: requiredText
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      preferred_skills: preferredText
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      seniority_level: seniority,
    })
  }

  return (
    <div className="min-h-svh bg-slate-50">
      <main className="mx-auto max-w-2xl px-6 py-16 flex flex-col gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Review job requirements</CardTitle>
            <CardDescription>Fields marked "Please review" were inferred rather than read verbatim.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-6">
            <div>
              <label className="text-sm font-medium text-slate-900">
                Required skills
                <LowConfidenceBadge field="required_skills" flagged={flagged} />
              </label>
              <Input className="mt-1" value={requiredText} onChange={(e) => setRequiredText(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-900">
                Preferred skills
                <LowConfidenceBadge field="preferred_skills" flagged={flagged} />
              </label>
              <Input className="mt-1" value={preferredText} onChange={(e) => setPreferredText(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-900">
                Seniority level
                <LowConfidenceBadge field="seniority_level" flagged={flagged} />
              </label>
              <Input className="mt-1" value={seniority} onChange={(e) => setSeniority(e.target.value)} />
            </div>
            {update.isError && <p className="text-sm text-red-600">Save failed. Please try again.</p>}
            <Button onClick={handleSave} disabled={update.isPending}>
              {update.isPending ? 'Saving...' : 'Save'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Compare against a resume</CardTitle>
            <CardDescription>Paste a resume ID (shown on its review page) to compute the skill gap.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Input
              value={resumeId}
              onChange={(e) => setResumeId(e.target.value)}
              placeholder="Resume ID"
            />
            <Button
              variant="outline"
              disabled={!resumeId.trim() || computeGap.isPending}
              onClick={() => computeGap.mutate({ resumeId, jobDescriptionId: jd.id })}
            >
              {computeGap.isPending ? 'Comparing...' : 'Compare'}
            </Button>

            {computeGap.isError && <p className="text-sm text-red-600">Comparison failed. Check the resume ID and try again.</p>}

            {computeGap.data && (
              <div className="flex flex-col gap-2 text-sm">
                <p className="font-medium text-slate-900">
                  Match score: {Math.round(computeGap.data.match_score * 100)}%
                </p>
                <p>
                  <span className="font-medium text-emerald-700">Matched: </span>
                  {computeGap.data.matched_skills.join(', ') || 'None'}
                </p>
                <p>
                  <span className="font-medium text-red-700">Missing required: </span>
                  {computeGap.data.missing_required_skills.join(', ') || 'None'}
                </p>
                <p>
                  <span className="font-medium text-amber-700">Missing preferred: </span>
                  {computeGap.data.missing_preferred_skills.join(', ') || 'None'}
                </p>
                <Button asChild className="mt-2 w-fit">
                  <Link to={`/interview-plans/new?skillGapId=${computeGap.data.id}`}>Continue to interview plan</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
