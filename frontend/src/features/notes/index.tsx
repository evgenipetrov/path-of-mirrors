import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Plus } from 'lucide-react'
import { useGameContext } from '@/hooks/useGameContext'
import {
  useListNotesApiNotesGet,
  useCreateNoteApiNotesPost,
  useUpdateNoteApiNotesNoteIdPut,
  useDeleteNoteApiNotesNoteIdDelete,
  type NoteCreate,
} from '@/hooks/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { NotesTable } from './components/notes-table'
import { createNotesColumns } from './components/notes-columns'
import { NoteFormDialog } from './components/note-form-dialog'
import type { Note } from './data/schema'

export function Notes() {
  const { game } = useGameContext()
  const queryClient = useQueryClient()
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [editingNote, setEditingNote] = useState<Note | null>(null)

  // Fetch notes for current game context
  const { data: notes = [], isLoading, error } = useListNotesApiNotesGet({ game })

  // Mutations with cache invalidation and toast notifications
  const createMutation = useCreateNoteApiNotesPost({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: ['listNotesApiNotesGet'] })
        toast.success('Note created successfully')
        setIsFormOpen(false)
      },
      onError: (error: any) => {
        toast.error(error?.response?.data?.detail?.[0]?.msg || 'Failed to create note')
      },
    },
  })

  const updateMutation = useUpdateNoteApiNotesNoteIdPut({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: ['listNotesApiNotesGet'] })
        toast.success('Note updated successfully')
        setEditingNote(null)
        setIsFormOpen(false)
      },
      onError: (error: any) => {
        toast.error(error?.response?.data?.detail?.[0]?.msg || 'Failed to update note')
      },
    },
  })

  const deleteMutation = useDeleteNoteApiNotesNoteIdDelete({
    mutation: {
      onSuccess: async () => {
        await queryClient.invalidateQueries({ queryKey: ['listNotesApiNotesGet'] })
        toast.success('Note deleted successfully')
      },
      onError: (error: any) => {
        toast.error(error?.response?.data?.detail?.[0]?.msg || 'Failed to delete note')
      },
    },
  })

  const handleCreate = () => {
    setEditingNote(null)
    setIsFormOpen(true)
  }

  const handleEdit = (note: Note) => {
    setEditingNote(note)
    setIsFormOpen(true)
  }

  const handleDelete = async (noteId: string) => {
    if (confirm('Are you sure you want to delete this note?')) {
      await deleteMutation.mutateAsync({ noteId })
    }
  }

  const handleSubmit = async (noteData: NoteCreate) => {
    if (editingNote) {
      await updateMutation.mutateAsync({ noteId: editingNote.id, data: noteData })
    } else {
      await createMutation.mutateAsync({ data: noteData })
    }
  }

  const columns = createNotesColumns(handleEdit, handleDelete)

  if (error) {
    return (
      <div className="p-8">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Notes</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">Failed to load notes. Please try again later.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Notes</h1>
            <p className="text-muted-foreground mt-1">
              Manage your notes for <span className="font-semibold">{game.toUpperCase()}</span>
            </p>
          </div>
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Create Note
          </Button>
        </div>

        {/* Notes Table */}
        <Card>
          <CardHeader>
            <CardTitle>Your Notes</CardTitle>
            <CardDescription>
              {isLoading ? 'Loading notes...' : `${notes.length} notes for ${game.toUpperCase()}`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : notes.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">
                  No notes yet. Create your first note to get started!
                </p>
              </div>
            ) : (
              <NotesTable columns={columns} data={notes} />
            )}
          </CardContent>
        </Card>

        {/* Note Form Dialog */}
        <NoteFormDialog
          open={isFormOpen}
          note={editingNote}
          gameContext={game}
          onOpenChange={setIsFormOpen}
          onSubmit={handleSubmit}
          isLoading={createMutation.isPending || updateMutation.isPending}
        />
      </div>
    </div>
  )
}
