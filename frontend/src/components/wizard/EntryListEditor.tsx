import type { ReactNode } from 'react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'

interface EntryListEditorProps<T> {
  entries: T[]
  onChange: (entries: T[]) => void
  emptyEntry: T
  addLabel: string
  renderFields: (entry: T, onChange: (entry: T) => void) => ReactNode
}

// Shared add/remove/empty-state shell for experience/education/project
// editors - the mechanics are identical across all three, only the fields
// per entry differ.
export function EntryListEditor<T>({ entries, onChange, emptyEntry, addLabel, renderFields }: EntryListEditorProps<T>) {
  function updateEntry(index: number, entry: T) {
    onChange(entries.map((existing, i) => (i === index ? entry : existing)))
  }

  function removeEntry(index: number) {
    onChange(entries.filter((_, i) => i !== index))
  }

  function addEntry() {
    onChange([...entries, emptyEntry])
  }

  return (
    <div className="flex flex-col gap-3">
      {entries.map((entry, index) => (
        <Card key={index}>
          <CardContent className="flex flex-col gap-3 pt-6">
            {renderFields(entry, (updated) => updateEntry(index, updated))}
            <Button variant="outline" size="sm" onClick={() => removeEntry(index)} className="w-fit">
              Remove
            </Button>
          </CardContent>
        </Card>
      ))}
      <Button variant="outline" onClick={addEntry} className="w-fit">
        {addLabel}
      </Button>
    </div>
  )
}
