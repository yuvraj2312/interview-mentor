import { Link, useParams } from 'react-router-dom'

import { ResourceStatusBadge } from '@/components/ResourceStatusBadge'
import { useJobDescriptionQuery } from '@/hooks/useJobDescription'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDate } from '@/lib/format'

export function JobDescriptionDetailPage() {
  const { jdId } = useParams<{ jdId: string }>()
  const jdQuery = useJobDescriptionQuery(jdId)

  const structuredData = jdQuery.data?.structured_data as
    | { required_skills?: string[]; preferred_skills?: string[]; seniority_level?: string }
    | null
    | undefined

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-ink-900">Job description</h1>
          {jdQuery.data && (
            <p className="mt-1 text-sm text-ink-400">Added {formatDate(jdQuery.data.created_at)}</p>
          )}
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/dashboard">Back to dashboard</Link>
        </Button>
      </div>

      {jdQuery.isLoading && <Skeleton className="h-64 w-full" />}
      {jdQuery.isError && <p className="text-sm text-danger-600">Could not load this job description.</p>}

      {jdQuery.data && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Details</CardTitle>
            <ResourceStatusBadge status={jdQuery.data.status} />
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {jdQuery.data.status === 'failed' && (
              <p className="text-sm text-danger-600">Analysis failed: {jdQuery.data.error_message}</p>
            )}
            {structuredData && (
              <>
                <div>
                  <p className="text-sm font-medium text-ink-900">Required skills</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(structuredData.required_skills ?? []).map((skill) => (
                      <Badge key={skill} variant="outline">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-ink-900">Preferred skills</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(structuredData.preferred_skills ?? []).map((skill) => (
                      <Badge key={skill} variant="outline">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-ink-900">Seniority level</p>
                  <p className="mt-1 text-sm text-ink-600">{structuredData.seniority_level}</p>
                </div>
              </>
            )}
            <div>
              <p className="text-sm font-medium text-ink-900">Raw text</p>
              <p className="mt-2 whitespace-pre-wrap text-sm text-ink-600">{jdQuery.data.raw_text}</p>
            </div>
          </CardContent>
        </Card>
      )}
    </main>
  )
}
