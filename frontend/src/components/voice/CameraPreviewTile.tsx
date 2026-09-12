import { useEffect, useRef } from 'react'
import { VideoOff } from 'lucide-react'

import { cn } from '@/lib/utils'

interface CameraPreviewTileProps {
  stream: MediaStream | null
  size: 'lg' | 'sm'
  className?: string
}

/**
 * Local self-view only. The stream is assigned directly to this <video>
 * element's srcObject and never leaves the browser - no WebSocket message,
 * no upload endpoint, no path to the backend.
 */
export function CameraPreviewTile({ stream, size, className }: CameraPreviewTileProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.srcObject = stream
    }
  }, [stream])

  return (
    <div
      className={cn(
        'flex items-center justify-center overflow-hidden rounded-lg border border-border bg-ink-900',
        size === 'lg' ? 'aspect-video w-full max-w-md' : 'aspect-video w-40',
        className,
      )}
    >
      {stream ? (
        <video ref={videoRef} autoPlay muted playsInline className="h-full w-full object-cover" />
      ) : (
        <VideoOff className={cn('text-ink-400', size === 'lg' ? 'size-8' : 'size-5')} />
      )}
    </div>
  )
}
