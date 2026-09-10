import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { InterviewPlanOut } from '@/lib/api'

interface ReadyStepProps {
  plan: InterviewPlanOut
  onStart: () => void
  isStarting: boolean
  isError: boolean
}

export function ReadyStep({ plan, onStart, isStarting, isError }: ReadyStepProps) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-6 pt-6">
        <div>
          <p className="text-sm font-medium text-ink-900">
            {plan.format} format - {plan.question_count} questions
          </p>
        </div>

        <div className="flex gap-8 text-sm">
          <div>
            <p className="font-medium text-ink-900">Candidate level</p>
            <p className="capitalize text-ink-600">{plan.candidate_level}</p>
          </div>
          <div>
            <p className="font-medium text-ink-900">Difficulty range</p>
            <p className="text-ink-600">
              {plan.difficulty_min} - {plan.difficulty_max} (of 5)
            </p>
          </div>
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-ink-900">Topic mix</p>
          <div className="overflow-hidden rounded-md border border-border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Topic</TableHead>
                  <TableHead className="text-right">Questions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(plan.topic_mix ?? []).map((entry) => (
                  <TableRow key={entry.topic}>
                    <TableCell>{entry.topic}</TableCell>
                    <TableCell className="text-right">{entry.question_count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-ink-900">Rationale</p>
          <p className="mt-1 text-sm text-ink-600">{plan.rationale}</p>
        </div>

        {isError && <p className="text-sm text-danger-600">Could not start the interview. Please try again.</p>}
        <Button onClick={onStart} disabled={isStarting} className="w-fit">
          {isStarting ? 'Starting…' : 'Start interview'}
        </Button>
      </CardContent>
    </Card>
  )
}
