import { Link, useNavigate } from 'react-router-dom'

import { SessionStatusBadge } from '@/components/SessionStatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useInterviewSessions } from '@/hooks/useInterviewSessions'
import { formatDate, formatDateTime, formatRelativeTime } from '@/lib/format'
import type { InterviewSessionListItem } from '@/lib/api'

function formatScore(value: number | null): string {
  return value === null ? '—' : value.toFixed(1)
}

const LIVE_STATUSES = new Set(['in_progress', 'evaluating', 'advancing'])

export function SessionHistoryPage() {
  const sessionsQuery = useInterviewSessions()
  const navigate = useNavigate()

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-12">
      <div>
        <h1 className="text-2xl font-semibold text-ink-900">Session history</h1>
        <p className="mt-1 text-sm text-ink-400">All of your interview sessions, most recent first.</p>
      </div>

      {sessionsQuery.isLoading && (
        <Card>
          <CardContent className="flex flex-col gap-3 pt-6">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      )}

      {sessionsQuery.data && sessionsQuery.data.length === 0 && (
        <Card>
          <CardHeader>
            <CardTitle>No sessions yet</CardTitle>
            <CardDescription>Start your first interview to see it show up here.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" className="w-fit">
              <Link to="/start-interview">Start an interview</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {sessionsQuery.data && sessionsQuery.data.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last activity</TableHead>
                  <TableHead>Questions</TableHead>
                  <TableHead>Technical</TableHead>
                  <TableHead>Communication</TableHead>
                  <TableHead>Completeness</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessionsQuery.data.map((session: InterviewSessionListItem) => (
                  <TableRow
                    key={session.session_id}
                    className="cursor-pointer"
                    onClick={() =>
                      navigate(
                        LIVE_STATUSES.has(session.status)
                          ? `/interview-sessions/${session.session_id}/live`
                          : `/interview-sessions/${session.session_id}`,
                      )
                    }
                  >
                    <TableCell>{formatDate(session.created_at)}</TableCell>
                    <TableCell>
                      <SessionStatusBadge status={session.status} />
                    </TableCell>
                    <TableCell title={formatDateTime(session.last_activity_at)}>
                      {formatRelativeTime(session.last_activity_at)}
                    </TableCell>
                    <TableCell>
                      {session.turns_completed} / {session.total_questions}
                    </TableCell>
                    <TableCell>{formatScore(session.avg_technical_score)}</TableCell>
                    <TableCell>{formatScore(session.avg_communication_score)}</TableCell>
                    <TableCell>{formatScore(session.avg_completeness_score)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </main>
  )
}
