import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'

import { AppHeader } from '@/components/AppHeader'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getInterviewSessionTranscript, type InterviewEvaluation } from '@/lib/api'

function ScoreRow({ evaluation }: { evaluation: InterviewEvaluation }) {
  return (
    <div className="flex flex-wrap gap-4 text-xs text-slate-600">
      <span>Technical: {evaluation.technical_score.toFixed(1)}</span>
      <span>Communication: {evaluation.communication_score.toFixed(1)}</span>
      <span>Completeness: {evaluation.completeness_score.toFixed(1)}</span>
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
    <div className="min-h-svh bg-slate-50">
      <AppHeader />
      <main className="mx-auto max-w-2xl px-6 py-12 flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Session transcript</h1>
            <p className="mt-1 text-sm text-slate-500">
              {transcriptQuery.data ? `${transcriptQuery.data.total_questions} questions` : ''}
            </p>
          </div>
          <Button asChild variant="outline" size="sm">
            <Link to="/sessions">Back to sessions</Link>
          </Button>
        </div>

        {transcriptQuery.isLoading && <p className="text-sm text-slate-500">Loading transcript...</p>}
        {transcriptQuery.isError && <p className="text-sm text-red-600">Could not load this session.</p>}

        {transcriptQuery.data && (
          <div className="flex flex-col gap-4">
            {transcriptQuery.data.turns.map((turn) => (
              <Card key={turn.turn_index}>
                <CardHeader>
                  <CardTitle className="text-base">{turn.topic}</CardTitle>
                  <CardDescription>Difficulty {turn.difficulty} of 5</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col gap-2">
                  <p className="text-sm font-medium text-slate-900">{turn.question_text}</p>
                  {turn.answer_text && <p className="text-sm text-slate-600">{turn.answer_text}</p>}
                  {turn.evaluation && (
                    <>
                      <ScoreRow evaluation={turn.evaluation} />
                      <p className="text-xs text-slate-500">{turn.evaluation.rationale}</p>
                    </>
                  )}
                  {!turn.evaluation && <p className="text-xs text-slate-400">Not answered.</p>}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
