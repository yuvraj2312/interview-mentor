import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { InterviewPlanFormat } from '@/lib/api'

const FORMAT_OPTIONS: { value: InterviewPlanFormat; label: string; description: string }[] = [
  { value: 'quick', label: 'Quick', description: '5 questions - a fast gut-check' },
  { value: 'standard', label: 'Standard', description: '8 questions - a typical full session' },
  { value: 'thorough', label: 'Thorough', description: '12 questions - deep coverage of the role' },
]

interface FormatStepProps {
  format: InterviewPlanFormat
  onFormatChange: (format: InterviewPlanFormat) => void
  onGenerate: () => void
  isGenerating: boolean
  isError: boolean
}

export function FormatStep({ format, onFormatChange, onGenerate, isGenerating, isError }: FormatStepProps) {
  return (
    <Card>
      <CardContent className="flex flex-col gap-4 pt-6">
        <div role="radiogroup" aria-label="Interview format" className="flex flex-col gap-3">
          {FORMAT_OPTIONS.map((option) => {
            const isSelected = format === option.value
            return (
              <button
                key={option.value}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => onFormatChange(option.value)}
                className={cn(
                  'flex cursor-pointer flex-col rounded-md border px-4 py-3 text-left transition-colors',
                  isSelected ? 'border-accent-500 bg-accent-50' : 'border-border hover:border-border-strong',
                )}
              >
                <span className="flex items-center gap-2.5">
                  <span
                    className={cn(
                      'flex size-4 shrink-0 items-center justify-center rounded-full border-2',
                      isSelected ? 'border-accent-500' : 'border-border-strong',
                    )}
                  >
                    {isSelected && <span className="size-2 rounded-full bg-accent-500" />}
                  </span>
                  <span className="text-sm font-medium text-ink-900">{option.label}</span>
                </span>
                <span className="ml-[26px] text-xs text-ink-400">{option.description}</span>
              </button>
            )
          })}
        </div>

        {isError && <p className="text-sm text-danger-600">Plan generation failed. Please try again.</p>}

        <Button onClick={onGenerate} disabled={isGenerating} className="w-fit">
          {isGenerating ? 'Generating plan...' : 'Generate plan'}
        </Button>
      </CardContent>
    </Card>
  )
}
