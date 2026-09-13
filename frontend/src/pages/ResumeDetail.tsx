import { Link, useParams } from 'react-router-dom'

import { ResourceStatusBadge } from '@/components/ResourceStatusBadge'
import { useResumeQuery } from '@/hooks/useResume'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { formatDate } from '@/lib/format'

function hasItems(value: unknown): value is unknown[] {
  return Array.isArray(value) && value.length > 0
}

function StructuredListSection({ label, value, emptyLabel }: { label: string; value: unknown; emptyLabel: string }) {
  return (
    <div>
      <p className="text-sm font-medium text-ink-900">{label}</p>
      {hasItems(value) ? (
        <pre className="mt-2 overflow-x-auto rounded-md bg-surface-muted p-3 text-xs text-ink-600">
          {JSON.stringify(value, null, 2)}
        </pre>
      ) : (
        <p className="mt-2 text-sm text-ink-400">{emptyLabel}</p>
      )}
    </div>
  )
}

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
                  {structuredData.skills && structuredData.skills.length > 0 ? (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {structuredData.skills.map((skill) => (
                        <Badge key={skill} variant="outline">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-2 text-sm text-ink-400">No skills listed</p>
                  )}
                </div>
                <StructuredListSection
                  label="Experience"
                  value={structuredData.experience}
                  emptyLabel="No experience listed"
                />
                <StructuredListSection
                  label="Education"
                  value={structuredData.education}
                  emptyLabel="No education listed"
                />
                <StructuredListSection
                  label="Projects"
                  value={structuredData.projects}
                  emptyLabel="No projects listed"
                />
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
