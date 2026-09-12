import { useCallback, useEffect, useRef, useState } from 'react'

interface UseMicLevelMeterResult {
  level: number // normalized 0..1
  isActive: boolean
  error: string | null
  start: () => Promise<void>
  stop: () => void
}

const LEVEL_UPDATE_INTERVAL_MS = 100

/**
 * Check-screen-only microphone level meter. Independent of SpeechRecognition
 * (which manages its own mic access with no level data exposed) - this hook
 * requests its own getUserMedia({audio:true}) stream purely to visualize
 * input level via a Web Audio AnalyserNode. The stream is only ever read
 * locally; it is never sent anywhere.
 */
export function useMicLevelMeter(): UseMicLevelMeterResult {
  const [level, setLevel] = useState(0)
  const [isActive, setIsActive] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const streamRef = useRef<MediaStream | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const rafRef = useRef<number | null>(null)
  const lastUpdateRef = useRef(0)
  // See useCameraPreview's identical generation guard: getUserMedia() is
  // async, so stop()/unmount can happen before an in-flight start() resolves
  // (React StrictMode's dev double-invoke does exactly this). Without this
  // check, that call would still wire up a live mic stream nothing can stop.
  const generationRef = useRef(0)

  const stop = useCallback(() => {
    generationRef.current += 1
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
    streamRef.current?.getTracks().forEach((track) => track.stop())
    streamRef.current = null
    if (audioContextRef.current) {
      void audioContextRef.current.close()
      audioContextRef.current = null
    }
    setIsActive(false)
    setLevel(0)
  }, [])

  const start = useCallback(async () => {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      setError('Microphone access is not supported in this browser.')
      return
    }
    setError(null)
    const generation = ++generationRef.current
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      if (generation !== generationRef.current) {
        // Superseded while the permission prompt/device handshake was in
        // flight - release it instead of leaking an active microphone.
        stream.getTracks().forEach((track) => track.stop())
        return
      }
      streamRef.current = stream

      const audioContext = new AudioContext()
      audioContextRef.current = audioContext
      const source = audioContext.createMediaStreamSource(stream)
      const analyser = audioContext.createAnalyser()
      analyser.fftSize = 512
      source.connect(analyser)

      const data = new Uint8Array(analyser.frequencyBinCount)
      const tick = (timestamp: number) => {
        analyser.getByteTimeDomainData(data)
        if (timestamp - lastUpdateRef.current >= LEVEL_UPDATE_INTERVAL_MS) {
          lastUpdateRef.current = timestamp
          let sumSquares = 0
          for (let i = 0; i < data.length; i++) {
            const normalized = (data[i] - 128) / 128
            sumSquares += normalized * normalized
          }
          const rms = Math.sqrt(sumSquares / data.length)
          setLevel(Math.min(1, rms * 4))
        }
        rafRef.current = requestAnimationFrame(tick)
      }
      rafRef.current = requestAnimationFrame(tick)
      setIsActive(true)
    } catch {
      setError('Microphone access was denied or unavailable. You can still continue without it.')
    }
  }, [])

  useEffect(() => {
    return () => {
      generationRef.current += 1
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)
      streamRef.current?.getTracks().forEach((track) => track.stop())
      if (audioContextRef.current) void audioContextRef.current.close()
    }
  }, [])

  return { level, isActive, error, start, stop }
}
