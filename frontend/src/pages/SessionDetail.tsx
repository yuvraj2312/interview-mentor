import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { getInterviewSessionTranscript, type InterviewEvaluation } from '@/lib/api'

function ScoreRow({ evaluation }: { evaluation: InterviewEvaluation }) {
  return (
    <div className="flex flex-wrap gap-2">
      <Badge variant="outline">Technical {evaluation.technical_score.toFixed(1)}</Badge>
      <Badge variant="outline">Communication {evaluation.communication_score.toFixed(1)}</Badge>
      <Badge variant="outline">Completeness {evaluation.completeness_score.toFixed(1)}</Badge>
    </div>
  )
}

export function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>()

  const transcriptQuery = useQuery({
    queryKey: ['interview-session-transcript', sessionId],
    queryFn: () => getInterviewSessionTranscript(sessionId!),
    enabled: Boolean(sessionId),
  })

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-ink-900">Session transcript</h1>
          <p className="mt-1 text-sm text-ink-400">
            {transcriptQuery.data ? `${transcriptQuery.data.total_questions} questions` : ''}
          </p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/sessions">Back to sessions</Link>
        </Button>
      </div>

      {transcriptQuery.isLoading && (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      )}
      {transcriptQuery.isError && <p className="text-sm text-danger-600">Could not load this session.</p>}

      {transcriptQuery.data && (
        <div className="flex flex-col gap-4">
          {transcriptQuery.data.turns.map((turn) => (
            <Card key={turn.turn_index}>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CardTitle className="text-base">{turn.topic}</CardTitle>
                  {turn.is_followup && <Badge variant="outline">Follow-up</Badge>}
                </div>
                <CardDescription>Difficulty {turn.difficulty} of 5</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                <p className="text-sm font-medium text-ink-900">{turn.question_text}</p>
                {turn.answer_text && <p className="text-sm text-ink-600">{turn.answer_text}</p>}
                {turn.evaluation && (
                  <>
                    <ScoreRow evaluation={turn.evaluation} />
                    <p className="text-xs text-ink-400">{turn.evaluation.rationale}</p>
                  </>
                )}
                {!turn.evaluation && <p className="text-xs text-ink-400">Not answered.</p>}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </main>
  )
}
