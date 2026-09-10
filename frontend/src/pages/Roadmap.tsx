import { CheckCircle2 } from 'lucide-react'
import { Link } from 'react-router-dom'

import { PriorityBadge } from '@/components/PriorityBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { useRoadmap } from '@/hooks/useRoadmap'
import { ApiError, type RoadmapItemOut, type RoadmapPriority } from '@/lib/api'

const PRIORITY_SECTIONS: {
  priority: RoadmapPriority
  label: string
  dotClass: string
  borderClass: string
}[] = [
  { priority: 'high', label: 'High priority', dotClass: 'bg-danger-600', borderClass: 'border-l-danger-600' },
  { priority: 'medium', label: 'Medium priority', dotClass: 'bg-warning-600', borderClass: 'border-l-warning-600' },
  { priority: 'low', label: 'Low priority', dotClass: 'bg-success-600', borderClass: 'border-l-success-600' },
]

function RoadmapItemCard({ item, borderClass }: { item: RoadmapItemOut; borderClass: string }) {
  return (
    <Card className={cn('border-l-4', borderClass)}>
      <CardHeader>
        <div className="flex items-center justify-between gap-4">
          <CardTitle className="text-base">{item.topic}</CardTitle>
          <PriorityBadge priority={item.priority} />
        </div>
        <CardDescription>{item.gap_description}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="text-sm text-ink-700">{item.recommended_action}</p>
        {item.resources.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-xs font-medium text-ink-400">Resources</p>
            <div className="flex flex-col gap-1.5">
              {item.resources.map((resource) => (
                <div key={resource.resource_id} className="flex items-center gap-2 text-sm">
                  {resource.url ? (
                    <a
                      href={resource.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent-600 underline underline-offset-2 hover:text-accent-500"
                    >
                      {resource.title ?? resource.url}
                    </a>
                  ) : (
                    <span className="text-ink-700">{resource.title ?? 'Untitled resource'}</span>
                  )}
                  {resource.resource_type && <Badge variant="outline">{resource.resource_type}</Badge>}
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export function RoadmapPage() {
  const roadmapQuery = useRoadmap()

  const roadmapMissing = roadmapQuery.error instanceof ApiError && roadmapQuery.error.status === 404

  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 px-6 py-12">
      <div>
        <h1 className="text-2xl font-semibold text-ink-900">Learning roadmap</h1>
        <p className="mt-1 text-sm text-ink-400">Personalized recommendations based on your interview performance.</p>
      </div>

      {roadmapQuery.isLoading && (
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </CardContent>
        </Card>
      )}

      {roadmapMissing && (
        <Card>
          <CardHeader>
            <CardTitle>No roadmap yet</CardTitle>
            <CardDescription>Complete an interview session to get a personalized roadmap.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" className="w-fit">
              <Link to="/start-interview">Start an interview</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {roadmapQuery.data && roadmapQuery.data.status !== 'ready' && (
        <Card>
          <CardHeader>
            <CardTitle>
              {roadmapQuery.data.status === 'failed' ? 'Roadmap generation failed' : 'Generating your roadmap...'}
            </CardTitle>
            <CardDescription>
              {roadmapQuery.data.status === 'failed'
                ? (roadmapQuery.data.error_message ?? 'Something went wrong generating your roadmap.')
                : 'This usually takes a few moments after your session finishes. Refresh to check again.'}
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {roadmapQuery.data && roadmapQuery.data.status === 'ready' && (
        <>
          {roadmapQuery.data.summary && (
            <Card>
              <CardHeader>
                <CardTitle>Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-ink-700">{roadmapQuery.data.summary}</p>
              </CardContent>
            </Card>
          )}

          {(roadmapQuery.data.strengths?.length || roadmapQuery.data.growth_areas?.length) && (
            <div className="grid gap-4 sm:grid-cols-2">
              {roadmapQuery.data.strengths && roadmapQuery.data.strengths.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Strengths</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="flex flex-col gap-2 text-sm text-ink-700">
                      {roadmapQuery.data.strengths.map((strength) => (
                        <li key={strength} className="flex items-start gap-2">
                          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success-600" />
                          {strength}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
              {roadmapQuery.data.growth_areas && roadmapQuery.data.growth_areas.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Growth areas</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="flex flex-col gap-2 text-sm text-ink-700">
                      {roadmapQuery.data.growth_areas.map((area) => (
                        <li key={area} className="flex items-start gap-2">
                          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-warning-600" />
                          {area}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {PRIORITY_SECTIONS.map(({ priority, label, dotClass, borderClass }) => {
            const items = roadmapQuery.data.items.filter((item) => item.priority === priority)
            if (items.length === 0) return null
            return (
              <div key={priority} className="flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <span className={cn('size-2 rounded-full', dotClass)} />
                  <h2 className="text-sm font-semibold text-ink-900">{label}</h2>
                  <span className="text-xs text-ink-400">({items.length})</span>
                </div>
                <div className="flex flex-col gap-4">
                  {items.map((item) => (
                    <RoadmapItemCard key={item.topic} item={item} borderClass={borderClass} />
                  ))}
                </div>
              </div>
            )
          })}
        </>
      )}
    </main>
  )
}
