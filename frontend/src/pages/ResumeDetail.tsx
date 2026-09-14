import type { ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ResourceStatusBadge } from '@/components/ResourceStatusBadge'
import { useResumeQuery } from '@/hooks/useResume'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { EducationCard, ExperienceCard, ProjectCard } from '@/components/ResumeEntryCard'
import { formatDate } from '@/lib/format'
import type { ResumeStructuredData } from '@/types/resume'

function StructuredListSection<T>({
  label,
  entries,
  emptyLabel,
  renderEntry,
}: {
  label: string
  entries: T[] | undefined
  emptyLabel: string
  renderEntry: (entry: T, index: number) => ReactNode
}) {
  return (
    <div>
      <p className="text-sm font-medium text-ink-900">{label}</p>
      {entries && entries.length > 0 ? (
        <div className="mt-2 flex flex-col gap-3">{entries.map(renderEntry)}</div>
      ) : (
        <p className="mt-2 text-sm text-ink-400">{emptyLabel}</p>
      )}
    </div>
  )
}

export function ResumeDetailPage() {
  const { resumeId } = useParams<{ resumeId: string }>()
  const resumeQuery = useResumeQuery(resumeId)

  const structuredData = resumeQuery.data?.structured_data as ResumeStructuredData | null | undefined

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
                  entries={structuredData.experience}
                  emptyLabel="No experience listed"
                  renderEntry={(entry, index) => <ExperienceCard key={index} entry={entry} />}
                />
                <StructuredListSection
                  label="Education"
                  entries={structuredData.education}
                  emptyLabel="No education listed"
                  renderEntry={(entry, index) => <EducationCard key={index} entry={entry} />}
                />
                <StructuredListSection
                  label="Projects"
                  entries={structuredData.projects}
                  emptyLabel="No projects listed"
                  renderEntry={(entry, index) => <ProjectCard key={index} entry={entry} />}
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
