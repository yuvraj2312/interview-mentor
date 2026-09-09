import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const badgeVariants = cva('inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium', {
  variants: {
    variant: {
      default: 'bg-slate-100 text-slate-700',
      outline: 'border border-slate-200 text-slate-600',
      good: 'bg-green-50 text-green-700',
      warning: 'bg-amber-50 text-amber-700',
      critical: 'bg-red-50 text-red-700',
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
