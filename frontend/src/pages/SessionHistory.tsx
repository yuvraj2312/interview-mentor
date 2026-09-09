import { Link, useNavigate } from 'react-router-dom'

import { AppHeader } from '@/components/AppHeader'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useInterviewSessions } from '@/hooks/useInterviewSessions'
import type { InterviewSessionListItem } from '@/lib/api'

const STATUS_BADGE: Record<string, { label: string; variant: 'good' | 'critical' | 'default' }> = {
  complete: { label: 'Complete', variant: 'good' },
  abandoned: { label: 'Abandoned', variant: 'critical' },
  planned: { label: 'Planned', variant: 'default' },
  in_progress: { label: 'In progress', variant: 'default' },
  evaluating: { label: 'In progress', variant: 'default' },
  advancing: { label: 'In progress', variant: 'default' },
}

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_BADGE[status] ?? { label: status, variant: 'default' as const }
  return <Badge variant={config.variant}>{config.label}</Badge>
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

function formatScore(value: number | null): string {
  return value === null ? '—' : value.toFixed(1)
}

export function SessionHistoryPage() {
  const sessionsQuery = useInterviewSessions()
  const navigate = useNavigate()

  return (
    <div className="min-h-svh bg-slate-50">
      <AppHeader />
      <main className="mx-auto max-w-4xl px-6 py-12 flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Session history</h1>
          <p className="mt-1 text-sm text-slate-500">All of your interview sessions, most recent first.</p>
        </div>

        {sessionsQuery.isLoading && <p className="text-sm text-slate-500">Loading sessions...</p>}

        {sessionsQuery.data && sessionsQuery.data.length === 0 && (
          <Card>
            <CardHeader>
              <CardTitle>No sessions yet</CardTitle>
              <CardDescription>Start your first interview to see it show up here.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="outline" className="w-fit">
                <Link to="/interview-plans/new">Start an interview</Link>
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
                      onClick={() => navigate(`/interview-sessions/${session.session_id}`)}
                    >
                      <TableCell>{formatDate(session.created_at)}</TableCell>
                      <TableCell>
                        <StatusBadge status={session.status} />
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
    </div>
  )
}
