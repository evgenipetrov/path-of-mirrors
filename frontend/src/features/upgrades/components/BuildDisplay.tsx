/**
 * Build Display Component
 *
 * Shows parsed Path of Building character information and items.
 */

import { useEffect, useRef, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import type { PoBParseResponse, ItemData } from '../types'

interface BuildDisplayProps {
  build: PoBParseResponse
}

const DEFAULT_WEIGHTS: Record<string, number> = {
  life: 2,
  es: 1,
  mana: 1,
  armour: 0.5,
  evasion: 0.5,
  block: 0.5,
  spell_block: 0.5,
  spell_suppression: 0.5,
  res_fire: 1,
  res_cold: 1,
  res_lightning: 1,
  res_chaos: 1,
  dps: 3,
  ehp: 2,
  max_hit: 1,
}

export function BuildDisplay({ build }: BuildDisplayProps) {
  const itemCount = build.items ? Object.keys(build.items).length : 0

  const groupedItems = groupItemsByCategory(build.items ?? {})
  const derived = build.derived_stats
  const [weights, setWeights] = useState<Record<string, number>>(DEFAULT_WEIGHTS)
  const storageKey = `build-name-${build.game}-${build.session_id}`
  const initialName =
    (typeof window !== 'undefined' && window.localStorage?.getItem(storageKey)) || build.name || 'Unnamed Build'
  const [customName, setCustomName] = useState(initialName)
  const [isEditingName, setIsEditingName] = useState(false)
  const nameInputRef = useRef<HTMLInputElement | null>(null)

  // Persist name per session
  useEffect(() => {
    setCustomName(initialName)
    setIsEditingName(false)
  }, [build.game, build.session_id, initialName])

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

  const getWeight = (key: string, fallback = 1) => weights[key] ?? DEFAULT_WEIGHTS[key] ?? fallback
  const onWeightChange = (key: string, value: number) =>
    setWeights((prev) => ({ ...prev, [key]: value }))

  return (
    <div className="space-y-4">
      {/* Character Info Card */}
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <div className="relative flex-1 max-w-sm">
                <input
                  aria-label="Build name"
                  ref={nameInputRef}
                  readOnly={!isEditingName}
                  className={`w-full rounded-md border px-3 py-2 pr-10 text-lg font-semibold ${isEditingName ? '' : 'bg-muted'}`}
                  value={customName}
                  onChange={(e) => handleNameChange(e.target.value)}
                  onBlur={stopNameEdit}
                />
                <button
                  type="button"
                  aria-label="Edit build name"
                  className="absolute inset-y-0 right-2 flex items-center text-muted-foreground hover:text-foreground"
                  onClick={startNameEdit}
                >
                  ✏️
                </button>
              </div>
            </div>
            <CardDescription>
              Level {build.level} {build.ascendancy || build.character_class}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Character quick info inline */}
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            <InfoBlock label="Class" lines={[build.character_class]} />
            {build.ascendancy && <InfoBlock label="Ascendancy" lines={[build.ascendancy]} />}
            <InfoBlock label="Level" lines={[build.level.toString()]} />
            {build.league && <InfoBlock label="League" lines={[build.league]} />}
            {derived?.attributes && (
              <InfoBlock
                label="Attributes"
                lines={[
                  formatAttributes(derived.attributes) ?? '—',
                  'Str / Dex / Int',
                ]}
              />
            )}
            {derived?.charges && (
              <InfoBlock
                label="Charges"
                lines={[
                  `${derived.charges.endurance ?? 0} / ${derived.charges.frenzy ?? 0} / ${derived.charges.power ?? 0}`,
                  'Endurance / Frenzy / Power',
                ]}
              />
            )}
          </div>

          <div className="grid gap-4 lg:grid-cols-3">

            <StatColumn
              title="Defensive"
              stats={[
                { label: 'Life', value: derived?.life ?? build.life, accent: 'text-red-500', weightKey: 'life' },
                { label: 'Energy Shield', value: derived?.es ?? build.energy_shield, weightKey: 'es' },
                { label: 'Mana', value: derived?.mana ?? build.mana, weightKey: 'mana' },
                { label: 'Armour', value: derived?.armour ?? build.armour, weightKey: 'armour' },
                { label: 'Evasion', value: derived?.eva ?? build.evasion, weightKey: 'evasion' },
                derived?.block?.attack !== undefined ? { label: 'Block', value: toPercent(derived.block.attack), weightKey: 'block' } : undefined,
                derived?.block?.spell !== undefined ? { label: 'Spell Block', value: toPercent(derived.block.spell), weightKey: 'spell_block' } : undefined,
                derived?.block?.suppression !== undefined
                  ? { label: 'Spell Suppression', value: toPercent(derived.block.suppression), weightKey: 'spell_suppression' }
                  : undefined,
              ].filter((stat) => stat && stat.value !== undefined)}
              getWeight={getWeight}
              onWeightChange={onWeightChange}
            />

            <StatColumn
              title="Resistances"
              stats={
                derived?.res
                  ? [
                      derived.res.fire !== undefined
                        ? { label: 'Fire', value: `${derived.res.fire}%`, weightKey: 'res_fire' }
                        : undefined,
                      derived.res.cold !== undefined
                        ? { label: 'Cold', value: `${derived.res.cold}%`, weightKey: 'res_cold' }
                        : undefined,
                      derived.res.lightning !== undefined
                        ? { label: 'Lightning', value: `${derived.res.lightning}%`, weightKey: 'res_lightning' }
                        : undefined,
                      derived.res.chaos !== undefined
                        ? { label: 'Chaos', value: `${derived.res.chaos}%`, weightKey: 'res_chaos' }
                        : undefined,
                    ].filter(Boolean) as StatTileProps[]
                  : []
              }
              getWeight={getWeight}
              onWeightChange={onWeightChange}
            />

            <StatColumn
              title="Offensive / Simulated"
              stats={[
                { label: 'Total DPS', value: derived?.dps, weightKey: 'dps' },
                { label: 'Effective HP', value: derived?.ehp, weightKey: 'ehp' },
                derived?.movement_speed !== undefined
                  ? { label: 'Movement Speed', value: toPercent(derived.movement_speed), weightKey: 'ms' }
                  : undefined,
                derived?.max_hit &&
                [
                  derived.max_hit.physical,
                  derived.max_hit.fire,
                  derived.max_hit.cold,
                  derived.max_hit.lightning,
                  derived.max_hit.chaos,
                ].some((v) => v && v !== 0)
                  ? {
                      label: 'Max Hit',
                      detail: [
                        derived.max_hit.physical !== undefined && `Phys ${Math.round(derived.max_hit.physical).toLocaleString()}`,
                        derived.max_hit.fire !== undefined && `Fire ${Math.round(derived.max_hit.fire).toLocaleString()}`,
                        derived.max_hit.cold !== undefined && `Cold ${Math.round(derived.max_hit.cold).toLocaleString()}`,
                        derived.max_hit.lightning !== undefined &&
                          `Lightning ${Math.round(derived.max_hit.lightning).toLocaleString()}`,
                        derived.max_hit.chaos !== undefined && `Chaos ${Math.round(derived.max_hit.chaos).toLocaleString()}`,
                      ]
                        .filter(Boolean)
                        .join(' · '),
                      weightKey: 'max_hit',
                    }
                  : undefined,
              ].filter((stat) => stat && (stat.value !== undefined || stat.detail))}
              getWeight={getWeight}
              onWeightChange={onWeightChange}
            />
          </div>
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

type StatTileProps = {
  label: string
  value?: number | string
  detail?: string
  accent?: string
  weightKey?: string
  getWeight: (key: string, fallback?: number) => number
  onWeightChange: (key: string, value: number) => void
}

function StatTile({ label, value, detail, accent, weightKey, getWeight, onWeightChange }: StatTileProps) {
  return (
    <div className="rounded-lg border p-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          {value !== undefined ? (
            <p className={`text-xl font-semibold leading-tight ${accent ?? ''}`}>
              {typeof value === 'number' ? Math.round(value).toLocaleString() : value}
            </p>
          ) : (
            <p className="text-sm text-muted-foreground">{detail || '—'}</p>
          )}
        </div>
        {weightKey && (
          <div className="flex items-center gap-1 self-end">
            <label className="text-xs text-muted-foreground" htmlFor={`weight-${weightKey}`}>
              Priority
            </label>
            <input
              id={`weight-${weightKey}`}
              type="number"
              step="0.1"
              className="w-14 rounded border px-2 py-1 text-right text-xs"
              value={getWeight(weightKey)}
              onChange={(e) => onWeightChange(weightKey, parseFloat(e.target.value) || 0)}
            />
          </div>
        )}
      </div>
      {detail && value !== undefined && (
        <p className="text-xs text-muted-foreground mt-1">{detail}</p>
      )}
    </div>
  )
}

type StatColumnProps = {
  title: string
  stats: Array<{ label: string; value?: number | string; detail?: string; accent?: string; weightKey?: string }>
  getWeight: (key: string, fallback?: number) => number
  onWeightChange: (key: string, value: number) => void
}

function StatColumn({ title, stats, getWeight, onWeightChange }: StatColumnProps) {
  if (!stats || stats.length === 0) return null
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase text-muted-foreground">{title}</p>
      <div className="grid gap-2">
        {stats.map((stat, idx) => (
          <StatTile
            key={`${title}-${idx}-${stat.label}`}
            {...stat}
            getWeight={getWeight}
            onWeightChange={onWeightChange}
          />
        ))}
      </div>
    </div>
  )
}

type InfoLineProps = {
  label: string
  value: string
  detail?: string
}

function InfoLine({ label, value, detail }: InfoLineProps) {
  return (
    <div className="flex flex-col">
      <span className="text-xs uppercase text-muted-foreground font-semibold">{label}</span>
      <span className="text-sm font-medium">{value}</span>
      {detail && <span className="text-xs text-muted-foreground">{detail}</span>}
    </div>
  )
}

function InfoBlock({ label, lines }: { label: string; lines: string[] }) {
  return (
    <div className="rounded-lg border px-3 py-2 flex flex-col gap-1">
      <span className="text-xs uppercase text-muted-foreground font-semibold">{label}</span>
      {lines.map((line, idx) => (
        <span key={`${label}-${idx}`} className={idx === 0 ? 'text-sm font-medium' : 'text-xs text-muted-foreground'}>
          {line}
        </span>
      ))}
    </div>
  )
}
