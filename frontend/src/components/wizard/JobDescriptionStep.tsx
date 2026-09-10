import { useEffect, useState } from 'react'

import { useJobDescriptions } from '@/hooks/useJobDescriptions'
import { useCreateJobDescription, useJobDescriptionQuery, useUpdateJobDescription } from '@/hooks/useJobDescription'
import { ResourceStatusBadge } from '@/components/ResourceStatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { isResourceReady } from '@/lib/resourceStatus'
import type { JobDescriptionOut } from '@/lib/api'

function LowConfidenceBadge({ field, flagged }: { field: string; flagged: string[] }) {
  const isFlagged = flagged.some((f) => f.startsWith(field))
  if (!isFlagged) return null
  return (
    <span className="ml-2 rounded-full bg-warning-50 px-2 py-0.5 text-xs font-medium text-warning-700">
      Please review
    </span>
  )
}

interface JobDescriptionStepProps {
  activeId: string | null
  onSelectExisting: (id: string) => void
  onCreated: (id: string) => void
  onContinue: (jd: JobDescriptionOut) => void
}

export function JobDescriptionStep({ activeId, onSelectExisting, onCreated, onContinue }: JobDescriptionStepProps) {
  const [mode, setMode] = useState<'choose' | 'paste'>('choose')
  const [rawText, setRawText] = useState('')

  const jdsQuery = useJobDescriptions()
  const activeJdQuery = useJobDescriptionQuery(activeId ?? undefined)
  const create = useCreateJobDescription()
  const update = useUpdateJobDescription(activeId ?? '')

  const [requiredText, setRequiredText] = useState('')
  const [preferredText, setPreferredText] = useState('')
  const [seniority, setSeniority] = useState('')
  const [isDirty, setIsDirty] = useState(false)

  useEffect(() => {
    const jd = activeJdQuery.data
    if (jd?.status === 'ready' && jd.structured_data) {
      const data = jd.structured_data as {
        required_skills?: string[]
        preferred_skills?: string[]
        seniority_level?: string
      }
      setRequiredText((data.required_skills ?? []).join(', '))
      setPreferredText((data.preferred_skills ?? []).join(', '))
      setSeniority(data.seniority_level ?? '')
      setIsDirty(false)
    }
  }, [activeJdQuery.data])

  async function handleCreate() {
    if (!rawText.trim()) return
    const jd = await create.mutateAsync(rawText)
    onCreated(jd.id)
  }

  async function handleContinue() {
    const jd = activeJdQuery.data
    if (!jd) return

    if (isDirty) {
      const updated = await update.mutateAsync({
        required_skills: requiredText
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        preferred_skills: preferredText
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        seniority_level: seniority,
      })
      onContinue(updated)
      return
    }

    onContinue(jd)
  }

  const flagged = activeJdQuery.data?.low_confidence_fields ?? []
  const activeIsReady = activeJdQuery.data ? isResourceReady(activeJdQuery.data.status) : false

  if (activeId) {
    return (
      <Card>
        <CardContent className="flex flex-col gap-6 pt-6">
          {activeJdQuery.isLoading && (
            <div className="flex flex-col gap-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          )}
          {!activeJdQuery.isLoading && !activeIsReady && activeJdQuery.data?.status !== 'failed' && (
            <div className="flex flex-col gap-3">
              <Skeleton className="h-10 w-full" />
              <p className="text-sm text-ink-400">Analyzing job description...</p>
            </div>
          )}

          {activeIsReady && activeJdQuery.data && (
            <>
              <div>
                <Label>
                  Required skills
                  <LowConfidenceBadge field="required_skills" flagged={flagged} />
                </Label>
                <Input
                  className="mt-1"
                  value={requiredText}
                  onChange={(e) => {
                    setRequiredText(e.target.value)
                    setIsDirty(true)
                  }}
                />
              </div>
              <div>
                <Label>
                  Preferred skills
                  <LowConfidenceBadge field="preferred_skills" flagged={flagged} />
                </Label>
                <Input
                  className="mt-1"
                  value={preferredText}
                  onChange={(e) => {
                    setPreferredText(e.target.value)
                    setIsDirty(true)
                  }}
                />
              </div>
              <div>
                <Label>
                  Seniority level
                  <LowConfidenceBadge field="seniority_level" flagged={flagged} />
                </Label>
                <Input
                  className="mt-1"
                  value={seniority}
                  onChange={(e) => {
                    setSeniority(e.target.value)
                    setIsDirty(true)
                  }}
                />
              </div>
              {update.isError && <p className="text-sm text-danger-600">Save failed. Please try again.</p>}
              <Button onClick={handleContinue} disabled={update.isPending} className="w-fit">
                {update.isPending ? 'Saving...' : 'Continue'}
              </Button>
            </>
          )}

          {activeJdQuery.data?.status === 'failed' && (
            <p className="text-sm text-danger-600">
              Analysis failed: {activeJdQuery.data.error_message}
            </p>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent className="flex flex-col gap-6 pt-6">
        {mode === 'choose' && (
          <>
            {jdsQuery.isLoading && (
              <div className="flex flex-col gap-2">
                <Skeleton className="h-14 w-full" />
                <Skeleton className="h-14 w-full" />
              </div>
            )}
            {jdsQuery.data && jdsQuery.data.length > 0 && (
              <div role="radiogroup" aria-label="Existing job descriptions" className="flex flex-col gap-2">
                {jdsQuery.data.map((jd) => {
                  const ready = isResourceReady(jd.status)
                  return (
                    <button
                      key={jd.id}
                      type="button"
                      role="radio"
                      aria-checked={false}
                      disabled={!ready}
                      onClick={() => onSelectExisting(jd.id)}
                      className={cn(
                        'flex items-center justify-between gap-4 rounded-md border border-border px-4 py-3 text-left transition-colors',
                        ready ? 'cursor-pointer hover:border-accent-500 hover:bg-accent-50' : 'cursor-not-allowed opacity-60',
                      )}
                    >
                      <span className="truncate text-sm text-ink-900">{jd.raw_text_preview}</span>
                      <ResourceStatusBadge status={jd.status} />
                    </button>
                  )
                })}
              </div>
            )}
            {jdsQuery.data && jdsQuery.data.length === 0 && (
              <p className="text-sm text-ink-400">You don't have any job descriptions yet.</p>
            )}
            <Button variant="outline" onClick={() => setMode('paste')} className="w-fit">
              Paste a new job description
            </Button>
          </>
        )}

        {mode === 'paste' && (
          <>
            <Textarea
              value={rawText}
              onChange={(event) => setRawText(event.target.value)}
              placeholder="Paste the full job description here..."
              rows={12}
            />
            {create.isError && <p className="text-sm text-danger-600">Analysis failed. Please try again.</p>}
            <div className="flex gap-3">
              <Button onClick={handleCreate} disabled={!rawText.trim() || create.isPending}>
                {create.isPending ? 'Analyzing...' : 'Analyze'}
              </Button>
              {jdsQuery.data && jdsQuery.data.length > 0 && (
                <Button variant="outline" onClick={() => setMode('choose')}>
                  Choose an existing one instead
                </Button>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
