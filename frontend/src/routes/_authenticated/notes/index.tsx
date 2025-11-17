import { createFileRoute } from '@tanstack/react-router'
import { Notes } from '@/features/notes'

export const Route = createFileRoute('/_authenticated/notes/')({
  component: Notes,
})
