import { z } from 'zod'

export const noteSchema = z.object({
  id: z.string(),
  title: z.string(),
  content: z.string().nullable(),
  game_context: z.enum(['poe1', 'poe2']),
  created_at: z.string(),
  updated_at: z.string(),
})

export type Note = z.infer<typeof noteSchema>
