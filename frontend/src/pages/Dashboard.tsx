import { BarChart3, ListChecks, Map, Rocket } from 'lucide-react'
import { Link } from 'react-router-dom'

import { ResourceStatusBadge } from '@/components/ResourceStatusBadge'
import { SessionStatusBadge } from '@/components/SessionStatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useInterviewSessions } from '@/hooks/useInterviewSessions'
import { useJobDescriptions } from '@/hooks/useJobDescriptions'
import { useResumes } from '@/hooks/useResumes'
import { formatDate } from '@/lib/format'

const RECENT_LIMIT = 5

const SECONDARY_LINKS = [
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/sessions', icon: ListChecks, label: 'Sessions' },
  { to: '/roadmap', icon: Map, label: 'Roadmap' },
]

export function DashboardPage() {
  const resumesQuery = useResumes()
  const jdsQuery = useJobDescriptions()
  const sessionsQuery = useInterviewSessions()

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
          <CardHeader>
            <CardTitle className="text-base">Recent resumes</CardTitle>
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
                <ResourceStatusBadge status={resume.status} />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent job descriptions</CardTitle>
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
                <ResourceStatusBadge status={jd.status} />
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
                <SessionStatusBadge status={session.status} />
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
    </main>
  )
}
