import { useEffect, useState } from 'react'

import { useResumes } from '@/hooks/useResumes'
import { useResumeQuery, useUpdateResume, useUploadResume } from '@/hooks/useResume'
import { ResourceStatusBadge } from '@/components/ResourceStatusBadge'
import { LowConfidenceBadge } from '@/components/wizard/LowConfidenceBadge'
import { SparseDataBanner } from '@/components/wizard/SparseDataBanner'
import { EducationEditor, ExperienceEditor, ProjectEditor } from '@/components/wizard/entryEditors'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { FileDropzone } from '@/components/ui/file-dropzone'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { isResourceReady } from '@/lib/resourceStatus'
import { getResumeGapMessage } from '@/lib/extractionQuality'
import { ApiError } from '@/lib/api'
import type { ResumeOut } from '@/lib/api'
import type { ResumeEducationEntry, ResumeExperienceEntry, ResumeProjectEntry, ResumeStructuredData } from '@/types/resume'

const PROCESSING_LABELS: Record<string, string> = {
  uploaded: 'Queued for processing...',
  parsing: 'Reading your resume...',
  analyzing: 'Extracting skills and experience...',
}

// Matches the backend's resume_max_upload_bytes (app/core/config.py) and
// the FileDropzone hint below - checked client-side so an oversized file is
// rejected immediately, with no network round-trip.
const MAX_RESUME_UPLOAD_BYTES = 10 * 1024 * 1024

interface ResumeStepProps {
  activeId: string | null
  onSelectExisting: (id: string) => void
  onUploaded: (id: string) => void
  onContinue: (resume: ResumeOut) => void
}

export function ResumeStep({ activeId, onSelectExisting, onUploaded, onContinue }: ResumeStepProps) {
  const [mode, setMode] = useState<'choose' | 'upload'>('choose')
  const [pendingFile, setPendingFile] = useState<File | null>(null)
  const [sizeError, setSizeError] = useState<string | null>(null)

  const resumesQuery = useResumes()
  const activeResumeQuery = useResumeQuery(activeId ?? undefined)
  const upload = useUploadResume()
  const update = useUpdateResume(activeId ?? '')

  const [skillsText, setSkillsText] = useState('')
  const [experience, setExperience] = useState<ResumeExperienceEntry[]>([])
  const [education, setEducation] = useState<ResumeEducationEntry[]>([])
  const [projects, setProjects] = useState<ResumeProjectEntry[]>([])
  const [isDirty, setIsDirty] = useState(false)

  useEffect(() => {
    const resume = activeResumeQuery.data
    if (resume?.status === 'ready' && resume.structured_data) {
      const data = resume.structured_data as {
        skills?: string[]
        experience?: ResumeExperienceEntry[]
        education?: ResumeEducationEntry[]
        projects?: ResumeProjectEntry[]
      }
      setSkillsText((data.skills ?? []).join(', '))
      setExperience(data.experience ?? [])
      setEducation(data.education ?? [])
      setProjects(data.projects ?? [])
      setIsDirty(false)
    }
  }, [activeResumeQuery.data])

  function handleFileChange(file: File | null) {
    if (file && file.size > MAX_RESUME_UPLOAD_BYTES) {
      setSizeError(`File is too large. Please upload a resume under ${MAX_RESUME_UPLOAD_BYTES / (1024 * 1024)}MB.`)
      setPendingFile(null)
      return
    }
    setSizeError(null)
    setPendingFile(file)
  }

  async function handleUpload() {
    if (!pendingFile) return
    try {
      const resume = await upload.mutateAsync(pendingFile)
      onUploaded(resume.id)
    } catch {
      // upload.isError already drives the visible error message below -
      // this catch only prevents an unhandled promise rejection console
      // warning, it doesn't change any user-facing behavior.
    }
  }

  async function handleContinue() {
    const resume = activeResumeQuery.data
    if (!resume) return

    try {
      if (isDirty) {
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
    } catch {
      // update.isError already drives the visible error message below.
    }
  }

  const flagged = activeResumeQuery.data?.low_confidence_fields ?? []
  const activeStatus = activeResumeQuery.data?.status
  const activeIsReady = activeStatus ? isResourceReady(activeStatus) : false
  const activeIsFailed = activeStatus === 'failed'
  const gapMessage = getResumeGapMessage(activeResumeQuery.data?.structured_data as ResumeStructuredData | null)

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
              {gapMessage && <SparseDataBanner message={gapMessage} />}
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
                <div className="mt-1">
                  <ExperienceEditor
                    entries={experience}
                    onChange={(entries) => {
                      setExperience(entries)
                      setIsDirty(true)
                    }}
                  />
                </div>
              </div>
              <div>
                <Label>
                  Education
                  <LowConfidenceBadge field="education" flagged={flagged} />
                </Label>
                <div className="mt-1">
                  <EducationEditor
                    entries={education}
                    onChange={(entries) => {
                      setEducation(entries)
                      setIsDirty(true)
                    }}
                  />
                </div>
              </div>
              <div>
                <Label>
                  Projects
                  <LowConfidenceBadge field="projects" flagged={flagged} />
                </Label>
                <div className="mt-1">
                  <ProjectEditor
                    entries={projects}
                    onChange={(entries) => {
                      setProjects(entries)
                      setIsDirty(true)
                    }}
                  />
                </div>
              </div>
              {update.isError && (
                <p className="text-sm text-danger-600">
                  {update.error instanceof ApiError ? update.error.message : 'Save failed. Please try again.'}
                </p>
              )}
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
            {resumesQuery.isError && (
              <p className="text-sm text-danger-600">Could not load your resumes. Please try again.</p>
            )}
            <Button variant="outline" onClick={() => setMode('upload')} className="w-fit">
              Upload a new resume
            </Button>
          </>
        )}

        {mode === 'upload' && (
          <>
            <FileDropzone value={pendingFile} onChange={handleFileChange} accept=".pdf,.docx" hint="PDF or DOCX, up to 10MB" />
            {sizeError && <p className="text-sm text-danger-600">{sizeError}</p>}
            {upload.isError && (
              <p className="text-sm text-danger-600">
                {upload.error instanceof ApiError ? upload.error.message : 'Upload failed. Please try again.'}
              </p>
            )}
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
