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
  session_id: string
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
  derived_stats?: DerivedStats | null
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

export interface UpgradeSearchRequest {
  session_id: string
  item_slot: string
  max_price_chaos?: number | null
  min_life?: number | null
  min_resistance?: number | null
  stat_weights?: Record<string, number> | null
  limit?: number
}

export interface UpgradeResult {
  trade_id: string
  name: string
  base_type: string
  rarity: string
  price_chaos: number
  stats: Record<string, number>
  improvements: Record<string, number>
  upgrade_score: number
  value_score: number | null
  trade_url: string
  whisper: string
}

export interface UpgradeSearchResponse {
  session_id: string
  game: Game
  item_slot: string
  current_item: {
    name?: string
    base_type: string
    stats: Record<string, number>
  }
  upgrades: UpgradeResult[]
  total_results: number
  query_time_ms: number
}

export interface DerivedStats {
  life?: number
  es?: number
  eva?: number
  armour?: number
  dps?: number
  ehp?: number
  res?: {
    fire?: number
    cold?: number
    lightning?: number
    chaos?: number
  }
}
