/**
 * Build Display Component
 *
 * Shows parsed Path of Building character information and items.
 */

import { useRef, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { X, Pencil, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react'
import type { PoBParseResponse, ItemData } from '../types'

interface BuildDisplayProps {
  build: PoBParseResponse
}

type StatWeight = {
  percentWeight: number
  flatWeight: number
  gainType: 'percent' | 'flat'
}

const DEFAULT_WEIGHTS: Record<string, StatWeight> = {
  life: { percentWeight: 0.5, flatWeight: 2, gainType: 'percent' },
  es: { percentWeight: 0.5, flatWeight: 1, gainType: 'flat' },
  mana: { percentWeight: 0.5, flatWeight: 1, gainType: 'flat' },
  armour: { percentWeight: 0.3, flatWeight: 0.5, gainType: 'flat' },
  evasion: { percentWeight: 0.3, flatWeight: 0.5, gainType: 'flat' },
  block: { percentWeight: 0.5, flatWeight: 0.5, gainType: 'percent' },
  spell_block: { percentWeight: 0.5, flatWeight: 0.5, gainType: 'percent' },
  spell_suppression: { percentWeight: 0.5, flatWeight: 0.5, gainType: 'percent' },
  res_fire: { percentWeight: 5, flatWeight: 0.05, gainType: 'flat' },
  res_cold: { percentWeight: 5, flatWeight: 0.05, gainType: 'flat' },
  res_lightning: { percentWeight: 5, flatWeight: 0.05, gainType: 'flat' },
  res_chaos: { percentWeight: 5, flatWeight: 0.05, gainType: 'flat' },
  dps: { percentWeight: 3, flatWeight: 0.001, gainType: 'percent' },
  ehp: { percentWeight: 2, flatWeight: 0.001, gainType: 'percent' },
  ms: { percentWeight: 1, flatWeight: 0.1, gainType: 'percent' },
  max_hit: { percentWeight: 1, flatWeight: 0.001, gainType: 'percent' },
}

export function BuildDisplay({ build }: BuildDisplayProps) {
  const itemCount = build.items ? Object.keys(build.items).length : 0

  const groupedItems = groupItemsByCategory(build.items ?? {})
  const derived = build.derived_stats
  const [weights, setWeights] = useState<Record<string, StatWeight>>(DEFAULT_WEIGHTS)
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

  const [hiddenStats, setHiddenStats] = useState<Set<string>>(new Set())
  const [isStatsCollapsed, setIsStatsCollapsed] = useState(false)

  const hideStat = (label: string) =>
    setHiddenStats((prev) => {
      const next = new Set(prev)
      next.add(label)
      return next
    })

  const isHidden = (label: string) => hiddenStats.has(label)

  const resetWeights = () => {
    setWeights(DEFAULT_WEIGHTS)
    setHiddenStats(new Set())
  }

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
                isHidden('Life') ? undefined : { label: 'Life', value: derived?.life ?? build.life, numericValue: derived?.life ?? build.life, accent: 'text-red-500', weightKey: 'life' },
                isHidden('Energy Shield') ? undefined : { label: 'Energy Shield', value: derived?.es ?? build.energy_shield, numericValue: derived?.es ?? build.energy_shield, weightKey: 'es' },
                isHidden('Mana') ? undefined : { label: 'Mana', value: derived?.mana ?? build.mana, numericValue: derived?.mana ?? build.mana, weightKey: 'mana' },
                isHidden('Armour') ? undefined : { label: 'Armour', value: derived?.armour ?? build.armour, numericValue: derived?.armour ?? build.armour, weightKey: 'armour' },
                isHidden('Evasion') ? undefined : { label: 'Evasion', value: derived?.eva ?? build.evasion, numericValue: derived?.eva ?? build.evasion, weightKey: 'evasion' },
                derived?.block?.attack !== undefined && !isHidden('Block') ? { label: 'Block', value: toPercent(derived.block.attack), numericValue: derived.block.attack, weightKey: 'block' } : undefined,
                derived?.block?.spell !== undefined && !isHidden('Spell Block') ? { label: 'Spell Block', value: toPercent(derived.block.spell), numericValue: derived.block.spell, weightKey: 'spell_block' } : undefined,
                derived?.block?.suppression !== undefined && !isHidden('Spell Suppression')
                  ? { label: 'Spell Suppression', value: toPercent(derived.block.suppression), numericValue: derived.block.suppression, weightKey: 'spell_suppression' }
                  : undefined,
                derived?.res?.fire !== undefined && !isHidden('Fire') ? { label: 'Fire Res', value: `${derived.res.fire}%`, numericValue: derived.res.fire, weightKey: 'res_fire' } : undefined,
                derived?.res?.cold !== undefined && !isHidden('Cold') ? { label: 'Cold Res', value: `${derived.res.cold}%`, numericValue: derived.res.cold, weightKey: 'res_cold' } : undefined,
                derived?.res?.lightning !== undefined && !isHidden('Lightning') ? { label: 'Lightning Res', value: `${derived.res.lightning}%`, numericValue: derived.res.lightning, weightKey: 'res_lightning' } : undefined,
                derived?.res?.chaos !== undefined && !isHidden('Chaos') ? { label: 'Chaos Res', value: `${derived.res.chaos}%`, numericValue: derived.res.chaos, weightKey: 'res_chaos' } : undefined,
                isHidden('Total DPS') ? undefined : { label: 'Total DPS', value: derived?.dps, numericValue: derived?.dps, weightKey: 'dps' },
                isHidden('Effective HP') ? undefined : { label: 'Effective HP', value: derived?.ehp, numericValue: derived?.ehp, weightKey: 'ehp' },
                derived?.movement_speed !== undefined && !isHidden('Movement Speed')
                  ? { label: 'Movement Speed', value: toPercent(derived.movement_speed), numericValue: derived.movement_speed, weightKey: 'ms' }
                  : undefined,
                derived?.max_hit &&
                [
                  derived.max_hit.physical,
                  derived.max_hit.fire,
                  derived.max_hit.cold,
                  derived.max_hit.lightning,
                  derived.max_hit.chaos,
                ].some((v) => v && v !== 0)
                  ? isHidden('Max Hit')
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
                          onClick={() => hideStat(stat.label)}
                          className="size-6"
                        >
                          <X className="size-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })}
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
