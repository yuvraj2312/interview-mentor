import { useCallback, useEffect, useRef, useState } from 'react'

interface UseCameraPreviewResult {
  stream: MediaStream | null
  isActive: boolean
  error: string | null
  start: () => Promise<void>
  stop: () => void
}

function stopTracks(stream: MediaStream | null) {
  stream?.getTracks().forEach((track) => track.stop())
}

/**
 * Client-side-only camera self-view. Video only, no audio track (speech
 * capture is handled independently by useSpeechRecognition). The returned
 * MediaStream is only ever assigned to a <video> element's srcObject or
 * stopped - it is never passed to fetch/FormData/WebSocket.send/MediaRecorder.
 */
export function useCameraPreview(): UseCameraPreviewResult {
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [error, setError] = useState<string | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  // Bumped by stop() and on unmount. getUserMedia() is async, so a start()
  // call can still be in flight when stop()/unmount happens (e.g. React
  // StrictMode's dev-only double-invoke: mount -> synthetic unmount, before
  // the permission prompt/device handshake has even resolved -> mount again).
  // Without this guard, that in-flight call resolves afterward and stores a
  // brand-new MediaStream that nothing can ever call stop() on again - the
  // camera hardware stays active (indicator light on) with no UI reference
  // to it at all. Comparing the generation captured at call time against the
  // current one when the promise resolves detects exactly this and releases
  // the now-orphaned stream immediately instead of leaking it.
  const generationRef = useRef(0)

  const stop = useCallback(() => {
    generationRef.current += 1
    stopTracks(streamRef.current)
    streamRef.current = null
    setStream(null)
  }, [])

  const start = useCallback(async () => {
    if (typeof navigator === 'undefined' || !navigator.mediaDevices?.getUserMedia) {
      setError('Camera access is not supported in this browser.')
      return
    }
    setError(null)
    const generation = ++generationRef.current
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      if (generation !== generationRef.current) {
        // Superseded by a stop()/unmount (or another start()) while this
        // call was in flight - release it instead of leaking an active camera.
        stopTracks(mediaStream)
        return
      }
      streamRef.current = mediaStream
      setStream(mediaStream)
    } catch {
      setError('Camera access was denied or unavailable. You can still continue without it.')
    }
  }, [])

  useEffect(() => {
    return () => {
      generationRef.current += 1
      stopTracks(streamRef.current)
      streamRef.current = null
    }
  }, [])

  return { stream, isActive: stream !== null, error, start, stop }
}
