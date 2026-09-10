import { Badge } from '@/components/ui/badge'

const STATUS_CONFIG: Record<string, { label: string; variant: 'good' | 'critical' | 'default' }> = {
  ready: { label: 'Ready', variant: 'good' },
  failed: { label: 'Failed', variant: 'critical' },
  uploaded: { label: 'Processing…', variant: 'default' },
  parsing: { label: 'Processing…', variant: 'default' },
  analyzing: { label: 'Processing…', variant: 'default' },
  pending: { label: 'Processing…', variant: 'default' },
}

export function ResourceStatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] ?? { label: status, variant: 'default' as const }
  return <Badge variant={config.variant}>{config.label}</Badge>
}
