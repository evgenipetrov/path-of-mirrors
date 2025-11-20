/**
 * Upgrade Filters Component
 *
 * Filters for price and minimum stat requirements.
 */

import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export interface UpgradeFiltersState {
  maxPriceChaos: number | null
  minLife: number | null
  minResistance: number | null
  limit: number
}

interface UpgradeFiltersProps {
  filters: UpgradeFiltersState
  onFiltersChange: (filters: UpgradeFiltersState) => void
  disabled?: boolean
}

export function UpgradeFilters({ filters, onFiltersChange, disabled = false }: UpgradeFiltersProps) {
  const handleFilterChange = (key: keyof UpgradeFiltersState, value: string) => {
    const numValue = value === '' ? null : Number(value)
    onFiltersChange({
      ...filters,
      [key]: numValue,
    })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Search Filters</CardTitle>
        <CardDescription>Customize your upgrade search criteria</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="space-y-2">
            <Label htmlFor="max-price">Max Price (Chaos)</Label>
            <Input
              id="max-price"
              type="number"
              placeholder="No limit"
              value={filters.maxPriceChaos ?? ''}
              onChange={(e) => handleFilterChange('maxPriceChaos', e.target.value)}
              disabled={disabled}
              min={0}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="min-life">Min Life</Label>
            <Input
              id="min-life"
              type="number"
              placeholder="No requirement"
              value={filters.minLife ?? ''}
              onChange={(e) => handleFilterChange('minLife', e.target.value)}
              disabled={disabled}
              min={0}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="min-resistance">Min Resistance</Label>
            <Input
              id="min-resistance"
              type="number"
              placeholder="No requirement"
              value={filters.minResistance ?? ''}
              onChange={(e) => handleFilterChange('minResistance', e.target.value)}
              disabled={disabled}
              min={0}
              max={75}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="limit">Max Results</Label>
          <Input
            id="limit"
            type="number"
            value={filters.limit}
            onChange={(e) => handleFilterChange('limit', e.target.value)}
            disabled={disabled}
            min={1}
            max={50}
          />
          <p className="text-xs text-muted-foreground">
            Number of results to return (1-50)
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
