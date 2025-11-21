/**
 * Build Display Component
 *
 * Shows parsed Path of Building character information and items.
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import type { PoBParseResponse, ItemData } from '../types'

interface BuildDisplayProps {
  build: PoBParseResponse
}

export function BuildDisplay({ build }: BuildDisplayProps) {
  const itemCount = build.items ? Object.keys(build.items).length : 0

  const groupedItems = groupItemsByCategory(build.items ?? {})
  const derived = build.derived_stats

  return (
    <div className="space-y-4">
      {/* Character Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {build.name}
            <Badge variant="outline">{build.game.toUpperCase()}</Badge>
          </CardTitle>
          <CardDescription>
            Level {build.level} {build.ascendancy || build.character_class}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div>
              <p className="text-sm text-muted-foreground">Class</p>
              <p className="font-medium">{build.character_class}</p>
            </div>
            {build.ascendancy && (
              <div>
                <p className="text-sm text-muted-foreground">Ascendancy</p>
                <p className="font-medium">{build.ascendancy}</p>
              </div>
            )}
            {build.league && (
              <div>
                <p className="text-sm text-muted-foreground">League</p>
                <p className="font-medium">{build.league}</p>
              </div>
            )}
            <div>
              <p className="text-sm text-muted-foreground">Level</p>
              <p className="font-medium">{build.level}</p>
            </div>
          </div>
          <Separator />

          <div className="grid gap-4 lg:grid-cols-4">
            <StatColumn
              title="Life / EHP"
              stats={[
                { label: 'Life', value: derived?.life ?? build.life ?? undefined, accent: 'text-red-500' },
                { label: 'Mana', value: build.mana ?? undefined },
                { label: 'EHP', value: derived?.ehp },
              ].filter((stat) => stat.value !== undefined)}
            />

            <StatColumn
              title="Defences"
              stats={[
                { label: 'Energy Shield', value: derived?.es ?? build.energy_shield ?? undefined },
                { label: 'Armour', value: derived?.armour ?? build.armour ?? undefined },
                { label: 'Evasion', value: derived?.eva ?? build.evasion ?? undefined },
              ].filter((stat) => stat.value !== undefined)}
            />

            <StatColumn
              title="Resistances"
              stats={
                derived?.res
                  ? [
                      {
                        label: 'Resists',
                        detail: [
                          derived.res.fire !== undefined && `Fire ${derived.res.fire}%`,
                          derived.res.cold !== undefined && `Cold ${derived.res.cold}%`,
                          derived.res.lightning !== undefined && `Lightning ${derived.res.lightning}%`,
                          derived.res.chaos !== undefined && `Chaos ${derived.res.chaos}%`,
                        ]
                          .filter(Boolean)
                          .join(' · '),
                      },
                    ].filter((stat) => stat.detail)
                  : []
              }
            />

            <StatColumn
              title="Offence"
              stats={[
                { label: 'Total DPS', value: derived?.dps },
              ].filter((stat) => stat.value !== undefined)}
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
  value?: number
  detail?: string
  accent?: string
}

function StatTile({ label, value, detail, accent }: StatTileProps) {
  return (
    <div className="rounded-lg border p-3">
      <p className="text-sm text-muted-foreground">{label}</p>
      {value !== undefined ? (
        <p className={`text-xl font-semibold ${accent ?? ''}`}>{Math.round(value).toLocaleString()}</p>
      ) : (
        <p className="text-sm text-muted-foreground">{detail || '—'}</p>
      )}
      {detail && value !== undefined && (
        <p className="text-xs text-muted-foreground mt-1">{detail}</p>
      )}
    </div>
  )
}

type StatColumnProps = {
  title: string
  stats: Array<{ label: string; value?: number; detail?: string; accent?: string }>
}

function StatColumn({ title, stats }: StatColumnProps) {
  if (!stats || stats.length === 0) return null
  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold uppercase text-muted-foreground">{title}</p>
      <div className="grid gap-2">
        {stats.map((stat, idx) => (
          <StatTile key={`${title}-${idx}-${stat.label}`} {...stat} />
        ))}
      </div>
    </div>
  )
}
