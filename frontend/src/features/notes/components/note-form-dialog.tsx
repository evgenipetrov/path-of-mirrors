import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import type { Note } from '../data/schema'
import type { NoteCreate } from '@/hooks/api'

interface NoteFormDialogProps {
  open: boolean
  note: Note | null
  gameContext: 'poe1' | 'poe2'
  onOpenChange: (open: boolean) => void
  onSubmit: (data: NoteCreate) => void
  isLoading: boolean
}

export function NoteFormDialog({
  open,
  note,
  gameContext,
  onOpenChange,
  onSubmit,
  isLoading,
}: NoteFormDialogProps) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      title,
      content: content || null,
    })
    // Reset form after submit
    setTitle('')
    setContent('')
  }

  const handleOpenChange = (newOpen: boolean) => {
    if (newOpen && note) {
      // Opening dialog with existing note - populate form
      setTitle(note.title)
      setContent(note.content || '')
    } else if (!newOpen) {
      // Closing dialog - reset form
      setTitle('')
      setContent('')
    }
    onOpenChange(newOpen)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>{note ? 'Edit Note' : 'Create New Note'}</DialogTitle>
            <DialogDescription>
              {note
                ? 'Update your note details below'
                : `Create a new note for ${gameContext.toUpperCase()}`}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title">
                Title <span className="text-destructive">*</span>
              </Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                maxLength={255}
                placeholder="Enter note title..."
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="content">Content</Label>
              <Textarea
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={6}
                placeholder="Enter note content..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => handleOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading || !title.trim()}>
              {isLoading ? 'Saving...' : note ? 'Update Note' : 'Create Note'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
