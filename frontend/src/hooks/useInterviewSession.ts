import { useCallback, useEffect, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import {
  bootstrapSession,
  getInterviewSessionTranscript,
  interviewSessionWsUrl,
  startInterviewSession,
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

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const attemptRef = useRef(0)
  const authRetriedRef = useRef(false)
  const manualCloseRef = useRef(false)
  const pendingAnswerRef = useRef<PendingAnswer | null>(null)
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

    ws.onopen = () => {
      const { accessToken } = useAuthStore.getState()
      ws.send(JSON.stringify({ type: 'auth', token: accessToken }))
    }

    ws.onmessage = (event) => {
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
          }
          setHistory((prev) => [...prev.filter((t) => t.turn_index !== entry.turn_index), entry])
        }
        pendingAnswerRef.current = null
        setIsSubmitting(false)
        setSubmitError(null)
        setState((prev) =>
          prev
            ? {
                ...prev,
                status: message.status,
                current_question: message.next_question,
                turn_index: message.next_question ? message.next_question.turn_index : prev.turn_index + 1,
                summary: message.summary,
              }
            : prev,
        )
        return
      }

      // error message
      setIsSubmitting(false)
      pendingAnswerRef.current = null
      if (message.code !== 'already_complete' && message.code !== 'abandoned') {
        setSubmitError(message.detail)
      }
    }

    ws.onclose = (event) => {
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

    connect()

    return () => {
      manualCloseRef.current = true
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current)
      wsRef.current?.close(1000, 'component unmounting')
      wsRef.current = null
    }
  }, [sessionId, connect])

  const submitAnswer = useCallback(
    (text: string) => {
      if (connectionStatus !== 'open' || !state?.current_question || isSubmitting) return
      pendingAnswerRef.current = { question: state.current_question, answerText: text }
      setIsSubmitting(true)
      setSubmitError(null)
      wsRef.current?.send(JSON.stringify({ type: 'answer', answer_text: text }))
    },
    [connectionStatus, state, isSubmitting],
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
    reconnect,
  }
}
