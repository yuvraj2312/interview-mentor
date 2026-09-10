interface LegendPayloadEntry {
  value?: string
  color?: string
}

interface ChartLegendProps {
  payload?: LegendPayloadEntry[]
}

export function ChartLegend({ payload }: ChartLegendProps) {
  if (!payload || payload.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-4 text-xs text-ink-600">
      {payload.map((entry) => (
        <div key={entry.value} className="flex items-center gap-1.5">
          <span className="inline-block size-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
          <span>{entry.value}</span>
        </div>
      ))}
    </div>
  )
}
