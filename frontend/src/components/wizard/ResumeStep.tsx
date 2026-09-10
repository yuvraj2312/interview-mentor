import { useEffect, useState } from 'react'

import { useResumes } from '@/hooks/useResumes'
import { useResumeQuery, useUpdateResume, useUploadResume } from '@/hooks/useResume'
import { ResourceStatusBadge } from '@/components/ResourceStatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { FileDropzone } from '@/components/ui/file-dropzone'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { isResourceReady } from '@/lib/resourceStatus'
import type { ResumeOut } from '@/lib/api'

const PROCESSING_LABELS: Record<string, string> = {
  uploaded: 'Queued for processing...',
  parsing: 'Reading your resume...',
  analyzing: 'Extracting skills and experience...',
}

function LowConfidenceBadge({ field, flagged }: { field: string; flagged: string[] }) {
  const isFlagged = flagged.some((f) => f.startsWith(field))
  if (!isFlagged) return null
  return (
    <span className="ml-2 rounded-full bg-warning-50 px-2 py-0.5 text-xs font-medium text-warning-700">
      Please review
    </span>
  )
}

interface ResumeStepProps {
  activeId: string | null
  onSelectExisting: (id: string) => void
  onUploaded: (id: string) => void
  onContinue: (resume: ResumeOut) => void
}

export function ResumeStep({ activeId, onSelectExisting, onUploaded, onContinue }: ResumeStepProps) {
  const [mode, setMode] = useState<'choose' | 'upload'>('choose')
  const [pendingFile, setPendingFile] = useState<File | null>(null)

  const resumesQuery = useResumes()
  const activeResumeQuery = useResumeQuery(activeId ?? undefined)
  const upload = useUploadResume()
  const update = useUpdateResume(activeId ?? '')

  const [skillsText, setSkillsText] = useState('')
  const [experienceJson, setExperienceJson] = useState('[]')
  const [educationJson, setEducationJson] = useState('[]')
  const [projectsJson, setProjectsJson] = useState('[]')
  const [isDirty, setIsDirty] = useState(false)

  useEffect(() => {
    const resume = activeResumeQuery.data
    if (resume?.status === 'ready' && resume.structured_data) {
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
      setIsDirty(false)
    }
  }, [activeResumeQuery.data])

  async function handleUpload() {
    if (!pendingFile) return
    const resume = await upload.mutateAsync(pendingFile)
    onUploaded(resume.id)
  }

  async function handleContinue() {
    const resume = activeResumeQuery.data
    if (!resume) return

    if (isDirty) {
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
      const updated = await update.mutateAsync({
        skills: skillsText
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        experience,
        education,
        projects,
      })
      onContinue(updated)
      return
    }

    onContinue(resume)
  }

  const flagged = activeResumeQuery.data?.low_confidence_fields ?? []
  const activeStatus = activeResumeQuery.data?.status
  const activeIsReady = activeStatus ? isResourceReady(activeStatus) : false
  const activeIsFailed = activeStatus === 'failed'

  if (activeId) {
    return (
      <Card>
        <CardContent className="flex flex-col gap-6 pt-6">
          {!activeIsReady && !activeIsFailed && (
            <div className="flex flex-col gap-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-24 w-full" />
              <p className="text-sm text-ink-400">{PROCESSING_LABELS[activeStatus ?? 'uploaded'] ?? 'Processing...'}</p>
            </div>
          )}

          {activeIsReady && activeResumeQuery.data && (
            <>
              <div>
                <Label>
                  Skills
                  <LowConfidenceBadge field="skills" flagged={flagged} />
                </Label>
                <Input
                  className="mt-1"
                  value={skillsText}
                  onChange={(e) => {
                    setSkillsText(e.target.value)
                    setIsDirty(true)
                  }}
                  placeholder="Python, FastAPI, PostgreSQL"
                />
              </div>
              <div>
                <Label>
                  Experience
                  <LowConfidenceBadge field="experience" flagged={flagged} />
                </Label>
                <Textarea
                  className="mt-1 font-mono"
                  value={experienceJson}
                  onChange={(e) => {
                    setExperienceJson(e.target.value)
                    setIsDirty(true)
                  }}
                />
              </div>
              <div>
                <Label>
                  Education
                  <LowConfidenceBadge field="education" flagged={flagged} />
                </Label>
                <Textarea
                  className="mt-1 font-mono"
                  value={educationJson}
                  onChange={(e) => {
                    setEducationJson(e.target.value)
                    setIsDirty(true)
                  }}
                />
              </div>
              <div>
                <Label>
                  Projects
                  <LowConfidenceBadge field="projects" flagged={flagged} />
                </Label>
                <Textarea
                  className="mt-1 font-mono"
                  value={projectsJson}
                  onChange={(e) => {
                    setProjectsJson(e.target.value)
                    setIsDirty(true)
                  }}
                />
              </div>
              {update.isError && <p className="text-sm text-danger-600">Save failed. Please try again.</p>}
              <Button onClick={handleContinue} disabled={update.isPending} className="w-fit">
                {update.isPending ? 'Saving...' : 'Continue'}
              </Button>
            </>
          )}

          {activeResumeQuery.data?.status === 'failed' && (
            <p className="text-sm text-danger-600">
              Processing failed: {activeResumeQuery.data.error_message}
            </p>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent className="flex flex-col gap-6 pt-6">
        {mode === 'choose' && (
          <>
            {resumesQuery.isLoading && (
              <div className="flex flex-col gap-2">
                <Skeleton className="h-14 w-full" />
                <Skeleton className="h-14 w-full" />
              </div>
            )}
            {resumesQuery.data && resumesQuery.data.length > 0 && (
              <div role="radiogroup" aria-label="Existing resumes" className="flex flex-col gap-2">
                {resumesQuery.data.map((resume) => {
                  const ready = isResourceReady(resume.status)
                  return (
                    <button
                      key={resume.id}
                      type="button"
                      role="radio"
                      aria-checked={false}
                      disabled={!ready}
                      onClick={() => onSelectExisting(resume.id)}
                      className={cn(
                        'flex items-center justify-between gap-4 rounded-md border border-border px-4 py-3 text-left transition-colors',
                        ready ? 'cursor-pointer hover:border-accent-500 hover:bg-accent-50' : 'cursor-not-allowed opacity-60',
                      )}
                    >
                      <span className="text-sm font-medium text-ink-900">{resume.original_filename}</span>
                      <ResourceStatusBadge status={resume.status} />
                    </button>
                  )
                })}
              </div>
            )}
            {resumesQuery.data && resumesQuery.data.length === 0 && (
              <p className="text-sm text-ink-400">You don't have any resumes yet.</p>
            )}
            <Button variant="outline" onClick={() => setMode('upload')} className="w-fit">
              Upload a new resume
            </Button>
          </>
        )}

        {mode === 'upload' && (
          <>
            <FileDropzone value={pendingFile} onChange={setPendingFile} accept=".pdf,.docx" hint="PDF or DOCX, up to 10MB" />
            {upload.isError && <p className="text-sm text-danger-600">Upload failed. Please try again.</p>}
            <div className="flex gap-3">
              <Button onClick={handleUpload} disabled={!pendingFile || upload.isPending}>
                {upload.isPending ? 'Uploading...' : 'Upload'}
              </Button>
              {resumesQuery.data && resumesQuery.data.length > 0 && (
                <Button variant="outline" onClick={() => setMode('choose')}>
                  Choose an existing resume instead
                </Button>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
