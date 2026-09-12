import { useCallback, useEffect, useRef, useState } from 'react'

const SpeechRecognitionCtor: SpeechRecognitionConstructor | undefined =
  typeof window !== 'undefined' ? window.SpeechRecognition ?? window.webkitSpeechRecognition : undefined

// Pure feature detection, independent of any particular hook instance - lets
// callers (e.g. a master on/off toggle) check availability without needing
// to own one of the (possibly multiple, independent) recognizer instances.
export function isSpeechRecognitionSupported(): boolean {
  return !!SpeechRecognitionCtor
}

interface UseSpeechRecognitionResult {
  isSupported: boolean
  isListening: boolean
  transcript: string
  interimTranscript: string
  error: string | null
  start: () => void
  stop: () => void
  reset: () => void
}

/**
 * Thin wrapper around the browser's SpeechRecognition API. Never touches a
 * MediaStream directly - SpeechRecognition.start() triggers the browser's own
 * internal microphone access, entirely separate from getUserMedia.
 */
export function useSpeechRecognition(): UseSpeechRecognitionResult {
  const isSupported = isSpeechRecognitionSupported()

  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)

  const recognitionRef = useRef<SpeechRecognition | null>(null)
  // Tracks whether capture *should* be running. Chrome can silently end a
  // recognition session after a period of silence even with continuous:true;
  // a natural interview thinking-pause must not be mistaken for "done", so we
  // auto-restart in onend unless the user (or an unrecoverable error) stopped
  // this deliberately.
  const wantsListeningRef = useRef(false)

  const ensureRecognition = useCallback((): SpeechRecognition | null => {
    if (!SpeechRecognitionCtor) return null
    if (recognitionRef.current) return recognitionRef.current

    const recognition = new SpeechRecognitionCtor()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = typeof navigator !== 'undefined' ? navigator.language : 'en-US'

    recognition.onresult = (event) => {
      let finalChunk = ''
      let interimChunk = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const text = result[0]?.transcript ?? ''
        if (result.isFinal) {
          finalChunk += text
        } else {
          interimChunk += text
        }
      }
      if (finalChunk) {
        setTranscript((prev) => (prev ? `${prev} ${finalChunk}`.trim() : finalChunk.trim()))
      }
      setInterimTranscript(interimChunk)
    }

    recognition.onerror = (event) => {
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        wantsListeningRef.current = false
        setError('Microphone access was denied. You can still type your answer.')
        setIsListening(false)
        return
      }
      if (event.error === 'no-speech' || event.error === 'aborted') {
        // Not a real failure - onend's auto-restart logic handles resuming.
        return
      }
      setError('Speech recognition ran into a problem. You can still type your answer.')
    }

    recognition.onend = () => {
      if (wantsListeningRef.current) {
        try {
          recognition.start()
          return
        } catch {
          // Ignore - a start() called while already starting throws; the
          // browser will settle and the next onend will retry if needed.
        }
      }
      setIsListening(false)
    }

    recognition.onstart = () => {
      setIsListening(true)
    }

    recognitionRef.current = recognition
    return recognition
  }, [])

  const start = useCallback(() => {
    const recognition = ensureRecognition()
    if (!recognition) return
    setError(null)
    wantsListeningRef.current = true
    try {
      recognition.start()
    } catch {
      // Already started - ignore.
    }
  }, [ensureRecognition])

  const stop = useCallback(() => {
    wantsListeningRef.current = false
    recognitionRef.current?.stop()
  }, [])

  const reset = useCallback(() => {
    setTranscript('')
    setInterimTranscript('')
    setError(null)
  }, [])

  useEffect(() => {
    return () => {
      wantsListeningRef.current = false
      recognitionRef.current?.stop()
      recognitionRef.current = null
    }
  }, [])

  return { isSupported, isListening, transcript, interimTranscript, error, start, stop, reset }
}
