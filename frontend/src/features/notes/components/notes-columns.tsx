import { ColumnDef } from '@tanstack/react-table'
import { Pencil, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DataTableColumnHeader } from '@/components/data-table/column-header'
import type { Note } from '../data/schema'

export const createNotesColumns = (
  onEdit: (note: Note) => void,
  onDelete: (noteId: string) => void
): ColumnDef<Note>[] => [
  {
    accessorKey: 'title',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Title" />,
    cell: ({ row }) => (
      <button
        onClick={() => onEdit(row.original)}
        className="font-medium hover:underline text-left"
      >
        {row.getValue('title')}
      </button>
    ),
  },
  {
    accessorKey: 'content',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Content" />,
    cell: ({ row }) => {
      const content = row.getValue('content') as string | null
      if (!content) return <span className="text-muted-foreground italic">No content</span>
      return (
        <span className="text-muted-foreground max-w-md truncate block">
          {content.length > 100 ? `${content.substring(0, 100)}...` : content}
        </span>
      )
    },
  },
  {
    accessorKey: 'game_context',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Game" />,
    cell: ({ row }) => {
      const gameContext = row.getValue('game_context') as string
      return (
        <span
          className={`px-2 py-1 rounded text-xs font-semibold ${
            gameContext === 'poe1'
              ? 'bg-blue-500/10 text-blue-500'
              : 'bg-purple-500/10 text-purple-500'
          }`}
        >
          {gameContext.toUpperCase()}
        </span>
      )
    },
  },
  {
    accessorKey: 'created_at',
    header: ({ column }) => <DataTableColumnHeader column={column} title="Created" />,
    cell: ({ row }) => {
      const date = new Date(row.getValue('created_at'))
      return <span className="text-muted-foreground text-sm">{date.toLocaleDateString()}</span>
    },
  },
  {
    id: 'actions',
    header: 'Actions',
    cell: ({ row }) => (
      <div className="flex gap-2">
        <Button variant="ghost" size="sm" onClick={() => onEdit(row.original)}>
          <Pencil className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete(row.original.id)}
          className="text-destructive hover:text-destructive"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    ),
  },
]
