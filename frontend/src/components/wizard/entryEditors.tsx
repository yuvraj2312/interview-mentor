import { useState } from 'react'

import { EntryListEditor } from '@/components/wizard/EntryListEditor'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  emptyEducationEntry,
  emptyExperienceEntry,
  emptyProjectEntry,
  type ResumeEducationEntry,
  type ResumeExperienceEntry,
  type ResumeProjectEntry,
} from '@/types/resume'

export function ExperienceEditor({
  entries,
  onChange,
}: {
  entries: ResumeExperienceEntry[]
  onChange: (entries: ResumeExperienceEntry[]) => void
}) {
  return (
    <EntryListEditor
      entries={entries}
      onChange={onChange}
      emptyEntry={emptyExperienceEntry}
      addLabel="Add experience"
      renderFields={(entry, update) => (
        <>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Title</Label>
              <Input className="mt-1" value={entry.title} onChange={(e) => update({ ...entry, title: e.target.value })} />
            </div>
            <div>
              <Label>Company</Label>
              <Input
                className="mt-1"
                value={entry.company}
                onChange={(e) => update({ ...entry, company: e.target.value })}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Start date</Label>
              <Input
                className="mt-1"
                value={entry.start_date}
                onChange={(e) => update({ ...entry, start_date: e.target.value })}
              />
            </div>
            <div>
              <Label>End date</Label>
              <Input
                className="mt-1"
                value={entry.end_date}
                onChange={(e) => update({ ...entry, end_date: e.target.value })}
                placeholder="Present"
              />
            </div>
          </div>
          <div>
            <Label>Description</Label>
            <Textarea
              className="mt-1"
              value={entry.description}
              onChange={(e) => update({ ...entry, description: e.target.value })}
            />
          </div>
        </>
      )}
    />
  )
}

export function EducationEditor({
  entries,
  onChange,
}: {
  entries: ResumeEducationEntry[]
  onChange: (entries: ResumeEducationEntry[]) => void
}) {
  return (
    <EntryListEditor
      entries={entries}
      onChange={onChange}
      emptyEntry={emptyEducationEntry}
      addLabel="Add education"
      renderFields={(entry, update) => (
        <>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Institution</Label>
              <Input
                className="mt-1"
                value={entry.institution}
                onChange={(e) => update({ ...entry, institution: e.target.value })}
              />
            </div>
            <div>
              <Label>Degree</Label>
              <Input className="mt-1" value={entry.degree} onChange={(e) => update({ ...entry, degree: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Field of study</Label>
              <Input
                className="mt-1"
                value={entry.field_of_study}
                onChange={(e) => update({ ...entry, field_of_study: e.target.value })}
              />
            </div>
            <div>
              <Label>Graduation date</Label>
              <Input
                className="mt-1"
                value={entry.graduation_date}
                onChange={(e) => update({ ...entry, graduation_date: e.target.value })}
              />
            </div>
          </div>
        </>
      )}
    />
  )
}

// Local text buffer, not derived from entry.technologies on every render:
// deriving it directly would strip a just-typed trailing comma/space
// (split -> filter(Boolean) removes the empty trailing segment) and yank
// it out from under the user mid-keystroke. Mirrors how the skills field
// elsewhere in this wizard is edited as free text and only split on save.
function TechnologiesInput({ value, onChange }: { value: string[]; onChange: (value: string[]) => void }) {
  const [text, setText] = useState(value.join(', '))
  return (
    <Input
      className="mt-1"
      value={text}
      onChange={(e) => {
        setText(e.target.value)
        onChange(
          e.target.value
            .split(',')
            .map((s) => s.trim())
            .filter(Boolean),
        )
      }}
      placeholder="React, TypeScript, PostgreSQL"
    />
  )
}

export function ProjectEditor({
  entries,
  onChange,
}: {
  entries: ResumeProjectEntry[]
  onChange: (entries: ResumeProjectEntry[]) => void
}) {
  return (
    <EntryListEditor
      entries={entries}
      onChange={onChange}
      emptyEntry={emptyProjectEntry}
      addLabel="Add project"
      renderFields={(entry, update) => (
        <>
          <div>
            <Label>Name</Label>
            <Input className="mt-1" value={entry.name} onChange={(e) => update({ ...entry, name: e.target.value })} />
          </div>
          <div>
            <Label>Description</Label>
            <Textarea
              className="mt-1"
              value={entry.description}
              onChange={(e) => update({ ...entry, description: e.target.value })}
            />
          </div>
          <div>
            <Label>Technologies</Label>
            <TechnologiesInput value={entry.technologies} onChange={(technologies) => update({ ...entry, technologies })} />
          </div>
        </>
      )}
    />
  )
}
