import { Check } from 'lucide-react'

import { cn } from '@/lib/utils'

export interface WizardStepMeta {
  label: string
}

interface StepIndicatorProps {
  steps: WizardStepMeta[]
  currentStep: number
}

export function StepIndicator({ steps, currentStep }: StepIndicatorProps) {
  return (
    <ol className="flex items-start">
      {steps.map((step, index) => {
        const stepNumber = index + 1
        const isComplete = stepNumber < currentStep
        const isCurrent = stepNumber === currentStep
        const isLast = stepNumber === steps.length

        return (
          <li key={step.label} className={cn('flex items-center', !isLast && 'flex-1')}>
            <div className="flex flex-col items-center gap-1.5">
              <span
                className={cn(
                  'flex size-8 shrink-0 items-center justify-center rounded-full border-2 text-sm font-semibold transition-colors',
                  isComplete && 'border-success-600 bg-success-600 text-white',
                  isCurrent && 'border-accent-500 bg-accent-500 text-white',
                  !isComplete && !isCurrent && 'border-border-strong bg-surface text-ink-400',
                )}
              >
                {isComplete ? <Check className="size-4" /> : stepNumber}
              </span>
              <span
                className={cn(
                  'whitespace-nowrap text-xs font-medium',
                  isCurrent && 'text-ink-900',
                  isComplete && 'text-ink-600',
                  !isComplete && !isCurrent && 'text-ink-400',
                )}
              >
                {step.label}
              </span>
            </div>
            {!isLast && (
              <span
                className={cn('mx-2 mb-5 h-0.5 flex-1 rounded-full', isComplete ? 'bg-success-600' : 'bg-border')}
              />
            )}
          </li>
        )
      })}
    </ol>
  )
}
