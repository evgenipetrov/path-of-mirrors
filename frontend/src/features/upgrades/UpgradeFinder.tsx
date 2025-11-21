/**
 * Upgrade Finder Feature Component
 *
 * Main page for finding item upgrades using Path of Building imports.
 * Complete end-to-end flow: Parse → Select Slot → Filter → Search → Display Results
 */

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { AlertCircle, CheckCircle2, ChevronUp, Search } from 'lucide-react'
import { PoBInput } from './components/PoBInput'
import { BuildDisplay } from './components/BuildDisplay'
import { ItemSlotSelector } from './components/ItemSlotSelector'
import { UpgradeFilters } from './components/UpgradeFilters'
import { UpgradeResults } from './components/UpgradeResults'
import { parsePob, searchUpgrades } from './api'
import type { Game, PoBParseResponse, UpgradeFiltersState, UpgradeSearchResponse } from './types'

export function UpgradeFinder() {
  const [game] = useState<Game>('poe1') // TODO: Add game selector
  const [parsedBuild, setParsedBuild] = useState<PoBParseResponse | null>(null)
  const [isImportOpen, setIsImportOpen] = useState(true)
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null)
  const [upgradeResults, setUpgradeResults] = useState<UpgradeSearchResponse | null>(null)
  const [filters, setFilters] = useState<UpgradeFiltersState>({
    maxPriceChaos: null,
    minLife: null,
    minResistance: null,
    limit: 10,
  })

  const parseMutation = useMutation({
    mutationFn: async (input: { pobXml?: string; pobCode?: string }) => {
      return parsePob({
        pob_xml: input.pobXml,
        pob_code: input.pobCode,
        game,
      })
    },
    onSuccess: (data) => {
      setParsedBuild(data)
      setIsImportOpen(false)
      setSelectedSlot(null) // Reset slot selection
      setUpgradeResults(null) // Clear previous results
    },
  })

  const searchMutation = useMutation({
    mutationFn: async () => {
      if (!parsedBuild || !selectedSlot) {
        throw new Error('No build or slot selected')
      }

      return searchUpgrades({
        session_id: parsedBuild.session_id,
        item_slot: selectedSlot,
        max_price_chaos: filters.maxPriceChaos,
        min_life: filters.minLife,
        min_resistance: filters.minResistance,
        limit: filters.limit,
      })
    },
    onSuccess: (data) => {
      setUpgradeResults(data)
    },
  })

  const availableSlots = parsedBuild?.items ? Object.keys(parsedBuild.items) : []
  const canSearch = parsedBuild && selectedSlot

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Build</h1>
        <p className="text-muted-foreground mt-2">
          Import a Path of Building to view key stats and equipped items grouped by slot. Then search for upgrades.
        </p>
      </div>

      {/* Parse Error Alert */}
      {parseMutation.isError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error parsing build</AlertTitle>
          <AlertDescription>
            {parseMutation.error instanceof Error
              ? parseMutation.error.message
              : 'Failed to parse Path of Building data. Please check your input and try again.'}
            {(
              (parseMutation.error as { response?: { data?: { detail?: string } } } | undefined)?.response?.data
                ?.detail
            ) && (
              <div className="mt-2 text-sm">
                <strong>Details:</strong>{' '}
                {
                  (parseMutation.error as { response?: { data?: { detail?: string } } } | undefined)?.response?.data
                    ?.detail
                }
              </div>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Search Error Alert */}
      {searchMutation.isError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error searching for upgrades</AlertTitle>
          <AlertDescription>
            {searchMutation.error instanceof Error
              ? searchMutation.error.message
              : 'Failed to search for upgrades. Please try again.'}
          </AlertDescription>
        </Alert>
      )}

      {/* Success Alert */}
      {parseMutation.isSuccess && parsedBuild && !isImportOpen && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertTitle>Build parsed successfully</AlertTitle>
          <AlertDescription className="flex items-center justify-between">
            <span>
              Loaded {parsedBuild.name} - {Object.keys(parsedBuild.items || {}).length} items found
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsImportOpen(true)}
              className="ml-4"
            >
              Import Another Build
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* PoB Input - Collapsible */}
      {isImportOpen && (
        <div className="space-y-4">
          {parsedBuild && (
            <div className="flex justify-end">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsImportOpen(false)}
              >
                <ChevronUp className="h-4 w-4 mr-2" />
                Hide Import
              </Button>
            </div>
          )}
          <PoBInput
            game={game}
            onParse={(input) => parseMutation.mutate(input)}
            isLoading={parseMutation.isPending}
          />
        </div>
      )}

      {/* Build Display */}
      {parsedBuild && <BuildDisplay build={parsedBuild} />}

      {/* Upgrade Search Section - Only show if build is parsed */}
      {parsedBuild && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* Item Slot Selector */}
            <ItemSlotSelector
              availableSlots={availableSlots}
              selectedSlot={selectedSlot}
              onSlotChange={setSelectedSlot}
              disabled={parseMutation.isPending || searchMutation.isPending}
            />

            {/* Upgrade Filters */}
            <UpgradeFilters
              filters={filters}
              onFiltersChange={setFilters}
              disabled={!canSearch || searchMutation.isPending}
            />
          </div>

          {/* Search Button */}
          <div className="flex justify-center">
            <Button
              onClick={() => searchMutation.mutate()}
              disabled={!canSearch || searchMutation.isPending}
              size="lg"
              className="w-full md:w-auto"
            >
              <Search className="mr-2 h-5 w-5" />
              {searchMutation.isPending ? 'Searching...' : 'Search for Upgrades'}
            </Button>
          </div>
        </div>
      )}

      {/* Upgrade Results */}
      {upgradeResults && (
        <UpgradeResults
          results={upgradeResults.upgrades}
          currentItem={upgradeResults.current_item}
        />
      )}
    </div>
  )
}
