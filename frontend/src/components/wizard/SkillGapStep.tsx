import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import type { SkillGapOut } from '@/lib/api'

function SkillChipRow({
  label,
  skills,
  variant,
}: {
  label: string
  skills: string[]
  variant: 'good' | 'critical' | 'warning'
}) {
  return (
    <div>
      <p className="mb-1.5 text-sm font-medium text-ink-700">{label}</p>
      {skills.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {skills.map((skill) => (
            <Badge key={skill} variant={variant}>
              {skill}
            </Badge>
          ))}
        </div>
      ) : (
        <p className="text-sm text-ink-400">None</p>
      )}
    </div>
  )
}

interface SkillGapStepProps {
  isPending: boolean
  isError: boolean
  data: SkillGapOut | undefined
}

export function SkillGapStep({ isPending, isError, data }: SkillGapStepProps) {
  const matchScore = data ? Math.round(data.match_score * 100) : 0
  const matchVariant = matchScore >= 70 ? 'good' : matchScore >= 40 ? 'warning' : 'critical'
  const matchFillClass =
    matchVariant === 'good' ? 'bg-success-600' : matchVariant === 'warning' ? 'bg-warning-600' : 'bg-danger-600'

  return (
    <Card>
      <CardContent className="flex flex-col gap-5 pt-6">
        {isPending && (
          <div className="flex flex-col gap-3">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-2 w-full" />
            <Skeleton className="h-16 w-full" />
            <p className="text-sm text-ink-400">Comparing your resume against the job description...</p>
          </div>
        )}

        {isError && (
          <p className="text-sm text-danger-600">Couldn't compute the skill gap. Try going back and re-selecting your resume or job description.</p>
        )}

        {data && (
          <>
            <div>
              <div className="mb-1.5 flex items-center justify-between text-sm">
                <span className="font-medium text-ink-900">Match score</span>
                <span className="font-semibold text-ink-900">{matchScore}%</span>
              </div>
              <Progress value={matchScore} max={100} indicatorClassName={matchFillClass} />
            </div>
            <SkillChipRow label="Matched" skills={data.matched_skills} variant="good" />
            <SkillChipRow label="Missing required" skills={data.missing_required_skills} variant="critical" />
            <SkillChipRow label="Missing preferred" skills={data.missing_preferred_skills} variant="warning" />
          </>
        )}
      </CardContent>
    </Card>
  )
}
