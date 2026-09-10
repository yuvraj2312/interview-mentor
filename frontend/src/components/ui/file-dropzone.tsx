import * as React from 'react'
import { FileText, UploadCloud, X } from 'lucide-react'

import { cn } from '@/lib/utils'

interface FileDropzoneProps {
  value: File | null
  onChange: (file: File | null) => void
  accept?: string
  hint?: string
  className?: string
}

function FileDropzone({ value, onChange, accept, hint, className }: FileDropzoneProps) {
  const inputRef = React.useRef<HTMLInputElement>(null)
  const [isDragActive, setIsDragActive] = React.useState(false)

  function handleFiles(files: FileList | null) {
    onChange(files?.[0] ?? null)
  }

  return (
    <div className={className}>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            inputRef.current?.click()
          }
        }}
        onDragOver={(event) => {
          event.preventDefault()
          setIsDragActive(true)
        }}
        onDragLeave={() => setIsDragActive(false)}
        onDrop={(event) => {
          event.preventDefault()
          setIsDragActive(false)
          handleFiles(event.dataTransfer.files)
        }}
        className={cn(
          'flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-border px-6 py-10 text-center transition-colors hover:border-border-strong hover:bg-surface-muted',
          isDragActive && 'border-accent-500 bg-accent-50',
        )}
      >
        <UploadCloud className={cn('size-8 text-ink-400', isDragActive && 'text-accent-500')} />
        <p className="text-sm font-medium text-ink-900">
          Drag and drop your file here, or <span className="text-accent-600">browse</span>
        </p>
        {hint && <p className="text-xs text-ink-400">{hint}</p>}
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={(event) => handleFiles(event.target.files)}
          className="sr-only"
        />
      </div>
      {value && (
        <div className="mt-3 flex items-center justify-between gap-2 rounded-md border border-border bg-surface-muted px-3 py-2">
          <div className="flex min-w-0 items-center gap-2">
            <FileText className="size-4 shrink-0 text-accent-600" />
            <span className="truncate text-sm text-ink-900">{value.name}</span>
          </div>
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation()
              onChange(null)
              if (inputRef.current) inputRef.current.value = ''
            }}
            className="shrink-0 rounded-sm p-1 text-ink-400 hover:bg-surface hover:text-ink-900"
            aria-label="Remove file"
          >
            <X className="size-4" />
          </button>
        </div>
      )}
    </div>
  )
}

export { FileDropzone }
