import { useEffect, useMemo, useRef, useState } from 'react'
import { Loader2, Mic, Video, VideoOff, Volume2, VolumeX } from 'lucide-react'
import { Link, useBlocker, useParams } from 'react-router-dom'

import { useInterviewSessionSocket } from '@/hooks/useInterviewSession'
import { isSpeechRecognitionSupported, useSpeechRecognition } from '@/hooks/useSpeechRecognition'
import { useSpeechSynthesis } from '@/hooks/useSpeechSynthesis'
import { useCameraPreview } from '@/hooks/useCameraPreview'
import { useInterviewPreferencesStore } from '@/store/interviewPreferencesStore'
import { useLiveInterviewStore } from '@/store/liveInterviewStore'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Textarea } from '@/components/ui/textarea'
import { CameraPreviewTile } from '@/components/voice/CameraPreviewTile'
import { CompletedTopicCard, ScoreRow } from '@/components/interview/CompletedTopicCard'
import type { InterviewTurnOut } from '@/lib/api'

// Shown as a brief transition banner whenever the interview advances to a
// new main topic (i.e. the evaluator didn't need a follow-up on the last
// answer) - a rotating set rather than one fixed line so it reads less
// scripted across a multi-topic session. Deliberately no LLM call here
// (see interview_graph.py's deliver_question_node docstring, still a
// no-op pass-through): a dynamic per-turn acknowledgment would add cost
// and latency to every non-follow-up turn, working against the point of
// a tight per-session cost cap.
const ACKNOWLEDGMENT_PHRASES = [
  "Good answer! Let's move to the next question.",
  "Nice work on that one - on to the next question.",
  "Solid answer. Moving on to the next question.",
  "Good answer - let's keep going.",
]

function splitIntoSentences(text: string): string[] {
  const trimmed = text.trim()
  if (!trimmed) return []
  return trimmed.split(/(?<=[.?!])\s+/).filter(Boolean)
}

function sentenceEndOffsets(sentences: string[]): number[] {
  let total = 0
  return sentences.map((sentence) => {
    total += sentence.length + 1
    return total
  })
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

function ListeningIndicator() {
  return (
    <span className="flex items-center gap-1.5 text-xs font-medium text-accent-600">
      <span className="size-2 rounded-full bg-accent-500 animate-pulse" />
      Listening…
    </span>
  )
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
    clarifications,
    isAskingClarification,
    clarificationError,
    askClarification,
    reconnect,
  } = useInterviewSessionSocket(sessionId)

  const ttsEnabled = useInterviewPreferencesStore((s) => s.ttsEnabled)
  const sttEnabled = useInterviewPreferencesStore((s) => s.sttEnabled)
  const setTtsEnabled = useInterviewPreferencesStore((s) => s.setTtsEnabled)
  const setSttEnabled = useInterviewPreferencesStore((s) => s.setSttEnabled)
  const sttSupported = isSpeechRecognitionSupported()

  // ttsEnabled/sttEnabled are persisted to sessionStorage (see
  // interviewPreferencesStore) so a mid-session toggle survives a page
  // refresh - but that same persistence meant a tester who muted the
  // speaker or mic in one interview would land on the *next* interview,
  // in the same browser tab, with it still off. Both should default on
  // for every fresh interview regardless of what a previous session left
  // behind, so force them on whenever this page mounts for a given
  // session id. A later explicit toggle within this session is untouched.
  useEffect(() => {
    setTtsEnabled(true)
    setSttEnabled(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId])

  // Two fully independent recognizers - one per field. Only one may capture
  // at a time (enforced explicitly below); neither auto-starts, capture only
  // ever begins from an explicit click on that field's own mic button.
  const answerStt = useSpeechRecognition()
  const clarificationStt = useSpeechRecognition()
  const tts = useSpeechSynthesis()
  const camera = useCameraPreview()

  const [answerText, setAnswerText] = useState('')
  const [clarificationQuestion, setClarificationQuestion] = useState('')
  const [revealedSentenceCount, setRevealedSentenceCount] = useState(0)
  const [revealedClarificationSentenceCount, setRevealedClarificationSentenceCount] = useState(0)
  const [acknowledgment, setAcknowledgment] = useState<string | null>(null)
  // undefined until the first live turn_index is observed, so the
  // acknowledgment effect below can tell "just hydrated/reconnected" (no
  // acknowledgment - we don't know whether this state is fresh) apart from
  // "the turn actually just advanced while this page was open."
  const prevTurnIndexRef = useRef<number | undefined>(undefined)

  const questionText = state?.current_question?.question_text ?? ''
  const sentences = useMemo(() => splitIntoSentences(questionText), [questionText])
  const sentenceOffsets = useMemo(() => sentenceEndOffsets(sentences), [sentences])
  const displayedQuestionText =
    ttsEnabled && tts.isSupported ? sentences.slice(0, revealedSentenceCount).join(' ') : questionText

  const latestClarification = clarifications[clarifications.length - 1] ?? null
  const clarificationText = latestClarification?.clarification_text ?? ''
  const clarificationSentences = useMemo(() => splitIntoSentences(clarificationText), [clarificationText])
  const clarificationOffsets = useMemo(() => sentenceEndOffsets(clarificationSentences), [clarificationSentences])
  const displayedClarificationText =
    ttsEnabled && tts.isSupported
      ? clarificationSentences.slice(0, revealedClarificationSentenceCount).join(' ')
      : clarificationText

  // The current topic stays "open" (left panel) through evaluating/advancing
  // - it only moves into the completed-topics panel once the session either
  // starts a new topic or ends. Mirrors the isLive definition below.
  const isTopicOpen =
    state !== null && (state.status === 'in_progress' || state.status === 'evaluating' || state.status === 'advancing')

  const currentTopicTurns = useMemo(() => {
    if (!isTopicOpen) return []
    return history.filter((t) => t.topic_number === state?.topic_number).sort((a, b) => a.turn_index - b.turn_index)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [history, state?.topic_number, isTopicOpen])

  const completedTopics = useMemo(() => {
    const excludeTopicNumber = isTopicOpen ? (state?.topic_number ?? null) : null
    const groups = new Map<number, InterviewTurnOut[]>()
    for (const turn of history) {
      if (turn.topic_number === null || turn.topic_number === excludeTopicNumber) continue
      const list = groups.get(turn.topic_number) ?? []
      list.push(turn)
      groups.set(turn.topic_number, list)
    }
    return Array.from(groups.entries())
      .map(([topicNumber, turns]) => ({
        topicNumber,
        turns: turns.slice().sort((a, b) => a.turn_index - b.turn_index),
      }))
      .sort((a, b) => b.topicNumber - a.topicNumber)
  }, [history, state?.topic_number, isTopicOpen])

  useEffect(() => {
    setAnswerText('')
  }, [history.length])

  useEffect(() => {
    setClarificationQuestion('')
  }, [state?.current_question?.turn_index])

  // Camera preview is local-only: the stream is assigned to a <video> element
  // and never sent anywhere. Start it once on mount; the hook stops all
  // tracks on unmount.
  useEffect(() => {
    void camera.start()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Narrate each question sentence-by-sentence in sync with TTS boundary
  // events. When TTS is off or unsupported, reveal the full text instantly
  // (today's behavior, no regression).
  useEffect(() => {
    if (!ttsEnabled || !tts.isSupported || sentences.length === 0) {
      setRevealedSentenceCount(sentences.length)
      return
    }
    setRevealedSentenceCount(0)
    tts.speak(questionText, (charIndex) => {
      setRevealedSentenceCount((prev) => {
        const idx = sentenceOffsets.findIndex((offset) => charIndex < offset)
        const resolved = idx === -1 ? sentences.length - 1 : idx
        return Math.max(prev, resolved + 1)
      })
    })
    return () => tts.cancel()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state?.current_question?.turn_index, ttsEnabled, tts.isSupported])

  // Brief "good answer, moving on" banner whenever the session advances to a
  // new main-topic question (the evaluator was satisfied with the last
  // answer - no follow-up triggered). Only fires on a transition actually
  // observed while this page is open (prevTurnIndexRef starts undefined),
  // so it never appears on initial connect/reconnect for a question that
  // was already current before this render.
  useEffect(() => {
    const turnIndex = state?.current_question?.turn_index
    const isFollowup = state?.current_question?.is_followup
    const prevTurnIndex = prevTurnIndexRef.current
    prevTurnIndexRef.current = turnIndex

    if (prevTurnIndex === undefined || turnIndex === undefined || turnIndex === prevTurnIndex) return
    if (isFollowup) {
      setAcknowledgment(null)
      return
    }
    setAcknowledgment(ACKNOWLEDGMENT_PHRASES[Math.floor(Math.random() * ACKNOWLEDGMENT_PHRASES.length)])
    const timer = setTimeout(() => setAcknowledgment(null), 5000)
    return () => clearTimeout(timer)
  }, [state?.current_question?.turn_index, state?.current_question?.is_followup])

  // Toggling TTS off mid-narration should stop it immediately and snap to
  // the full text rather than leaving it partially revealed.
  useEffect(() => {
    if (!ttsEnabled) {
      tts.cancel()
      setRevealedSentenceCount(sentences.length)
      setRevealedClarificationSentenceCount(clarificationSentences.length)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ttsEnabled])

  // Narrate each clarification response as it arrives (CE-b), same
  // sentence-by-sentence sync as the main question. This interrupts (cancels)
  // any question narration still in progress - snap the question to fully
  // revealed rather than leaving it frozen mid-sentence.
  useEffect(() => {
    if (!latestClarification) return
    if (!ttsEnabled || !tts.isSupported || clarificationSentences.length === 0) {
      setRevealedClarificationSentenceCount(clarificationSentences.length)
      return
    }
    setRevealedSentenceCount(sentences.length)
    setRevealedClarificationSentenceCount(0)
    tts.speak(clarificationText, (charIndex) => {
      setRevealedClarificationSentenceCount((prev) => {
        const idx = clarificationOffsets.findIndex((offset) => charIndex < offset)
        const resolved = idx === -1 ? clarificationSentences.length - 1 : idx
        return Math.max(prev, resolved + 1)
      })
    })
    return () => tts.cancel()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clarifications.length, ttsEnabled, tts.isSupported])

  // Each recognizer drives only its own field - both stay plain, editable
  // controlled inputs the whole time. Neither ever auto-submits.
  useEffect(() => {
    if (!answerStt.isListening) return
    setAnswerText([answerStt.transcript, answerStt.interimTranscript].filter(Boolean).join(' '))
  }, [answerStt.transcript, answerStt.interimTranscript, answerStt.isListening])

  useEffect(() => {
    if (!clarificationStt.isListening) return
    setClarificationQuestion([clarificationStt.transcript, clarificationStt.interimTranscript].filter(Boolean).join(' '))
  }, [clarificationStt.transcript, clarificationStt.interimTranscript, clarificationStt.isListening])

  // Neither recognizer should carry over into a new question - stop and
  // reset both. Capture never auto-starts; it only begins from an explicit
  // click on a field's own mic button.
  useEffect(() => {
    answerStt.stop()
    answerStt.reset()
    clarificationStt.stop()
    clarificationStt.reset()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state?.current_question?.turn_index])

  function toggleAnswerMic() {
    if (answerStt.isListening) {
      answerStt.stop()
      return
    }
    clarificationStt.stop()
    answerStt.reset()
    answerStt.start()
  }

  function toggleClarificationMic() {
    if (clarificationStt.isListening) {
      clarificationStt.stop()
      return
    }
    answerStt.stop()
    clarificationStt.reset()
    clarificationStt.start()
  }

  const clarificationsExhausted =
    clarifications.length > 0 && clarifications[clarifications.length - 1].clarifications_remaining === 0

  const isLive =
    !permanentError &&
    state !== null &&
    (state.status === 'in_progress' || state.status === 'evaluating' || state.status === 'advancing')

  useEffect(() => {
    if (!isLive) return
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [isLive])

  useEffect(() => {
    useLiveInterviewStore.getState().setIsLive(isLive)
    return () => useLiveInterviewStore.getState().setIsLive(false)
  }, [isLive])

  const blocker = useBlocker(isLive)

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
    <div className="mx-auto max-w-6xl">
      {camera.stream && (
        <div className="fixed bottom-4 right-4 z-10">
          <CameraPreviewTile stream={camera.stream} size="sm" />
        </div>
      )}

      <header className="sticky top-[54px] z-20 flex flex-col gap-2 border-b border-border bg-surface px-6 py-3">
        <div className="flex flex-wrap items-center justify-between gap-y-2">
          <div className="flex flex-col gap-0.5">
            <p className="text-sm text-ink-600">
              Topic {Math.min(state.topic_number, state.total_questions)} of {state.total_questions}
            </p>
            {state.current_question?.is_followup && (
              <p className="text-xs text-ink-400">Follow-up {state.current_question.followup_number} of 2</p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setTtsEnabled(!ttsEnabled)}
                disabled={!tts.isSupported}
                title={
                  !tts.isSupported
                    ? 'Reading questions aloud is not supported in this browser'
                    : ttsEnabled
                      ? 'Turn off reading questions aloud'
                      : 'Turn on reading questions aloud'
                }
              >
                {ttsEnabled && tts.isSupported ? <Volume2 className="size-4" /> : <VolumeX className="size-4" />}
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setSttEnabled(!sttEnabled)}
                disabled={!sttSupported}
                title={
                  !sttSupported
                    ? 'Voice input is not supported in this browser'
                    : sttEnabled
                      ? 'Turn off voice input'
                      : 'Turn on voice input'
                }
              >
                <Mic className={sttEnabled && sttSupported ? 'size-4' : 'size-4 text-ink-400'} />
              </Button>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => (camera.isActive ? camera.stop() : void camera.start())}
                title={camera.error ?? (camera.isActive ? 'Turn off camera preview' : 'Turn on camera preview')}
              >
                {camera.isActive ? <Video className="size-4" /> : <VideoOff className="size-4" />}
              </Button>
            </div>
            <ConnectionIndicator status={connectionStatus} />
          </div>
        </div>
        <Progress value={history.length} max={state.total_questions} />
        <p className="text-xs text-ink-400">
          ${state.total_cost_usd.toFixed(3)} / ${state.cost_cap_usd.toFixed(2)} used
        </p>
        {blocker.state === 'blocked' && (
          <Card className="border-l-4 border-l-warning-600">
            <CardHeader>
              <CardTitle>Leave interview?</CardTitle>
              <CardDescription>
                If you leave now, this session will be marked abandoned after a period of inactivity.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Button variant="outline" onClick={() => blocker.reset()}>
                Stay
              </Button>
              <Button onClick={() => blocker.proceed()}>Leave</Button>
            </CardContent>
          </Card>
        )}
      </header>

      <div className="flex flex-col gap-6 px-6 py-6 lg:flex-row lg:items-start">
        <section className="flex flex-col gap-4 lg:min-w-0 lg:flex-1">
          {currentTopicTurns.length > 0 && (
            <div className="flex flex-col gap-3 border-l-2 border-l-ink-200 pl-4">
              {currentTopicTurns.map((turn) => (
                <div key={turn.turn_index} className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    {turn.is_followup && <Badge variant="outline">Follow-up</Badge>}
                    <p className="text-sm font-medium text-ink-900">{turn.question_text}</p>
                  </div>
                  <p className="text-sm text-ink-600">{turn.answer_text}</p>
                  {turn.evaluation && <ScoreRow evaluation={turn.evaluation} />}
                </div>
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
                {acknowledgment && <p className="text-sm font-medium text-success-700">{acknowledgment}</p>}
                <p className="text-sm text-ink-900">{displayedQuestionText}</p>

                <div className="flex flex-col gap-2 border-l-2 border-l-ink-200 pl-4">
                  <Label className="text-xs text-ink-600">
                    Need clarification on this question? This isn't part of your evaluation.
                  </Label>

                  {clarifications.map((c, i) => (
                    <div key={i} className="flex flex-col gap-0.5">
                      <p className="text-xs font-medium text-ink-600">You asked: {c.question}</p>
                      <p className={c.declined ? 'text-xs text-warning-700' : 'text-xs text-ink-400'}>
                        {i === clarifications.length - 1 ? displayedClarificationText : c.clarification_text}
                      </p>
                    </div>
                  ))}

                  {!clarificationsExhausted && (
                    <div className="flex flex-col gap-2">
                      <div className="flex gap-2">
                        <Input
                          value={clarificationQuestion}
                          onChange={(e) => setClarificationQuestion(e.target.value)}
                          placeholder="Ask about scope, terminology, etc."
                          className="text-sm"
                        />
                        {sttEnabled && sttSupported && (
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={toggleClarificationMic}
                            title={clarificationStt.isListening ? 'Stop voice input' : 'Ask by voice'}
                          >
                            <Mic
                              className={
                                clarificationStt.isListening ? 'size-4 animate-pulse text-accent-600' : 'size-4'
                              }
                            />
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            clarificationStt.stop()
                            askClarification(clarificationQuestion)
                            setClarificationQuestion('')
                          }}
                          disabled={
                            isAskingClarification || connectionStatus !== 'open' || !clarificationQuestion.trim()
                          }
                        >
                          {isAskingClarification ? 'Asking…' : 'Ask for clarification'}
                        </Button>
                      </div>
                      {clarificationStt.isListening && <ListeningIndicator />}
                      {clarificationStt.error && (
                        <p className="text-xs text-warning-700">{clarificationStt.error}</p>
                      )}
                    </div>
                  )}
                  {clarificationError && <p className="text-xs text-danger-600">{clarificationError}</p>}
                </div>

                <div className="flex flex-col gap-2">
                  <div className="flex items-start gap-2">
                    <Textarea
                      value={answerText}
                      onChange={(e) => setAnswerText(e.target.value)}
                      placeholder="Type your answer..."
                      rows={6}
                      className="flex-1"
                    />
                    {sttEnabled && sttSupported && (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={toggleAnswerMic}
                        title={answerStt.isListening ? 'Stop voice input' : 'Answer by voice'}
                      >
                        <Mic className={answerStt.isListening ? 'size-4 animate-pulse text-accent-600' : 'size-4'} />
                      </Button>
                    )}
                  </div>
                  {answerStt.isListening && <ListeningIndicator />}
                  {answerStt.error && <p className="text-xs text-warning-700">{answerStt.error}</p>}
                </div>

                {submitError && <p className="text-sm text-danger-600">{submitError}</p>}
                <Button
                  onClick={() => {
                    answerStt.stop()
                    submitAnswer(answerText)
                  }}
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
        </section>

        <aside className="flex flex-col gap-3 lg:w-[380px] lg:shrink-0">
          <p className="text-sm font-medium text-ink-900">Completed topics</p>
          <div className="flex max-h-[32rem] flex-col gap-3 overflow-y-auto">
            {isHistoryLoading && <p className="text-xs text-ink-400">Loading history...</p>}
            {completedTopics.length === 0 && !isHistoryLoading && (
              <p className="text-xs text-ink-400">Nothing completed yet.</p>
            )}
            {completedTopics.map((group) => (
              <CompletedTopicCard key={group.topicNumber} topicNumber={group.topicNumber} turns={group.turns} />
            ))}
          </div>
        </aside>
      </div>
    </div>
  )
}
