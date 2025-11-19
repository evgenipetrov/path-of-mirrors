/**
 * Types for PoB parsing and upgrade finding features.
 * These mirror the backend Pydantic schemas.
 */

export type Game = 'poe1' | 'poe2'

export interface PoBParseRequest {
  pob_xml?: string
  pob_code?: string
  game: Game
}

export interface PoBParseResponse {
  game: Game
  name: string
  character_class: string
  level: number
  ascendancy?: string | null
  league?: string | null
  life?: number | null
  energy_shield?: number | null
  mana?: number | null
  armour?: number | null
  evasion?: number | null
  items?: Record<string, ItemData> | null
  passive_tree?: Record<string, unknown> | null
  skills?: Array<Record<string, unknown>> | null
  source: string
}

export interface ItemData {
  name?: string | null
  base_type: string
  rarity: string
  explicit_mods: string[]
  implicit_mods: string[]
  properties: Record<string, string>
  sockets?: string
  corrupted?: boolean
  unique_id?: string
}
