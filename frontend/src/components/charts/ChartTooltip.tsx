interface TooltipPayloadEntry {
  dataKey?: string | number
  name?: string
  value?: number | string
  color?: string
}

interface ChartTooltipProps {
  active?: boolean
  label?: string | number
  payload?: TooltipPayloadEntry[]
}

export function ChartTooltip({ active, label, payload }: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null

  return (
    <div className="rounded-md border border-slate-200 bg-white px-3 py-2 shadow-sm">
      {label !== undefined && <p className="mb-1 text-xs font-medium text-slate-500">{label}</p>}
      <div className="flex flex-col gap-1">
        {payload.map((entry) => (
          <div key={String(entry.dataKey)} className="flex items-center gap-2 text-xs">
            <span className="inline-block h-0.5 w-3 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="font-semibold text-slate-900">
              {typeof entry.value === 'number' ? entry.value.toFixed(1) : entry.value}
            </span>
            <span className="text-slate-500">{entry.name}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
