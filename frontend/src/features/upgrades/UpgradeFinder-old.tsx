/**
 * Upgrade Finder Feature Component
 *
 * Main page for finding item upgrades using Path of Building imports.
 */
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { AlertCircle, CheckCircle2, ChevronUp } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { parsePob } from './api'
import { BuildDisplay } from './components/BuildDisplay'
import { PoBInput } from './components/PoBInput'
import type { Game, PoBParseResponse } from './types'

type ApiError = { response?: { data?: { detail?: string } } }

export function UpgradeFinder() {
  const [game] = useState<Game>('poe1') // TODO: Add game selector
  const [parsedBuild, setParsedBuild] = useState<PoBParseResponse | null>(null)
  const [isImportOpen, setIsImportOpen] = useState(true)

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
      setIsImportOpen(false) // Collapse after successful import
    },
  })

  return (
    <div className='container mx-auto space-y-6 py-8'>
      <div>
        <h1 className='text-3xl font-bold tracking-tight'>Build Analyzer</h1>
        <p className='text-muted-foreground mt-2'>
          Import your Path of Building to analyze your build and find upgrades
        </p>
      </div>

      {/* Error Alert */}
      {parseMutation.isError && (
        <Alert variant='destructive'>
          <AlertCircle className='h-4 w-4' />
          <AlertTitle>Error parsing build</AlertTitle>
          <AlertDescription>
            {parseMutation.error instanceof Error
              ? parseMutation.error.message
              : 'Failed to parse Path of Building data. Please check your input and try again.'}
            {/* Show backend error detail if available */}
            {(parseMutation.error as ApiError | undefined)?.response?.data
              ?.detail && (
              <div className='mt-2 text-sm'>
                <strong>Details:</strong>{' '}
                {(parseMutation.error as ApiError).response?.data?.detail}
              </div>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Success Alert with Import Another Build button */}
      {parseMutation.isSuccess && parsedBuild && !isImportOpen && (
        <Alert>
          <CheckCircle2 className='h-4 w-4' />
          <AlertTitle>Build parsed successfully</AlertTitle>
          <AlertDescription className='flex items-center justify-between'>
            <span>
              Loaded {parsedBuild.name} -{' '}
              {parsedBuild.items ? Object.keys(parsedBuild.items).length : 0}{' '}
              items found
            </span>
            <Button
              variant='outline'
              size='sm'
              onClick={() => setIsImportOpen(true)}
              className='ml-4'
            >
              Import Another Build
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* PoB Input - Collapsible */}
      {isImportOpen && (
        <div className='space-y-4'>
          {parsedBuild && (
            <div className='flex justify-end'>
              <Button
                variant='ghost'
                size='sm'
                onClick={() => setIsImportOpen(false)}
              >
                <ChevronUp className='mr-2 h-4 w-4' />
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
    </div>
  )
}
