import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useInterviewSessionSocket } from '@/hooks/useInterviewSession'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Textarea } from '@/components/ui/textarea'
import type { InterviewEvaluation } from '@/lib/api'

function ScoreRow({ evaluation }: { evaluation: InterviewEvaluation }) {
  return (
    <div className="flex flex-wrap gap-4 text-xs text-slate-600">
      <span>Technical: {evaluation.technical_score}</span>
      <span>Communication: {evaluation.communication_score}</span>
      <span>Completeness: {evaluation.completeness_score}</span>
    </div>
  )
}

function ConnectionIndicator({ status }: { status: string }) {
  if (status === 'reconnecting') {
    return <span className="text-xs font-medium text-amber-700">Reconnecting…</span>
  }
  if (status === 'connecting') {
    return <span className="text-xs font-medium text-slate-500">Connecting…</span>
  }
  return null
}

export function LiveInterviewPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const {
    connectionStatus,
    permanentError,
    state,
    history,
    isHistoryLoading,
    isSubmitting,
    submitError,
    submitAnswer,
    reconnect,
  } = useInterviewSessionSocket(sessionId)

  const [answerText, setAnswerText] = useState('')

  useEffect(() => {
    setAnswerText('')
  }, [history.length])

  if (permanentError) {
    return (
      <div className="min-h-svh bg-slate-50 px-6 py-16">
        <main className="mx-auto max-w-2xl">
          <Card>
            <CardHeader>
              <CardTitle>Connection problem</CardTitle>
              <CardDescription>{permanentError.message}</CardDescription>
            </CardHeader>
            <CardContent>
              {permanentError.kind === 'auth' && (
                <Button asChild>
                  <Link to="/login">Log in again</Link>
                </Button>
              )}
              {permanentError.kind === 'not_found' && (
                <Button asChild variant="outline">
                  <Link to="/dashboard">Back to dashboard</Link>
                </Button>
              )}
              {permanentError.kind === 'unknown' && <Button onClick={reconnect}>Reconnect</Button>}
            </CardContent>
          </Card>
        </main>
      </div>
    )
  }

  if (!state) {
    return (
      <div className="min-h-svh bg-slate-50 px-6 py-16 text-center text-sm text-slate-500">
        Connecting to your interview...
      </div>
    )
  }

  return (
    <div className="min-h-svh bg-slate-50">
      <main className="mx-auto max-w-2xl px-6 py-16 flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-600">
              Question {Math.min(state.turn_index + 1, state.total_questions)} of {state.total_questions}
            </p>
            <ConnectionIndicator status={connectionStatus} />
          </div>
          <Progress value={history.length} max={state.total_questions} />
        </div>

        {history.length > 0 && (
          <div className="flex flex-col gap-4 max-h-96 overflow-y-auto">
            {isHistoryLoading && <p className="text-xs text-slate-500">Loading history...</p>}
            {history.map((turn) => (
              <Card key={turn.turn_index}>
                <CardContent className="flex flex-col gap-2 pt-6">
                  <p className="text-sm font-medium text-slate-900">{turn.question_text}</p>
                  <p className="text-sm text-slate-600">{turn.answer_text}</p>
                  {turn.evaluation && (
                    <>
                      <ScoreRow evaluation={turn.evaluation} />
                      <p className="text-xs text-slate-500">{turn.evaluation.rationale}</p>
                    </>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {state.status === 'in_progress' && state.current_question && (
          <Card>
            <CardHeader>
              <CardTitle>{state.current_question.topic}</CardTitle>
              <CardDescription>Difficulty {state.current_question.difficulty} of 5</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <p className="text-sm text-slate-900">{state.current_question.question_text}</p>
              <Textarea
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                placeholder="Type your answer..."
                rows={6}
              />
              {submitError && <p className="text-sm text-red-600">{submitError}</p>}
              <Button
                onClick={() => submitAnswer(answerText)}
                disabled={isSubmitting || connectionStatus !== 'open' || !answerText.trim()}
                className="w-fit"
              >
                {isSubmitting ? 'Submitting…' : 'Submit answer'}
              </Button>
            </CardContent>
          </Card>
        )}

        {(state.status === 'evaluating' || state.status === 'advancing') && (
          <Card>
            <CardContent className="flex flex-col gap-4 pt-6">
              <p className="text-sm text-slate-600">
                Your last answer is being processed. This should resolve in a few seconds. If it doesn't, reconnect.
              </p>
              <Button variant="outline" onClick={reconnect} className="w-fit">
                Reconnect
              </Button>
            </CardContent>
          </Card>
        )}

        {state.status === 'complete' && state.summary && (
          <Card>
            <CardHeader>
              <CardTitle>Interview complete</CardTitle>
              <CardDescription>Here's how you did.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex flex-wrap gap-4 text-sm text-slate-700">
                <span>Avg technical: {state.summary.avg_technical_score.toFixed(1)}</span>
                <span>Avg communication: {state.summary.avg_communication_score.toFixed(1)}</span>
                <span>Avg completeness: {state.summary.avg_completeness_score.toFixed(1)}</span>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-900">Difficulty path</p>
                <div className="mt-2 flex gap-2">
                  {state.summary.difficulty_path.map((d, i) => (
                    <span key={i} className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-700">
                      {d}
                    </span>
                  ))}
                </div>
              </div>
              <Button asChild className="w-fit">
                <Link to={`/interview-plans/${state.interview_plan_id}/review`}>Back to plan</Link>
              </Button>
            </CardContent>
          </Card>
        )}

        {state.status === 'abandoned' && (
          <Card>
            <CardHeader>
              <CardTitle>Session abandoned</CardTitle>
              <CardDescription>This interview session was abandoned due to inactivity.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild className="w-fit">
                <Link to={`/interview-plans/${state.interview_plan_id}/review`}>Back to plan</Link>
              </Button>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
