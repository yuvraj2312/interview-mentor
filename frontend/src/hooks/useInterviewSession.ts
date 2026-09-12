import { useCallback, useEffect, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import {
  bootstrapSession,
  getInterviewSessionTranscript,
  interviewSessionWsUrl,
  startInterviewSession,
  type InterviewClarificationResultMessage,
  type InterviewQuestion,
  type InterviewServerMessage,
  type InterviewStateMessage,
  type InterviewTurnOut,
} from '@/lib/api'
import { useAuthStore } from '@/store/authStore'

export function useStartInterviewSession() {
  return useMutation({
    mutationFn: (planId: string) => startInterviewSession(planId),
  })
}

const MAX_RECONNECT_ATTEMPTS = 8
const RECONNECT_BASE_DELAY_MS = 1000
const RECONNECT_MAX_DELAY_MS = 15000

export type InterviewConnectionStatus = 'connecting' | 'open' | 'reconnecting' | 'closed_permanent'

export interface InterviewPermanentError {
  kind: 'auth' | 'not_found' | 'unknown'
  message: string
}

interface PendingAnswer {
  question: InterviewQuestion
  answerText: string
}

export function useInterviewSessionSocket(sessionId: string | undefined) {
  const [connectionStatus, setConnectionStatus] = useState<InterviewConnectionStatus>('connecting')
  const [permanentError, setPermanentError] = useState<InterviewPermanentError | null>(null)
  const [state, setState] = useState<InterviewStateMessage | null>(null)
  const [history, setHistory] = useState<InterviewTurnOut[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [clarifications, setClarifications] = useState<InterviewClarificationResultMessage[]>([])
  const [isAskingClarification, setIsAskingClarification] = useState(false)
  const [clarificationError, setClarificationError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const attemptRef = useRef(0)
  const authRetriedRef = useRef(false)
  const manualCloseRef = useRef(false)
  const pendingAnswerRef = useRef<PendingAnswer | null>(null)
  // Which action a still-unresolved {"type": "error", ...} reply belongs to -
  // the WS protocol has one shared error shape for both flows, so this is
  // what lets the fallback branch below attribute it to the right UI surface.
  const pendingActionRef = useRef<'answer' | 'clarify' | null>(null)
  const seededRef = useRef(false)

  const transcriptQuery = useQuery({
    queryKey: ['interview-session-transcript', sessionId],
    queryFn: () => getInterviewSessionTranscript(sessionId!),
    enabled: Boolean(sessionId),
    staleTime: Infinity,
  })

  useEffect(() => {
    if (transcriptQuery.data && !seededRef.current) {
      seededRef.current = true
      setHistory(transcriptQuery.data.turns.filter((turn) => turn.evaluation !== null))
    }
  }, [transcriptQuery.data])

  const connect = useCallback(() => {
    if (!sessionId) return

    const ws = new WebSocket(interviewSessionWsUrl(sessionId))
    wsRef.current = ws

    // Every handler below is scoped to this specific `ws` instance via
    // closure, but StrictMode's dev-only double-invoke (mount -> cleanup ->
    // mount again) means a socket created by the *first* invocation can be
    // superseded by a second one before it ever opens. When that first
    // socket's close event finally arrives (asynchronously - the browser
    // does not fire it synchronously from cleanup's .close() call), it can
    // land *after* the second effect run has already reset
    // manualCloseRef/attemptRef, so onclose's reconnect logic would
    // misread a stale/aborted socket's close as an unexpected drop of the
    // still-healthy current connection and schedule a redundant reconnect.
    // wsRef.current always points at the latest socket, so comparing
    // against it here is what actually answers "is this the connection we
    // still care about" - independent of ref-reset ordering.
    const isCurrent = () => wsRef.current === ws

    ws.onopen = () => {
      if (!isCurrent()) return
      const { accessToken } = useAuthStore.getState()
      ws.send(JSON.stringify({ type: 'auth', token: accessToken }))
    }

    ws.onmessage = (event) => {
      if (!isCurrent()) return
      let message: InterviewServerMessage
      try {
        message = JSON.parse(event.data)
      } catch {
        return
      }

      attemptRef.current = 0
      setConnectionStatus('open')

      if (message.type === 'state') {
        pendingAnswerRef.current = null
        pendingActionRef.current = null
        setIsSubmitting(false)
        setState(message)
        return
      }

      if (message.type === 'answer_result') {
        const pending = pendingAnswerRef.current
        if (pending) {
          const entry: InterviewTurnOut = {
            turn_index: pending.question.turn_index,
            topic: pending.question.topic,
            difficulty: pending.question.difficulty,
            question_text: pending.question.question_text,
            answer_text: pending.answerText,
            evaluation: message.evaluation,
            topic_number: pending.question.topic_number,
            is_followup: pending.question.is_followup,
            followup_reason: null,
          }
          setHistory((prev) => [...prev.filter((t) => t.turn_index !== entry.turn_index), entry])
        }
        pendingAnswerRef.current = null
        pendingActionRef.current = null
        setIsSubmitting(false)
        setSubmitError(null)
        setState((prev) =>
          prev
            ? {
                ...prev,
                status: message.status,
                current_question: message.next_question,
                turn_index: message.next_question ? message.next_question.turn_index : prev.turn_index + 1,
                topic_number: message.topic_number,
                summary: message.summary,
                total_cost_usd: message.total_cost_usd,
                cost_cap_usd: message.cost_cap_usd,
                stop_reason: message.stop_reason,
              }
            : prev,
        )
        return
      }

      if (message.type === 'clarification_result') {
        pendingActionRef.current = null
        setIsAskingClarification(false)
        setClarificationError(null)
        setClarifications((prev) => [...prev, message])
        return
      }

      // error message
      const failedAction = pendingActionRef.current
      pendingActionRef.current = null
      setIsSubmitting(false)
      setIsAskingClarification(false)
      pendingAnswerRef.current = null
      if (message.code !== 'already_complete' && message.code !== 'abandoned') {
        if (failedAction === 'clarify') {
          setClarificationError(message.detail)
        } else {
          setSubmitError(message.detail)
        }
      }
    }

    ws.onclose = (event) => {
      if (!isCurrent()) return
      if (manualCloseRef.current) return

      if (event.code === 1000) {
        // Server already told us why via the last message received; trust
        // state.status rather than reconnecting.
        return
      }

      if (event.code === 4401) {
        if (!authRetriedRef.current) {
          authRetriedRef.current = true
          setConnectionStatus('reconnecting')
          bootstrapSession().then((refreshed) => {
            if (refreshed) {
              connect()
            } else {
              setConnectionStatus('closed_permanent')
              setPermanentError({ kind: 'auth', message: 'Your session has expired. Please log in again.' })
            }
          })
        } else {
          setConnectionStatus('closed_permanent')
          setPermanentError({ kind: 'auth', message: 'Your session has expired. Please log in again.' })
        }
        return
      }

      if (event.code === 4404) {
        setConnectionStatus('closed_permanent')
        setPermanentError({ kind: 'not_found', message: 'This interview session was not found.' })
        return
      }

      if (attemptRef.current >= MAX_RECONNECT_ATTEMPTS) {
        setConnectionStatus('closed_permanent')
        setPermanentError({ kind: 'unknown', message: 'Lost connection to the interview.' })
        return
      }

      setConnectionStatus('reconnecting')
      const delay = Math.min(RECONNECT_BASE_DELAY_MS * 2 ** attemptRef.current, RECONNECT_MAX_DELAY_MS)
      attemptRef.current += 1
      reconnectTimerRef.current = setTimeout(connect, delay)
    }

    ws.onerror = () => {
      // No-op: onclose fires right after and handles reconnect logic.
    }
  }, [sessionId])

  useEffect(() => {
    if (!sessionId) return

    attemptRef.current = 0
    authRetriedRef.current = false
    manualCloseRef.current = false
    seededRef.current = false
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
    setConnectionStatus('connecting')
    setState(null)
    setPermanentError(null)
    setHistory([])
    setClarifications([])
    setIsAskingClarification(false)
    setClarificationError(null)
    pendingActionRef.current = null

    connect()

    return () => {
      manualCloseRef.current = true
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
      wsRef.current?.close(1000, 'component unmounting')
      wsRef.current = null
    }
  }, [sessionId, connect])

  // A new question always starts with an empty clarification sub-thread.
  useEffect(() => {
    setClarifications([])
    setClarificationError(null)
  }, [state?.current_question?.turn_index])

  const submitAnswer = useCallback(
    (text: string) => {
      if (connectionStatus !== 'open' || !state?.current_question || isSubmitting) return
      pendingAnswerRef.current = { question: state.current_question, answerText: text }
      pendingActionRef.current = 'answer'
      setIsSubmitting(true)
      setSubmitError(null)
      wsRef.current?.send(JSON.stringify({ type: 'answer', answer_text: text }))
    },
    [connectionStatus, state, isSubmitting],
  )

  const askClarification = useCallback(
    (question: string) => {
      if (connectionStatus !== 'open' || !state?.current_question || isAskingClarification) return
      pendingActionRef.current = 'clarify'
      setIsAskingClarification(true)
      setClarificationError(null)
      wsRef.current?.send(JSON.stringify({ type: 'clarify', question }))
    },
    [connectionStatus, state, isAskingClarification],
  )

  const reconnect = useCallback(() => {
    attemptRef.current = 0
    authRetriedRef.current = false
    manualCloseRef.current = false
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
    setPermanentError(null)
    setConnectionStatus('connecting')
    connect()
  }, [connect])

  return {
    connectionStatus,
    permanentError,
    state,
    history,
    isHistoryLoading: transcriptQuery.isLoading,
    isSubmitting,
    submitError,
    submitAnswer,
    clarifications,
    isAskingClarification,
    clarificationError,
    askClarification,
    reconnect,
  }
}
