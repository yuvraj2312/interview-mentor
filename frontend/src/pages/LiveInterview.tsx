import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'

import { useInterviewSessionSocket } from '@/hooks/useInterviewSession'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Textarea } from '@/components/ui/textarea'
import type { InterviewEvaluation } from '@/lib/api'

function ScoreRow({ evaluation }: { evaluation: InterviewEvaluation }) {
  return (
    <div className="flex flex-wrap gap-4 text-xs text-ink-600">
      <span>Technical: {evaluation.technical_score}</span>
      <span>Communication: {evaluation.communication_score}</span>
      <span>Completeness: {evaluation.completeness_score}</span>
    </div>
  )
}

function ConnectionIndicator({ status }: { status: string }) {
  if (status === 'reconnecting') {
    return (
      <span className="flex items-center gap-1.5 text-xs font-medium text-warning-700">
        <Loader2 className="size-3 animate-spin" />
        Reconnecting…
      </span>
    )
  }
  if (status === 'connecting') {
    return (
      <span className="flex items-center gap-1.5 text-xs font-medium text-ink-400">
        <Loader2 className="size-3 animate-spin" />
        Connecting…
      </span>
    )
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
      <main className="mx-auto max-w-2xl px-6 py-16">
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
    )
  }

  if (!state) {
    return (
      <main className="flex items-center justify-center gap-2 px-6 py-16 text-sm text-ink-400">
        <Loader2 className="size-4 animate-spin" />
        Connecting to your interview...
      </main>
    )
  }

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-16">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <p className="text-sm text-ink-600">
            Question {Math.min(state.turn_index + 1, state.total_questions)} of {state.total_questions}
          </p>
          <ConnectionIndicator status={connectionStatus} />
        </div>
        <Progress value={history.length} max={state.total_questions} />
        <p className="text-xs text-ink-400">
          ${state.total_cost_usd.toFixed(3)} / ${state.cost_cap_usd.toFixed(2)} used
        </p>
      </div>

      {history.length > 0 && (
        <div className="flex max-h-96 flex-col gap-4 overflow-y-auto">
          {isHistoryLoading && <p className="text-xs text-ink-400">Loading history...</p>}
          {history.map((turn) => (
            <Card key={turn.turn_index}>
              <CardContent className="flex flex-col gap-2 pt-6">
                <p className="text-sm font-medium text-ink-900">{turn.question_text}</p>
                <p className="text-sm text-ink-600">{turn.answer_text}</p>
                {turn.evaluation && (
                  <>
                    <ScoreRow evaluation={turn.evaluation} />
                    <p className="text-xs text-ink-400">{turn.evaluation.rationale}</p>
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
            <p className="text-sm text-ink-900">{state.current_question.question_text}</p>
            <Textarea
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              placeholder="Type your answer..."
              rows={6}
            />
            {submitError && <p className="text-sm text-danger-600">{submitError}</p>}
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
        <Card className="border-l-4 border-l-accent-500">
          <CardContent className="flex flex-col gap-4 pt-6">
            <p className="flex items-center gap-2 text-sm text-ink-600">
              <Loader2 className="size-4 animate-spin text-accent-600" />
              Your last answer is being processed. This should resolve in a few seconds. If it doesn't, reconnect.
            </p>
            <Button variant="outline" onClick={reconnect} className="w-fit">
              Reconnect
            </Button>
          </CardContent>
        </Card>
      )}

      {state.status === 'complete' && state.summary && (
        <Card className="border-l-4 border-l-success-600">
          <CardHeader>
            <CardTitle>Interview complete</CardTitle>
            <CardDescription>
              {state.stop_reason === 'cost_cap_exceeded'
                ? "This session ended early because it reached its cost limit. Here's how you did so far."
                : "Here's how you did."}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex flex-wrap gap-4 text-sm text-ink-700">
              <span>Avg technical: {state.summary.avg_technical_score.toFixed(1)}</span>
              <span>Avg communication: {state.summary.avg_communication_score.toFixed(1)}</span>
              <span>Avg completeness: {state.summary.avg_completeness_score.toFixed(1)}</span>
            </div>
            <div>
              <p className="text-sm font-medium text-ink-900">Difficulty path</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {state.summary.difficulty_path.map((d, i) => (
                  <Badge key={i}>{d}</Badge>
                ))}
              </div>
            </div>
            <Button asChild className="w-fit">
              <Link to="/dashboard">Back to dashboard</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {state.status === 'abandoned' && (
        <Card className="border-l-4 border-l-ink-400">
          <CardHeader>
            <CardTitle>Session abandoned</CardTitle>
            <CardDescription>This interview session was abandoned due to inactivity.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild className="w-fit">
              <Link to="/dashboard">Back to dashboard</Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </main>
  )
}
