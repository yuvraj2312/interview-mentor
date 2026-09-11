import { Link, useParams } from 'react-router-dom'

import { ResourceStatusBadge } from '@/components/ResourceStatusBadge'
import { useResumeQuery } from '@/hooks/useResume'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDate } from '@/lib/format'

export function ResumeDetailPage() {
  const { resumeId } = useParams<{ resumeId: string }>()
  const resumeQuery = useResumeQuery(resumeId)

  const structuredData = resumeQuery.data?.structured_data as
    | { skills?: string[]; experience?: unknown; education?: unknown; projects?: unknown }
    | null
    | undefined

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-ink-900">
            {resumeQuery.data?.original_filename ?? 'Resume'}
          </h1>
          {resumeQuery.data && (
            <p className="mt-1 text-sm text-ink-400">Uploaded {formatDate(resumeQuery.data.created_at)}</p>
          )}
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/dashboard">Back to dashboard</Link>
        </Button>
      </div>

      {resumeQuery.isLoading && <Skeleton className="h-64 w-full" />}
      {resumeQuery.isError && <p className="text-sm text-danger-600">Could not load this resume.</p>}

      {resumeQuery.data && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-base">Details</CardTitle>
            <ResourceStatusBadge status={resumeQuery.data.status} />
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {resumeQuery.data.status === 'failed' && (
              <p className="text-sm text-danger-600">Processing failed: {resumeQuery.data.error_message}</p>
            )}
            {structuredData && (
              <>
                <div>
                  <p className="text-sm font-medium text-ink-900">Skills</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(structuredData.skills ?? []).map((skill) => (
                      <Badge key={skill} variant="outline">
                        {skill}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm font-medium text-ink-900">Experience</p>
                  <pre className="mt-2 overflow-x-auto rounded-md bg-surface-muted p-3 text-xs text-ink-600">
                    {JSON.stringify(structuredData.experience ?? [], null, 2)}
                  </pre>
                </div>
                <div>
                  <p className="text-sm font-medium text-ink-900">Education</p>
                  <pre className="mt-2 overflow-x-auto rounded-md bg-surface-muted p-3 text-xs text-ink-600">
                    {JSON.stringify(structuredData.education ?? [], null, 2)}
                  </pre>
                </div>
                <div>
                  <p className="text-sm font-medium text-ink-900">Projects</p>
                  <pre className="mt-2 overflow-x-auto rounded-md bg-surface-muted p-3 text-xs text-ink-600">
                    {JSON.stringify(structuredData.projects ?? [], null, 2)}
                  </pre>
                </div>
              </>
            )}
            {!structuredData && resumeQuery.data.status !== 'failed' && (
              <p className="text-sm text-ink-400">Still processing...</p>
            )}
          </CardContent>
        </Card>
      )}
    </main>
  )
}
