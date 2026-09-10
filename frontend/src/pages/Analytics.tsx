import { Link } from 'react-router-dom'

import { TrendBadge } from '@/components/TrendBadge'
import { ProgressChart } from '@/components/charts/ProgressChart'
import { SkillBreakdownChart } from '@/components/charts/SkillBreakdownChart'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useInterviewSessions } from '@/hooks/useInterviewSessions'
import { useSkillProfile } from '@/hooks/useSkillProfile'
import { ApiError } from '@/lib/api'

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <Button asChild variant="outline" className="w-fit">
          <Link to="/start-interview">Start an interview</Link>
        </Button>
      </CardContent>
    </Card>
  )
}

export function AnalyticsPage() {
  const skillProfileQuery = useSkillProfile()
  const sessionsQuery = useInterviewSessions()

  const skillProfileMissing = skillProfileQuery.error instanceof ApiError && skillProfileQuery.error.status === 404

  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-12">
      <div>
        <h1 className="text-2xl font-semibold text-ink-900">Analytics</h1>
        <p className="mt-1 text-sm text-ink-400">Your skill breakdown and progress across interview sessions.</p>
      </div>

      {skillProfileQuery.isLoading && (
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-48 w-full" />
          </CardContent>
        </Card>
      )}

      {skillProfileMissing && (
        <EmptyState
          title="No skill profile yet"
          description="Complete an interview session to see your skill breakdown."
        />
      )}

      {skillProfileQuery.data && (
        <Card>
          <CardHeader>
            <CardTitle>Skill breakdown</CardTitle>
            <CardDescription>
              Average scores per topic across {skillProfileQuery.data.sessions_completed} completed session
              {skillProfileQuery.data.sessions_completed === 1 ? '' : 's'}.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-6">
            {skillProfileQuery.data.topics.length === 0 ? (
              <p className="text-sm text-ink-400">No topic data yet.</p>
            ) : (
              <>
                <SkillBreakdownChart topics={skillProfileQuery.data.topics} />
                <div className="flex flex-col divide-y divide-border border-t border-border">
                  {skillProfileQuery.data.topics.map((topic) => (
                    <div key={topic.topic} className="flex items-center justify-between py-3 text-sm">
                      <div>
                        <p className="font-medium text-ink-900">{topic.topic}</p>
                        <p className="text-xs text-ink-400">
                          {topic.sessions_count} session{topic.sessions_count === 1 ? '' : 's'}
                        </p>
                      </div>
                      <TrendBadge trend={topic.trend} />
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {sessionsQuery.isLoading && (
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-48 w-full" />
          </CardContent>
        </Card>
      )}

      {sessionsQuery.data && (
        <Card>
          <CardHeader>
            <CardTitle>Progress over time</CardTitle>
            <CardDescription>Average scores per completed session, in order.</CardDescription>
          </CardHeader>
          <CardContent>
            {sessionsQuery.data.filter((s) => s.status === 'complete' && s.avg_technical_score !== null).length ===
            0 ? (
              <p className="text-sm text-ink-400">Complete a full interview session to see your trend here.</p>
            ) : (
              <ProgressChart sessions={sessionsQuery.data} />
            )}
          </CardContent>
        </Card>
      )}
    </main>
  )
}
