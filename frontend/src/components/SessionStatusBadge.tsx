import { Badge } from '@/components/ui/badge'

const STATUS_BADGE: Record<string, { label: string; variant: 'good' | 'critical' | 'default' }> = {
  complete: { label: 'Complete', variant: 'good' },
  abandoned: { label: 'Abandoned', variant: 'critical' },
  planned: { label: 'Planned', variant: 'default' },
  in_progress: { label: 'In progress', variant: 'default' },
  evaluating: { label: 'In progress', variant: 'default' },
  advancing: { label: 'In progress', variant: 'default' },
}

export function SessionStatusBadge({ status }: { status: string }) {
  const config = STATUS_BADGE[status] ?? { label: status, variant: 'default' as const }
  return <Badge variant={config.variant}>{config.label}</Badge>
}
