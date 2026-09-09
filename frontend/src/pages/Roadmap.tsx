import { Link } from 'react-router-dom'

import { AppHeader } from '@/components/AppHeader'
import { PriorityBadge } from '@/components/PriorityBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useRoadmap } from '@/hooks/useRoadmap'
import { ApiError, type RoadmapItemOut, type RoadmapPriority } from '@/lib/api'

const PRIORITY_ORDER: Record<RoadmapPriority, number> = { high: 0, medium: 1, low: 2 }

function RoadmapItemCard({ item }: { item: RoadmapItemOut }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-4">
          <CardTitle className="text-base">{item.topic}</CardTitle>
          <PriorityBadge priority={item.priority} />
        </div>
        <CardDescription>{item.gap_description}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <p className="text-sm text-slate-700">{item.recommended_action}</p>
        {item.resources.length > 0 && (
          <div className="flex flex-col gap-2">
            <p className="text-xs font-medium text-slate-500">Resources</p>
            <div className="flex flex-col gap-1.5">
              {item.resources.map((resource) => (
                <div key={resource.resource_id} className="flex items-center gap-2 text-sm">
                  {resource.url ? (
                    <a
                      href={resource.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-slate-900 underline underline-offset-2 hover:text-slate-600"
                    >
                      {resource.title ?? resource.url}
                    </a>
                  ) : (
                    <span className="text-slate-700">{resource.title ?? 'Untitled resource'}</span>
                  )}
                  {resource.resource_type && (
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                      {resource.resource_type}
                    </span>
                  )}
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
    <div className="min-h-svh bg-slate-50">
      <AppHeader />
      <main className="mx-auto max-w-3xl px-6 py-12 flex flex-col gap-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Learning roadmap</h1>
          <p className="mt-1 text-sm text-slate-500">Personalized recommendations based on your interview performance.</p>
        </div>

        {roadmapQuery.isLoading && <p className="text-sm text-slate-500">Loading roadmap...</p>}

        {roadmapMissing && (
          <Card>
            <CardHeader>
              <CardTitle>No roadmap yet</CardTitle>
              <CardDescription>Complete an interview session to get a personalized roadmap.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="outline" className="w-fit">
                <Link to="/interview-plans/new">Start an interview</Link>
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
                  <p className="text-sm text-slate-700">{roadmapQuery.data.summary}</p>
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
                      <ul className="flex flex-col gap-1.5 text-sm text-slate-700">
                        {roadmapQuery.data.strengths.map((strength) => (
                          <li key={strength}>• {strength}</li>
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
                      <ul className="flex flex-col gap-1.5 text-sm text-slate-700">
                        {roadmapQuery.data.growth_areas.map((area) => (
                          <li key={area}>• {area}</li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            <div className="flex flex-col gap-4">
              {[...roadmapQuery.data.items]
                .sort((a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority])
                .map((item) => (
                  <RoadmapItemCard key={item.topic} item={item} />
                ))}
            </div>
          </>
        )}
      </main>
    </div>
  )
}
