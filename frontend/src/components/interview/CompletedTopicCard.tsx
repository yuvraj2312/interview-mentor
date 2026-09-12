import { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import type { InterviewEvaluation, InterviewTurnOut } from '@/lib/api'

export function ScoreRow({ evaluation }: { evaluation: InterviewEvaluation }) {
  return (
    <div className="flex flex-wrap gap-4 text-xs text-ink-600">
      <span>Technical: {evaluation.technical_score}</span>
      <span>Communication: {evaluation.communication_score}</span>
      <span>Completeness: {evaluation.completeness_score}</span>
    </div>
  )
}

function averageScore(turns: InterviewTurnOut[]): number | null {
  const scored = turns.filter((t): t is InterviewTurnOut & { evaluation: InterviewEvaluation } => t.evaluation !== null)
  if (scored.length === 0) return null
  const total = scored.reduce((sum, t) => {
    const e = t.evaluation
    return sum + (e.technical_score + e.communication_score + e.completeness_score) / 3
  }, 0)
  return total / scored.length
}

interface CompletedTopicCardProps {
  topicNumber: number
  turns: InterviewTurnOut[]
}

/** Collapsed by default (question + score only) so the completed-topics
 * panel stays scannable as the interview progresses; expands on click to
 * show every turn's full question/answer/evaluation for that topic. */
export function CompletedTopicCard({ topicNumber, turns }: CompletedTopicCardProps) {
  const [expanded, setExpanded] = useState(false)
  const mainTurn = turns[0]
  const avgScore = averageScore(turns)

  if (!mainTurn) return null

  return (
    <Card>
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="flex w-full items-start justify-between gap-3 p-4 text-left"
      >
        <div className="flex flex-col gap-1">
          <p className="text-xs font-medium text-ink-400">Topic {topicNumber}</p>
          <p className="line-clamp-2 text-sm font-medium text-ink-900">{mainTurn.question_text}</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {avgScore !== null && <Badge variant="outline">{avgScore.toFixed(1)}</Badge>}
          {expanded ? (
            <ChevronUp className="size-4 text-ink-400" />
          ) : (
            <ChevronDown className="size-4 text-ink-400" />
          )}
        </div>
      </button>
      {expanded && (
        <CardContent className="flex flex-col gap-4 border-t border-border pt-4">
          {turns.map((turn) => (
            <div key={turn.turn_index} className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                {turn.is_followup && <Badge variant="outline">Follow-up</Badge>}
                <p className="text-sm font-medium text-ink-900">{turn.question_text}</p>
              </div>
              <p className="text-sm text-ink-600">{turn.answer_text}</p>
              {turn.evaluation && (
                <>
                  <ScoreRow evaluation={turn.evaluation} />
                  <p className="text-xs text-ink-400">{turn.evaluation.rationale}</p>
                </>
              )}
            </div>
          ))}
        </CardContent>
      )}
    </Card>
  )
}
