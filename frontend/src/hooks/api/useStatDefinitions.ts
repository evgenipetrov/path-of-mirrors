/**
 * Hook for fetching canonical stat definitions from the backend.
 *
 * This hook provides the single source of truth for valid stat names,
 * categories, and default weights. Use this to populate stat selection UIs
 * and ensure consistency between frontend and backend.
 */

import { useQuery } from '@tanstack/react-query'
import { AXIOS_INSTANCE } from '@/lib/api-client'

export type StatCategory = 'defense' | 'resistance' | 'attribute' | 'damage' | 'utility'

export type Game = 'poe1' | 'poe2'

export interface StatDefinition {
  key: string
  display_name: string
  category: StatCategory
  default_weight: number
}

export interface StatDefinitionsResponse {
  game: Game
  stats: StatDefinition[]
}

/**
 * Fetch canonical stat definitions for a specific game.
 *
 * @param game - Game context ('poe1' or 'poe2')
 * @returns Query result with stat definitions
 */
export function useStatDefinitions(game: Game) {
  return useQuery<StatDefinitionsResponse>({
    queryKey: ['stat-definitions', game],
    queryFn: async () => {
      const response = await AXIOS_INSTANCE.get<StatDefinitionsResponse>(`/api/v1/builds/stats/${game}`)
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes - stat definitions rarely change
    gcTime: 30 * 60 * 1000, // 30 minutes
  })
}
