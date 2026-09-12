import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Camera, Mic } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { CameraPreviewTile } from '@/components/voice/CameraPreviewTile'
import { useCameraPreview } from '@/hooks/useCameraPreview'
import { useMicLevelMeter } from '@/hooks/useMicLevelMeter'
import { useSpeechRecognition } from '@/hooks/useSpeechRecognition'
import { useSpeechSynthesis } from '@/hooks/useSpeechSynthesis'
import { useInterviewPreferencesStore } from '@/store/interviewPreferencesStore'

export function PreSessionCheckPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()

  const camera = useCameraPreview()
  const mic = useMicLevelMeter()
  const stt = useSpeechRecognition()
  const tts = useSpeechSynthesis()

  const hasSeenCameraNotice = useInterviewPreferencesStore((s) => s.hasSeenCameraNotice)
  const markCameraNoticeSeen = useInterviewPreferencesStore((s) => s.markCameraNoticeSeen)
  const hasCheckedSession = useInterviewPreferencesStore((s) => s.hasCheckedSession)
  const markSessionChecked = useInterviewPreferencesStore((s) => s.markSessionChecked)

  const alreadyChecked = Boolean(sessionId && hasCheckedSession(sessionId))

  // The check screen is a one-time gate before a session starts. If this
  // session has already passed it (e.g. the user left mid-interview and the
  // browser back button landed here again), skip straight back to the live
  // session instead of re-showing the camera/mic setup UI. `replace: true`
  // also drops this page from the history stack so a further back-press
  // can't land here either.
  useEffect(() => {
    if (alreadyChecked && sessionId) {
      navigate(`/interview-sessions/${sessionId}/live`, { replace: true })
    }
  }, [alreadyChecked, sessionId, navigate])

  function handleContinue() {
    if (sessionId) markSessionChecked(sessionId)
    camera.stop()
    mic.stop()
    navigate(`/interview-sessions/${sessionId}/live`, { replace: true })
  }

  if (alreadyChecked) return null

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 px-6 py-16">
      <div>
        <h1 className="text-2xl font-semibold text-ink-900">Check your camera &amp; mic</h1>
        <p className="mt-1 text-sm text-ink-400">
          Make sure everything works before you start. You can still type your answers even if you skip this.
        </p>
      </div>

      {camera.isActive && !hasSeenCameraNotice && (
        <Card className="border-l-4 border-l-accent-500">
          <CardContent className="flex flex-col gap-3 pt-6 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-ink-600">
              Your camera preview stays on your device - it's never recorded or transmitted anywhere.
            </p>
            <Button variant="outline" size="sm" className="w-fit" onClick={markCameraNoticeSeen}>
              Got it
            </Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Camera className="size-4" />
            Camera
          </CardTitle>
          <CardDescription>A self-view tile so you can confirm your camera works.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-start gap-4">
          <CameraPreviewTile stream={camera.stream} size="lg" />
          {camera.error && <p className="text-sm text-danger-600">{camera.error}</p>}
          <Button variant="outline" size="sm" onClick={camera.isActive ? camera.stop : camera.start}>
            {camera.isActive ? 'Stop camera' : 'Enable camera'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mic className="size-4" />
            Microphone
          </CardTitle>
          <CardDescription>Speak normally and confirm the level bar reacts.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-start gap-4">
          <Progress value={mic.level * 100} max={100} className="w-full max-w-xs" />
          {mic.error && <p className="text-sm text-danger-600">{mic.error}</p>}
          <Button variant="outline" size="sm" onClick={mic.isActive ? mic.stop : mic.start}>
            {mic.isActive ? 'Stop mic check' : 'Enable microphone'}
          </Button>
          {!stt.isSupported && (
            <p className="text-xs text-ink-400">
              Voice input (speech-to-text) isn't supported in this browser - try Chrome or Edge. You can still type
              your answers.
            </p>
          )}
          {!tts.isSupported && (
            <p className="text-xs text-ink-400">
              Reading questions aloud isn't supported in this browser. Questions will still display as text.
            </p>
          )}
        </CardContent>
      </Card>

      <Button onClick={handleContinue} className="w-fit">
        Continue to interview
      </Button>
    </main>
  )
}
