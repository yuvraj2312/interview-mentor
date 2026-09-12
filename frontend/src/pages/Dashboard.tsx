import { useState } from 'react'
import { BarChart3, Eye, ListChecks, Map, Plus, Rocket, Trash2 } from 'lucide-react'
import { Link } from 'react-router-dom'

import { ResourceStatusBadge } from '@/components/ResourceStatusBadge'
import { SessionStatusBadge } from '@/components/SessionStatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { JobDescriptionStep } from '@/components/wizard/JobDescriptionStep'
import { ResumeStep } from '@/components/wizard/ResumeStep'
import { useDeleteInterviewSession } from '@/hooks/useDeleteInterviewSession'
import { useInterviewSessions } from '@/hooks/useInterviewSessions'
import { useJobDescriptions } from '@/hooks/useJobDescriptions'
import { useDeleteJobDescription } from '@/hooks/useJobDescription'
import { useResumes } from '@/hooks/useResumes'
import { useDeleteResume } from '@/hooks/useResume'
import { formatDate } from '@/lib/format'

const RECENT_LIMIT = 5
const LIVE_STATUSES = new Set(['in_progress', 'evaluating', 'advancing'])

const SECONDARY_LINKS = [
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/sessions', icon: ListChecks, label: 'Sessions' },
  { to: '/roadmap', icon: Map, label: 'Roadmap' },
]

export function DashboardPage() {
  const resumesQuery = useResumes()
  const jdsQuery = useJobDescriptions()
  const sessionsQuery = useInterviewSessions()
  const deleteResume = useDeleteResume()
  const deleteJobDescription = useDeleteJobDescription()
  const deleteSession = useDeleteInterviewSession()

  const [resumeModalOpen, setResumeModalOpen] = useState(false)
  const [resumeModalActiveId, setResumeModalActiveId] = useState<string | null>(null)
  const [jdModalOpen, setJdModalOpen] = useState(false)
  const [jdModalActiveId, setJdModalActiveId] = useState<string | null>(null)

  function handleDeleteResume(id: string, filename: string) {
    if (window.confirm(`Delete "${filename}"? Existing plans and sessions built from it will be unaffected.`)) {
      deleteResume.mutate(id)
    }
  }

  function handleDeleteJobDescription(id: string) {
    if (window.confirm('Delete this job description? Existing plans and sessions built from it will be unaffected.')) {
      deleteJobDescription.mutate(id)
    }
  }

  function handleDeleteSession(id: string) {
    if (window.confirm('Delete this interview session? Its roadmap and evaluations will be unaffected.')) {
      deleteSession.mutate(id)
    }
  }

  function closeResumeModal() {
    setResumeModalOpen(false)
    setResumeModalActiveId(null)
  }

  function closeJdModal() {
    setJdModalOpen(false)
    setJdModalActiveId(null)
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-16">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-ink-900">Welcome</h1>
        <p className="mt-2 text-sm text-ink-400">Start a new interview, or catch up on your progress.</p>
        <Button asChild size="lg" className="mt-8">
          <Link to="/start-interview">
            <Rocket className="size-4" />
            Start New Interview
          </Link>
        </Button>
      </div>

      <div className="mt-16 grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
            <CardTitle className="text-base">Recent resumes</CardTitle>
            <Button variant="outline" size="sm" onClick={() => setResumeModalOpen(true)}>
              <Plus className="size-4" />
              Upload
            </Button>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {resumesQuery.isLoading && (
              <>
                <Skeleton className="h-9 w-full" />
                <Skeleton className="h-9 w-full" />
              </>
            )}
            {resumesQuery.data && resumesQuery.data.length === 0 && (
              <p className="text-sm text-ink-400">No resumes yet.</p>
            )}
            {resumesQuery.data?.slice(0, RECENT_LIMIT).map((resume) => (
              <div key={resume.id} className="flex items-center justify-between gap-2 py-1">
                <div className="min-w-0">
                  <p className="truncate text-sm text-ink-900">{resume.original_filename}</p>
                  <p className="text-xs text-ink-400">{formatDate(resume.created_at)}</p>
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  <ResourceStatusBadge status={resume.status} />
                  <Button asChild variant="ghost" size="sm" className="size-8 p-0">
                    <Link to={`/resumes/${resume.id}`} aria-label="View resume">
                      <Eye className="size-4" />
                    </Link>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="size-8 p-0"
                    aria-label="Delete resume"
                    onClick={() => handleDeleteResume(resume.id, resume.original_filename)}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0">
            <CardTitle className="text-base">Recent job descriptions</CardTitle>
            <Button variant="outline" size="sm" onClick={() => setJdModalOpen(true)}>
              <Plus className="size-4" />
              Add
            </Button>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {jdsQuery.isLoading && (
              <>
                <Skeleton className="h-9 w-full" />
                <Skeleton className="h-9 w-full" />
              </>
            )}
            {jdsQuery.data && jdsQuery.data.length === 0 && (
              <p className="text-sm text-ink-400">No job descriptions yet.</p>
            )}
            {jdsQuery.data?.slice(0, RECENT_LIMIT).map((jd) => (
              <div key={jd.id} className="flex items-center justify-between gap-2 py-1">
                <div className="min-w-0">
                  <p className="truncate text-sm text-ink-900">{jd.raw_text_preview}</p>
                  <p className="text-xs text-ink-400">{formatDate(jd.created_at)}</p>
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  <ResourceStatusBadge status={jd.status} />
                  <Button asChild variant="ghost" size="sm" className="size-8 p-0">
                    <Link to={`/job-descriptions/${jd.id}`} aria-label="View job description">
                      <Eye className="size-4" />
                    </Link>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="size-8 p-0"
                    aria-label="Delete job description"
                    onClick={() => handleDeleteJobDescription(jd.id)}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent sessions</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {sessionsQuery.isLoading && (
              <>
                <Skeleton className="h-9 w-full" />
                <Skeleton className="h-9 w-full" />
              </>
            )}
            {sessionsQuery.data && sessionsQuery.data.length === 0 && (
              <p className="text-sm text-ink-400">No sessions yet.</p>
            )}
            {sessionsQuery.data?.slice(0, RECENT_LIMIT).map((session) => (
              <div key={session.session_id} className="flex items-center justify-between gap-2 py-1">
                <p className="text-sm text-ink-900">{formatDate(session.created_at)}</p>
                <div className="flex shrink-0 items-center gap-1">
                  <SessionStatusBadge status={session.status} />
                  <Button asChild variant="ghost" size="sm" className="size-8 p-0">
                    <Link
                      to={
                        LIVE_STATUSES.has(session.status)
                          ? `/interview-sessions/${session.session_id}/live`
                          : `/interview-sessions/${session.session_id}`
                      }
                      aria-label="View session"
                    >
                      <Eye className="size-4" />
                    </Link>
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="size-8 p-0"
                    aria-label="Delete session"
                    onClick={() => handleDeleteSession(session.session_id)}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </div>
              </div>
            ))}
            {sessionsQuery.data && sessionsQuery.data.length > 0 && (
              <Link to="/sessions" className="mt-1 text-xs font-medium text-accent-600 hover:text-accent-500">
                View all
              </Link>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="mt-10 flex items-center justify-center gap-2 border-t border-border pt-6">
        {SECONDARY_LINKS.map(({ to, icon: Icon, label }) => (
          <Button key={to} asChild variant="ghost" size="sm">
            <Link to={to}>
              <Icon className="size-4" />
              {label}
            </Link>
          </Button>
        ))}
      </div>

      <Dialog open={resumeModalOpen} onOpenChange={(open) => (open ? setResumeModalOpen(true) : closeResumeModal())}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Upload a resume</DialogTitle>
          </DialogHeader>
          <ResumeStep
            activeId={resumeModalActiveId}
            onSelectExisting={setResumeModalActiveId}
            onUploaded={setResumeModalActiveId}
            onContinue={closeResumeModal}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={jdModalOpen} onOpenChange={(open) => (open ? setJdModalOpen(true) : closeJdModal())}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add a job description</DialogTitle>
          </DialogHeader>
          <JobDescriptionStep
            activeId={jdModalActiveId}
            onSelectExisting={setJdModalActiveId}
            onCreated={setJdModalActiveId}
            onContinue={closeJdModal}
          />
        </DialogContent>
      </Dialog>
    </main>
  )
}
