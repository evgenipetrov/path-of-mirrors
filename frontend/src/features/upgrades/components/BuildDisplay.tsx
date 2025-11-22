/**
 * Build Display Component
 *
 * Shows parsed Path of Building character information and items.
 */

import { useEffect, useRef, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { X, Pencil, RotateCcw, ChevronDown, ChevronUp, Plus } from 'lucide-react'
import { useGameContext } from '@/hooks/useGameContext'
import { useStatDefinitions } from '@/hooks/api/useStatDefinitions'
import type { PoBParseResponse, ItemData } from '../types'

interface BuildDisplayProps {
  build: PoBParseResponse
}

type StatWeight = {
  percentWeight: number
  flatWeight: number
  gainType: 'percent' | 'flat'
}

// Note: These keys match the backend's canonical stat keys from the analysis context
// We keep some frontend-specific stats that aren't in the backend yet (like armour, evasion, etc.)
const DEFAULT_WEIGHTS: Record<string, StatWeight> = {
  life: { percentWeight: 0.5, flatWeight: 2, gainType: 'percent' },
  energy_shield: { percentWeight: 0.5, flatWeight: 1, gainType: 'flat' },
  mana: { percentWeight: 0.5, flatWeight: 1, gainType: 'flat' },
  armour: { percentWeight: 0.3, flatWeight: 0.5, gainType: 'flat' },
  evasion: { percentWeight: 0.3, flatWeight: 0.5, gainType: 'flat' },
  block: { percentWeight: 0.5, flatWeight: 0.5, gainType: 'percent' },
  spell_block: { percentWeight: 0.5, flatWeight: 0.5, gainType: 'percent' },
  spell_suppression: { percentWeight: 0.5, flatWeight: 0.5, gainType: 'percent' },
  fire_res: { percentWeight: 5, flatWeight: 0.05, gainType: 'flat' },
  cold_res: { percentWeight: 5, flatWeight: 0.05, gainType: 'flat' },
  lightning_res: { percentWeight: 5, flatWeight: 0.05, gainType: 'flat' },
  chaos_res: { percentWeight: 5, flatWeight: 0.05, gainType: 'flat' },
  dps: { percentWeight: 3, flatWeight: 0.001, gainType: 'percent' },
  ehp: { percentWeight: 2, flatWeight: 0.001, gainType: 'percent' },
  movement_speed: { percentWeight: 1, flatWeight: 0.1, gainType: 'percent' },
  max_hit: { percentWeight: 1, flatWeight: 0.001, gainType: 'percent' },
}

export function BuildDisplay({ build }: BuildDisplayProps) {
  const itemCount = build.items ? Object.keys(build.items).length : 0

  const groupedItems = groupItemsByCategory(build.items ?? {})
  const derived = build.derived_stats

  // Fetch canonical stats from backend
  const { game } = useGameContext()
  const { data: statDefinitions, isLoading: isLoadingStats } = useStatDefinitions(game as 'poe1' | 'poe2')

  // Initialize weights with all canonical stats from backend
  const [weights, setWeights] = useState<Record<string, StatWeight>>(() => {
    if (!statDefinitions) return DEFAULT_WEIGHTS

    const allStats: Record<string, StatWeight> = {}
    statDefinitions.stats.forEach((stat) => {
      // Use existing DEFAULT_WEIGHTS if available, otherwise use backend's default
      allStats[stat.key] = DEFAULT_WEIGHTS[stat.key] ?? {
        percentWeight: stat.default_weight,
        flatWeight: stat.default_weight,
        gainType: 'percent' as const,
      }
    })
    return allStats
  })

  const [isAddStatDialogOpen, setIsAddStatDialogOpen] = useState(false)

  // Update weights when stat definitions load from backend
  useEffect(() => {
    if (statDefinitions) {
      const allStats: Record<string, StatWeight> = {}
      statDefinitions.stats.forEach((stat) => {
        // Use existing DEFAULT_WEIGHTS if available, otherwise use backend's default
        allStats[stat.key] = DEFAULT_WEIGHTS[stat.key] ?? {
          percentWeight: stat.default_weight,
          flatWeight: stat.default_weight,
          gainType: 'percent' as const,
        }
      })
      setWeights(allStats)
    }
  }, [statDefinitions])

  const storageKey = `build-name-${build.game}-${build.session_id}`
  const initialName =
    (typeof window !== 'undefined' && window.localStorage?.getItem(storageKey)) || build.name || 'Unnamed Build'
  const [customName, setCustomName] = useState(initialName)
  const [isEditingName, setIsEditingName] = useState(false)
  const nameInputRef = useRef<HTMLInputElement | null>(null)

  const handleNameChange = (value: string) => {
    setCustomName(value)
    if (typeof window !== 'undefined' && window.localStorage) {
      window.localStorage.setItem(storageKey, value)
    }
  }

  const startNameEdit = () => {
    setIsEditingName(true)
    requestAnimationFrame(() => {
      nameInputRef.current?.focus()
      nameInputRef.current?.select()
    })
  }

  const stopNameEdit = () => setIsEditingName(false)

  const formatAttributes = (attrs?: { str?: number; dex?: number; int?: number }) => {
    if (!attrs) return undefined
    const { str, dex, int } = attrs
    if ([str, dex, int].every((v) => v === undefined)) return undefined
    return `${str ?? '–'} / ${dex ?? '–'} / ${int ?? '–'}`
  }

  const toPercent = (value?: number) =>
    value === undefined ? undefined : `${Math.round(value >= 10 ? value : value * 100)}%`

  const getWeight = (key: string): StatWeight =>
    weights[key] ?? DEFAULT_WEIGHTS[key] ?? { percentWeight: 1, flatWeight: 1, gainType: 'percent' }

  const onWeightChange = (key: string, field: 'percentWeight' | 'flatWeight' | 'gainType', value: number | string) => {
    setWeights((prev) => ({
      ...prev,
      [key]: {
        ...getWeight(key),
        [field]: value,
      },
    }))
  }

  // Initialize hiddenStats to hide stats not in DEFAULT_WEIGHTS
  const [hiddenStats, setHiddenStats] = useState<Set<string>>(() => {
    if (!statDefinitions) return new Set()

    const hidden = new Set<string>()
    statDefinitions.stats.forEach((stat) => {
      // Hide stats that aren't in DEFAULT_WEIGHTS
      if (!DEFAULT_WEIGHTS[stat.key]) {
        hidden.add(stat.key)
      }
    })
    return hidden
  })

  const [isStatsCollapsed, setIsStatsCollapsed] = useState(false)

  // Update hidden stats when stat definitions load
  useEffect(() => {
    if (statDefinitions) {
      const hidden = new Set<string>()
      statDefinitions.stats.forEach((stat) => {
        // Hide stats that aren't in DEFAULT_WEIGHTS
        if (!DEFAULT_WEIGHTS[stat.key]) {
          hidden.add(stat.key)
        }
      })
      setHiddenStats(hidden)
    }
  }, [statDefinitions])

  const hideStat = (statKey: string) =>
    setHiddenStats((prev) => {
      const next = new Set(prev)
      next.add(statKey)
      return next
    })

  const isHidden = (statKey: string) => hiddenStats.has(statKey)

  const resetWeights = () => {
    // Reset weights to match DEFAULT_WEIGHTS values
    if (statDefinitions) {
      const allStats: Record<string, StatWeight> = {}
      statDefinitions.stats.forEach((stat) => {
        allStats[stat.key] = DEFAULT_WEIGHTS[stat.key] ?? {
          percentWeight: stat.default_weight,
          flatWeight: stat.default_weight,
          gainType: 'percent' as const,
        }
      })
      setWeights(allStats)
    }
    // Reset hidden stats to hide non-DEFAULT stats
    const hidden = new Set<string>()
    statDefinitions?.stats.forEach((stat) => {
      if (!DEFAULT_WEIGHTS[stat.key]) {
        hidden.add(stat.key)
      }
    })
    setHiddenStats(hidden)
  }

  const addStat = (statKey: string) => {
    // Just unhide the stat (it already exists in weights)
    setHiddenStats((prev) => {
      const next = new Set(prev)
      next.delete(statKey)
      return next
    })
    setIsAddStatDialogOpen(false)
  }

  // Get available stats (hidden stats that can be shown)
  const availableStats = statDefinitions?.stats.filter(
    (stat) => hiddenStats.has(stat.key)
  ) ?? []

  // Group available stats by category
  const statsByCategory = availableStats.reduce((acc, stat) => {
    if (!acc[stat.category]) {
      acc[stat.category] = []
    }
    acc[stat.category].push(stat)
    return acc
  }, {} as Record<string, typeof availableStats>)

  return (
    <div className="space-y-4">
      {/* Character Info Card */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <div className="relative flex-1 max-w-sm">
                <Input
                  aria-label="Build name"
                  ref={nameInputRef}
                  readOnly={!isEditingName}
                  className={`pr-10 text-lg font-semibold ${isEditingName ? '' : 'bg-muted'}`}
                  value={customName}
                  onChange={(e) => handleNameChange(e.target.value)}
                  onBlur={stopNameEdit}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label="Edit build name"
                  className="absolute inset-y-0 right-0 h-full"
                  onClick={startNameEdit}
                >
                  <Pencil className="size-4" />
                </Button>
              </div>
            </div>
            <CardDescription>
              Level {build.level} {build.ascendancy || build.character_class}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Character quick info - compact stats bar */}
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <Badge variant="secondary" className="font-medium">
              Class: {build.character_class}
            </Badge>
            {build.ascendancy && (
              <Badge variant="secondary" className="font-medium">
                Asc: {build.ascendancy}
              </Badge>
            )}
            <Badge variant="secondary" className="font-medium">
              Lv: {build.level}
            </Badge>
            {build.league && (
              <>
                <Separator orientation="vertical" className="h-4" />
                <Badge variant="outline" className="font-medium">
                  {build.league}
                </Badge>
              </>
            )}
            {derived?.attributes && (
              <>
                <Separator orientation="vertical" className="h-4" />
                <span className="text-muted-foreground font-medium">
                  {formatAttributes(derived.attributes)}
                </span>
                <span className="text-xs text-muted-foreground">Str/Dex/Int</span>
              </>
            )}
            {derived?.charges && (
              <>
                <Separator orientation="vertical" className="h-4" />
                <span className="text-muted-foreground font-medium">
                  {derived.charges.endurance ?? 0}/{derived.charges.frenzy ?? 0}/{derived.charges.power ?? 0}
                </span>
                <span className="text-xs text-muted-foreground">E/F/P</span>
              </>
            )}
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase text-muted-foreground">Build Statistics</p>
            <div className="flex gap-2">
              <Dialog open={isAddStatDialogOpen} onOpenChange={setIsAddStatDialogOpen}>
                <DialogTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8"
                    disabled={isLoadingStats || availableStats.length === 0}
                  >
                    <Plus className="size-4 mr-1" />
                    Add Stat
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-md max-h-[80vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Add Stat</DialogTitle>
                    <DialogDescription>
                      Select a stat to add to your weights table. These are canonical stats from the backend.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    {Object.entries(statsByCategory).map(([category, stats]) => (
                      <div key={category} className="space-y-2">
                        <h3 className="text-sm font-semibold capitalize text-muted-foreground">
                          {category}
                        </h3>
                        <div className="grid gap-2">
                          {stats.map((stat) => (
                            <Button
                              key={stat.key}
                              variant="outline"
                              className="justify-start h-auto py-2"
                              onClick={() => addStat(stat.key)}
                            >
                              <div className="flex flex-col items-start gap-1">
                                <span className="font-medium">{stat.display_name}</span>
                                <span className="text-xs text-muted-foreground">
                                  Default weight: {stat.default_weight}
                                </span>
                              </div>
                            </Button>
                          ))}
                        </div>
                      </div>
                    ))}
                    {availableStats.length === 0 && (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        All available stats have been added.
                      </p>
                    )}
                  </div>
                </DialogContent>
              </Dialog>
              <Button
                variant="outline"
                size="sm"
                onClick={resetWeights}
                className="h-8"
              >
                <RotateCcw className="size-4 mr-1" />
                Reset
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsStatsCollapsed(!isStatsCollapsed)}
                className="h-8"
              >
                {isStatsCollapsed ? (
                  <>
                    <ChevronDown className="size-4 mr-1" />
                    Expand
                  </>
                ) : (
                  <>
                    <ChevronUp className="size-4 mr-1" />
                    Collapse
                  </>
                )}
              </Button>
            </div>
          </div>

          {!isStatsCollapsed && (
            <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[180px] px-3">Stat</TableHead>
                <TableHead className="text-right w-[120px] px-3">Value</TableHead>
                <TableHead className="text-right w-[100px] px-3">% Weight</TableHead>
                <TableHead className="text-right w-[100px] px-3">Flat Weight</TableHead>
                <TableHead className="w-[120px] px-3">Gain</TableHead>
                <TableHead className="w-[50px] px-2"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {[
                isHidden('life') ? undefined : { label: 'Life', value: derived?.life ?? build.life, numericValue: derived?.life ?? build.life, accent: 'text-red-500', weightKey: 'life' },
                isHidden('energy_shield') ? undefined : { label: 'Energy Shield', value: derived?.es ?? build.energy_shield, numericValue: derived?.es ?? build.energy_shield, weightKey: 'energy_shield' },
                isHidden('mana') ? undefined : { label: 'Mana', value: derived?.mana ?? build.mana, numericValue: derived?.mana ?? build.mana, weightKey: 'mana' },
                isHidden('armour') ? undefined : { label: 'Armour', value: derived?.armour ?? build.armour, numericValue: derived?.armour ?? build.armour, weightKey: 'armour' },
                isHidden('evasion') ? undefined : { label: 'Evasion', value: derived?.eva ?? build.evasion, numericValue: derived?.eva ?? build.evasion, weightKey: 'evasion' },
                derived?.block?.attack !== undefined && !isHidden('block') ? { label: 'Block', value: toPercent(derived.block.attack), numericValue: derived.block.attack, weightKey: 'block' } : undefined,
                derived?.block?.spell !== undefined && !isHidden('spell_block') ? { label: 'Spell Block', value: toPercent(derived.block.spell), numericValue: derived.block.spell, weightKey: 'spell_block' } : undefined,
                derived?.block?.suppression !== undefined && !isHidden('spell_suppression')
                  ? { label: 'Spell Suppression', value: toPercent(derived.block.suppression), numericValue: derived.block.suppression, weightKey: 'spell_suppression' }
                  : undefined,
                derived?.res?.fire !== undefined && !isHidden('fire_res') ? { label: 'Fire Res', value: `${derived.res.fire}%`, numericValue: derived.res.fire, weightKey: 'fire_res' } : undefined,
                derived?.res?.cold !== undefined && !isHidden('cold_res') ? { label: 'Cold Res', value: `${derived.res.cold}%`, numericValue: derived.res.cold, weightKey: 'cold_res' } : undefined,
                derived?.res?.lightning !== undefined && !isHidden('lightning_res') ? { label: 'Lightning Res', value: `${derived.res.lightning}%`, numericValue: derived.res.lightning, weightKey: 'lightning_res' } : undefined,
                derived?.res?.chaos !== undefined && !isHidden('chaos_res') ? { label: 'Chaos Res', value: `${derived.res.chaos}%`, numericValue: derived.res.chaos, weightKey: 'chaos_res' } : undefined,
                isHidden('dps') ? undefined : { label: 'Total DPS', value: derived?.dps, numericValue: derived?.dps, weightKey: 'dps' },
                isHidden('ehp') ? undefined : { label: 'Effective HP', value: derived?.ehp, numericValue: derived?.ehp, weightKey: 'ehp' },
                derived?.movement_speed !== undefined && !isHidden('movement_speed')
                  ? { label: 'Movement Speed', value: toPercent(derived.movement_speed), numericValue: derived.movement_speed, weightKey: 'movement_speed' }
                  : undefined,
                derived?.max_hit &&
                [
                  derived.max_hit.physical,
                  derived.max_hit.fire,
                  derived.max_hit.cold,
                  derived.max_hit.lightning,
                  derived.max_hit.chaos,
                ].some((v) => v && v !== 0)
                  ? isHidden('max_hit')
                    ? undefined
                    : {
                        label: 'Max Hit',
                        value: [
                          derived.max_hit.physical !== undefined && `Phys ${Math.round(derived.max_hit.physical).toLocaleString()}`,
                          derived.max_hit.fire !== undefined && `Fire ${Math.round(derived.max_hit.fire).toLocaleString()}`,
                          derived.max_hit.cold !== undefined && `Cold ${Math.round(derived.max_hit.cold).toLocaleString()}`,
                          derived.max_hit.lightning !== undefined && `Lightning ${Math.round(derived.max_hit.lightning).toLocaleString()}`,
                          derived.max_hit.chaos !== undefined && `Chaos ${Math.round(derived.max_hit.chaos).toLocaleString()}`,
                        ]
                          .filter(Boolean)
                          .join(' · '),
                        numericValue: Math.max(
                          derived.max_hit.physical ?? 0,
                          derived.max_hit.fire ?? 0,
                          derived.max_hit.cold ?? 0,
                          derived.max_hit.lightning ?? 0,
                          derived.max_hit.chaos ?? 0,
                        ),
                        weightKey: 'max_hit',
                      }
                  : undefined,
              ]
                .filter((stat) => stat && stat.value !== undefined)
                .map((stat, idx) => {
                  const weight = stat.weightKey ? getWeight(stat.weightKey) : null
                  return (
                    <TableRow key={`stat-${idx}-${stat.label}`}>
                      <TableCell className="font-medium px-3">{stat.label}</TableCell>
                      <TableCell className={`text-right px-3 ${stat.accent ?? ''}`}>
                        {typeof stat.value === 'number' ? Math.round(stat.value).toLocaleString() : stat.value}
                      </TableCell>
                      <TableCell className="px-3">
                        {weight && (
                          <Input
                            type="number"
                            step="0.05"
                            min="0"
                            className="h-7 w-full text-right text-xs px-2"
                            value={weight.percentWeight}
                            onChange={(e) => onWeightChange(stat.weightKey!, 'percentWeight', parseFloat(e.target.value) || 0)}
                            disabled={weight.gainType === 'flat'}
                            title="Weight for 1% more"
                          />
                        )}
                      </TableCell>
                      <TableCell className="px-3">
                        {weight && (
                          <Input
                            type="number"
                            step="0.05"
                            min="0"
                            className="h-7 w-full text-right text-xs px-2"
                            value={weight.flatWeight}
                            onChange={(e) => onWeightChange(stat.weightKey!, 'flatWeight', parseFloat(e.target.value) || 0)}
                            disabled={weight.gainType === 'percent'}
                            title="Weight for +1 flat"
                          />
                        )}
                      </TableCell>
                      <TableCell className="px-3">
                        {weight && (
                          <select
                            className="h-7 w-full text-xs rounded-md border border-input bg-background px-2 cursor-pointer hover:bg-accent"
                            value={weight.gainType}
                            onChange={(e) => onWeightChange(stat.weightKey!, 'gainType', e.target.value)}
                          >
                            <option value="percent">1% more</option>
                            <option value="flat">+1 flat</option>
                          </select>
                        )}
                      </TableCell>
                      <TableCell className="px-2">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          aria-label={`Hide ${stat.label}`}
                          onClick={() => hideStat(stat.weightKey!)}
                          className="size-6"
                        >
                          <X className="size-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })}
              {/* Render additional stats that were added via "+ Add Stat" */}
              {Object.keys(weights)
                .filter((key) => {
                  // Check if this stat key is already rendered in the hardcoded list above
                  const hardcodedKeys = [
                    'life', 'energy_shield', 'mana', 'armour', 'evasion',
                    'block', 'spell_block', 'spell_suppression',
                    'fire_res', 'cold_res', 'lightning_res', 'chaos_res',
                    'dps', 'ehp', 'movement_speed', 'max_hit'
                  ]
                  return !hardcodedKeys.includes(key)
                })
                .map((statKey) => {
                  const weight = getWeight(statKey)
                  const statDef = statDefinitions?.stats.find((s) => s.key === statKey)
                  const displayName = statDef?.display_name || statKey.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())

                  // Check if stat is hidden
                  if (isHidden(statKey)) return null

                  // Map stat keys to their values from derived or build data
                  const getStatValue = (key: string): number | string | undefined => {
                    if (!derived && !build) return undefined

                    switch (key) {
                      // Defense stats
                      case 'mana':
                        return derived?.mana ?? build.mana
                      case 'armour':
                        return derived?.armour ?? build.armour
                      case 'evasion':
                        return derived?.eva ?? build.evasion
                      case 'block':
                        return derived?.block?.attack
                      case 'spell_block':
                        return derived?.block?.spell
                      case 'spell_suppression':
                        return derived?.block?.suppression

                      // Attributes
                      case 'strength':
                        return derived?.attributes?.str
                      case 'dexterity':
                        return derived?.attributes?.dex
                      case 'intelligence':
                        return derived?.attributes?.int

                      // Damage stats
                      case 'crit_chance':
                        return derived?.crit_chance
                      case 'crit_multi':
                        return derived?.crit_multi
                      case 'phys_damage_avg':
                        return derived?.phys_damage_avg
                      case 'phys_damage_percent':
                        return derived?.phys_damage_percent

                      // Speed stats
                      case 'attack_speed':
                        return derived?.attack_speed
                      case 'cast_speed':
                        return derived?.cast_speed

                      default:
                        return undefined
                    }
                  }

                  const statValue = getStatValue(statKey)

                  return (
                    <TableRow key={`added-stat-${statKey}`}>
                      <TableCell className="font-medium px-3">{displayName}</TableCell>
                      <TableCell className="text-right px-3">
                        {typeof statValue === 'number' ? Math.round(statValue).toLocaleString() : statValue ?? '—'}
                      </TableCell>
                      <TableCell className="px-3">
                        <Input
                          type="number"
                          step="0.05"
                          min="0"
                          className="h-7 w-full text-right text-xs px-2"
                          value={weight.percentWeight}
                          onChange={(e) => onWeightChange(statKey, 'percentWeight', parseFloat(e.target.value) || 0)}
                          disabled={weight.gainType === 'flat'}
                          title="Weight for 1% more"
                        />
                      </TableCell>
                      <TableCell className="px-3">
                        <Input
                          type="number"
                          step="0.05"
                          min="0"
                          className="h-7 w-full text-right text-xs px-2"
                          value={weight.flatWeight}
                          onChange={(e) => onWeightChange(statKey, 'flatWeight', parseFloat(e.target.value) || 0)}
                          disabled={weight.gainType === 'percent'}
                          title="Weight for +1 flat"
                        />
                      </TableCell>
                      <TableCell className="px-3">
                        <select
                          className="h-7 w-full text-xs rounded-md border border-input bg-background px-2 cursor-pointer hover:bg-accent"
                          value={weight.gainType}
                          onChange={(e) => onWeightChange(statKey, 'gainType', e.target.value)}
                        >
                          <option value="percent">1% more</option>
                          <option value="flat">+1 flat</option>
                        </select>
                      </TableCell>
                      <TableCell className="px-2">
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          aria-label={`Hide ${displayName}`}
                          onClick={() => hideStat(statKey)}
                          className="size-6"
                        >
                          <X className="size-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })
                .filter(Boolean)}
            </TableBody>
          </Table>
          )}
        </CardContent>
      </Card>

      {/* Items Card */}
      {itemCount > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Equipped Items</CardTitle>
            <CardDescription>{itemCount} items equipped</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {groupedItems.map(({ label, items }) => (
              <div key={label} className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">{label}</h3>
                  <Separator className="flex-1 ml-3" />
                </div>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {items.map(({ slot, item }) => (
                    <div key={slot} className="rounded-lg border p-3">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-medium text-muted-foreground uppercase">
                              {slot}
                            </span>
                            <Badge
                              variant={
                                item.rarity === 'UNIQUE'
                                  ? 'default'
                                  : item.rarity === 'RARE'
                                    ? 'secondary'
                                    : 'outline'
                              }
                            >
                              {item.rarity}
                            </Badge>
                          </div>
                          <p className="font-medium">
                            {item.name || item.base_type}
                          </p>
                          {item.name && item.name !== item.base_type && (
                            <p className="text-sm text-muted-foreground">{item.base_type}</p>
                          )}
                          {item.sockets && (
                            <p className="text-xs text-muted-foreground">Sockets: {item.sockets}</p>
                          )}
                        </div>
                      </div>
                      {/* Show first 3 mods */}
                      {item.explicit_mods.length > 0 && (
                        <div className="mt-2 space-y-1">
                          {item.explicit_mods.slice(0, 3).map((mod: string, idx: number) => (
                            <p key={idx} className="text-xs text-muted-foreground">
                              {mod}
                            </p>
                          ))}
                          {item.explicit_mods.length > 3 && (
                            <p className="text-xs text-muted-foreground italic">
                              +{item.explicit_mods.length - 3} more mods
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

type GroupKey = 'Weapons' | 'Armour' | 'Jewellery' | 'Flasks' | 'Other'

const GROUP_ORDER: GroupKey[] = ['Weapons', 'Armour', 'Jewellery', 'Flasks', 'Other']

function toGroup(slot: string): GroupKey {
  const key = slot.toLowerCase()
  if (key.includes('weapon') || key.includes('hand') || key.includes('quiver') || key.includes('shield')) {
    return 'Weapons'
  }
  if (
    key.includes('helm') ||
    key.includes('body') ||
    key.includes('armour') ||
    key.includes('glove') ||
    key.includes('boot')
  ) {
    return 'Armour'
  }
  if (key.includes('amulet') || key.includes('ring') || key.includes('belt')) {
    return 'Jewellery'
  }
  if (key.includes('flask')) {
    return 'Flasks'
  }
  return 'Other'
}

function groupItemsByCategory(items: Record<string, ItemData>) {
  const groups: Record<GroupKey, { slot: string; item: ItemData }[]> = {
    Weapons: [],
    Armour: [],
    Jewellery: [],
    Flasks: [],
    Other: [],
  }

  Object.entries(items).forEach(([slot, item]) => {
    groups[toGroup(slot)].push({ slot, item })
  })

  return GROUP_ORDER.map((label) => ({
    label,
    items: groups[label],
  })).filter((group) => group.items.length > 0)
}
