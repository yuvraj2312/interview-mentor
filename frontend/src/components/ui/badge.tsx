import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const badgeVariants = cva('inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium', {
  variants: {
    variant: {
      default: 'bg-ink-100 text-ink-700',
      outline: 'border border-border text-ink-600',
      good: 'bg-success-50 text-success-700',
      warning: 'bg-warning-50 text-warning-700',
      critical: 'bg-danger-50 text-danger-700',
    },
  },
  defaultVariants: {
    variant: 'default',
  },
})

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant, className }))} {...props} />
}

export { Badge, badgeVariants }
