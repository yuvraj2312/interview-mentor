import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { useResumeQuery, useUpdateResume } from '@/hooks/useResume'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'

const PROCESSING_LABELS: Record<string, string> = {
  uploaded: 'Queued for processing...',
  parsing: 'Reading your resume...',
  analyzing: 'Extracting skills and experience...',
}

function LowConfidenceBadge({ field, flagged }: { field: string; flagged: string[] }) {
  const isFlagged = flagged.some((f) => f.startsWith(field))
  if (!isFlagged) return null
  return (
    <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
      Please review
    </span>
  )
}

export function ResumeReviewPage() {
  const { resumeId } = useParams<{ resumeId: string }>()
  const { data: resume, isLoading } = useResumeQuery(resumeId)
  const update = useUpdateResume(resumeId!)

  const [skillsText, setSkillsText] = useState('')
  const [experienceJson, setExperienceJson] = useState('[]')
  const [educationJson, setEducationJson] = useState('[]')
  const [projectsJson, setProjectsJson] = useState('[]')

  useEffect(() => {
    if (resume?.structured_data) {
      const data = resume.structured_data as {
        skills?: string[]
        experience?: unknown
        education?: unknown
        projects?: unknown
      }
      setSkillsText((data.skills ?? []).join(', '))
      setExperienceJson(JSON.stringify(data.experience ?? [], null, 2))
      setEducationJson(JSON.stringify(data.education ?? [], null, 2))
      setProjectsJson(JSON.stringify(data.projects ?? [], null, 2))
    }
  }, [resume?.structured_data])

  if (isLoading || !resume) {
    return (
      <div className="min-h-svh bg-slate-50 px-6 py-16 text-center text-sm text-slate-500">Loading...</div>
    )
  }

  if (resume.status !== 'ready') {
    if (resume.status === 'failed') {
      return (
        <div className="min-h-svh bg-slate-50 px-6 py-16 text-center text-sm text-red-600">
          Processing failed: {resume.error_message}
        </div>
      )
    }
    return (
      <div className="min-h-svh bg-slate-50 px-6 py-16 text-center text-sm text-slate-500">
        {PROCESSING_LABELS[resume.status] ?? 'Processing...'}
      </div>
    )
  }

  const flagged = resume.low_confidence_fields ?? []

  async function handleSave() {
    let experience: unknown
    let education: unknown
    let projects: unknown
    try {
      experience = JSON.parse(experienceJson)
      education = JSON.parse(educationJson)
      projects = JSON.parse(projectsJson)
    } catch {
      window.alert('One of the fields is not valid JSON.')
      return
    }

    await update.mutateAsync({
      skills: skillsText
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      experience,
      education,
      projects,
    })
  }

  return (
    <div className="min-h-svh bg-slate-50">
      <main className="mx-auto max-w-2xl px-6 py-16">
        <Card>
          <CardHeader>
            <CardTitle>Review extracted resume data</CardTitle>
            <CardDescription>Fields marked "Please review" were inferred rather than read verbatim.</CardDescription>
            <p className="text-xs text-slate-400">
              Resume ID (use this to compare against a job description): <span className="font-mono">{resume.id}</span>
            </p>
          </CardHeader>
          <CardContent className="flex flex-col gap-6">
            <div>
              <label className="text-sm font-medium text-slate-900">
                Skills
                <LowConfidenceBadge field="skills" flagged={flagged} />
              </label>
              <Input
                className="mt-1"
                value={skillsText}
                onChange={(e) => setSkillsText(e.target.value)}
                placeholder="Python, FastAPI, PostgreSQL"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-slate-900">
                Experience
                <LowConfidenceBadge field="experience" flagged={flagged} />
              </label>
              <Textarea className="mt-1 font-mono" value={experienceJson} onChange={(e) => setExperienceJson(e.target.value)} />
            </div>

            <div>
              <label className="text-sm font-medium text-slate-900">
                Education
                <LowConfidenceBadge field="education" flagged={flagged} />
              </label>
              <Textarea className="mt-1 font-mono" value={educationJson} onChange={(e) => setEducationJson(e.target.value)} />
            </div>

            <div>
              <label className="text-sm font-medium text-slate-900">
                Projects
                <LowConfidenceBadge field="projects" flagged={flagged} />
              </label>
              <Textarea className="mt-1 font-mono" value={projectsJson} onChange={(e) => setProjectsJson(e.target.value)} />
            </div>

            {update.isError && <p className="text-sm text-red-600">Save failed. Please try again.</p>}
            <Button onClick={handleSave} disabled={update.isPending}>
              {update.isPending ? 'Saving...' : 'Save'}
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
