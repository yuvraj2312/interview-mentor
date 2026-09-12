import { useCallback, useEffect, useRef, useState } from 'react'

interface UseSpeechSynthesisResult {
  isSupported: boolean
  isSpeaking: boolean
  speak: (text: string, onBoundaryCharIndex?: (charIndex: number) => void) => void
  cancel: () => void
}

const isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window

/**
 * Thin wrapper around the browser's SpeechSynthesis API. Sentence-splitting
 * and reveal-count state live with the caller (LiveInterview.tsx) - this hook
 * only reports raw utterance boundary char-index progress.
 */
export function useSpeechSynthesis(): UseSpeechSynthesisResult {
  const [isSpeaking, setIsSpeaking] = useState(false)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)

  const cancel = useCallback(() => {
    if (!isSupported) return
    window.speechSynthesis.cancel()
    utteranceRef.current = null
    setIsSpeaking(false)
  }, [])

  const speak = useCallback((text: string, onBoundaryCharIndex?: (charIndex: number) => void) => {
    if (!isSupported) return
    // Always cancel any in-flight utterance first - covers question-change
    // interruptions cleanly.
    window.speechSynthesis.cancel()

    const utterance = new SpeechSynthesisUtterance(text)
    utteranceRef.current = utterance

    utterance.onstart = () => setIsSpeaking(true)
    utterance.onboundary = (event) => {
      onBoundaryCharIndex?.(event.charIndex)
    }
    utterance.onend = () => {
      // Safety net: charIndex tracking can undershoot on trailing punctuation.
      onBoundaryCharIndex?.(text.length)
      setIsSpeaking(false)
    }
    utterance.onerror = () => {
      onBoundaryCharIndex?.(text.length)
      setIsSpeaking(false)
    }

    window.speechSynthesis.speak(utterance)
  }, [])

  useEffect(() => {
    return () => {
      if (isSupported) window.speechSynthesis.cancel()
    }
  }, [])

  return { isSupported, isSpeaking, speak, cancel }
}
