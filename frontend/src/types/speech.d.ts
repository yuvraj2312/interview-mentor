// Ambient declarations for the parts of the Web Speech API's SpeechRecognition
// family missing from TypeScript's bundled DOM lib. As of TypeScript 6,
// lib.dom.d.ts already includes SpeechRecognitionEvent/ErrorEvent/Result(List)/
// Alternative and SpeechRecognitionErrorCode - only the recognizer interface
// itself and its Window bindings are still absent, so only those are added here.
// SpeechSynthesis/SpeechSynthesisUtterance (including boundary/charIndex) are
// already fully covered by the DOM lib - no augmentation needed for TTS.

export {}

declare global {
  interface SpeechRecognition extends EventTarget {
    continuous: boolean
    interimResults: boolean
    lang: string
    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null
    onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null
    onend: ((this: SpeechRecognition, ev: Event) => void) | null
    onstart: ((this: SpeechRecognition, ev: Event) => void) | null
    start(): void
    stop(): void
    abort(): void
  }

  interface SpeechRecognitionConstructor {
    new (): SpeechRecognition
  }

  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor
    webkitSpeechRecognition?: SpeechRecognitionConstructor
  }
}
