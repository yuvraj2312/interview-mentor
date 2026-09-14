import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import type { ResumeEducationEntry, ResumeExperienceEntry, ResumeProjectEntry } from '@/types/resume'

// Dates are shown as extracted/edited free text (e.g. "Jun 2021", "Present"),
// not reformatted - they aren't guaranteed to be ISO dates.
export function ExperienceCard({ entry }: { entry: ResumeExperienceEntry }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-1 pt-6">
        <p className="text-sm font-medium text-ink-900">{entry.title || 'Untitled role'}</p>
        <p className="text-sm text-ink-600">
          {entry.company}
          {entry.company && (entry.start_date || entry.end_date) ? ' · ' : ''}
          {[entry.start_date, entry.end_date].filter(Boolean).join(' – ')}
        </p>
        {entry.description && <p className="mt-1 whitespace-pre-wrap text-sm text-ink-600">{entry.description}</p>}
      </CardContent>
    </Card>
  )
}

export function EducationCard({ entry }: { entry: ResumeEducationEntry }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-1 pt-6">
        <p className="text-sm font-medium text-ink-900">{entry.degree || 'Untitled degree'}</p>
        <p className="text-sm text-ink-600">
          {[entry.field_of_study, entry.institution].filter(Boolean).join(' · ')}
          {entry.graduation_date ? ` · ${entry.graduation_date}` : ''}
        </p>
      </CardContent>
    </Card>
  )
}

export function ProjectCard({ entry }: { entry: ResumeProjectEntry }) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-2 pt-6">
        <p className="text-sm font-medium text-ink-900">{entry.name || 'Untitled project'}</p>
        {entry.description && <p className="whitespace-pre-wrap text-sm text-ink-600">{entry.description}</p>}
        {entry.technologies.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {entry.technologies.map((tech) => (
              <Badge key={tech} variant="outline">
                {tech}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
