/**
 * Upgrade Results Component
 *
 * Display ranked upgrades with sortable table using TanStack Table.
 */
import { useMemo, useState } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table'
import { ArrowUpDown, TrendingUp, TrendingDown } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { TradeWhisper } from './TradeWhisper'

export interface UpgradeResultItem {
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

interface UpgradeResultsProps {
  results: UpgradeResultItem[]
  currentItem: {
    name?: string
    base_type: string
    stats: Record<string, number>
  }
}

export function UpgradeResults({ results, currentItem }: UpgradeResultsProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'upgrade_score', desc: true },
  ])

  const columns = useMemo<ColumnDef<UpgradeResultItem>[]>(
    () => [
      {
        accessorKey: 'name',
        header: 'Item',
        cell: ({ row }) => (
          <div className='space-y-1'>
            <div className='font-medium'>
              {row.original.name || row.original.base_type}
            </div>
            <div className='text-muted-foreground text-sm'>
              {row.original.base_type}
            </div>
            <Badge variant={getRarityVariant(row.original.rarity)}>
              {row.original.rarity}
            </Badge>
          </div>
        ),
      },
      {
        accessorKey: 'price_chaos',
        header: ({ column }) => (
          <div
            className='flex cursor-pointer items-center'
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          >
            Price
            <ArrowUpDown className='ml-2 h-4 w-4' />
          </div>
        ),
        cell: ({ row }) => (
          <div className='font-medium'>
            {row.original.price_chaos.toFixed(1)}c
          </div>
        ),
      },
      {
        accessorKey: 'upgrade_score',
        header: ({ column }) => (
          <div
            className='flex cursor-pointer items-center'
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          >
            Score
            <ArrowUpDown className='ml-2 h-4 w-4' />
          </div>
        ),
        cell: ({ row }) => (
          <div className='font-bold text-green-600'>
            {row.original.upgrade_score.toFixed(1)}
          </div>
        ),
      },
      {
        id: 'improvements',
        header: 'Improvements',
        cell: ({ row }) => (
          <div className='space-y-1 text-sm'>
            {Object.entries(row.original.improvements)
              .slice(0, 3)
              .map(([stat, value]) => (
                <div key={stat} className='flex items-center gap-1'>
                  {value > 0 ? (
                    <TrendingUp className='h-3 w-3 text-green-500' />
                  ) : (
                    <TrendingDown className='h-3 w-3 text-red-500' />
                  )}
                  <span
                    className={value > 0 ? 'text-green-600' : 'text-red-600'}
                  >
                    {value > 0 ? '+' : ''}
                    {value.toFixed(0)} {formatStatName(stat)}
                  </span>
                </div>
              ))}
            {Object.keys(row.original.improvements).length > 3 && (
              <div className='text-muted-foreground text-xs italic'>
                +{Object.keys(row.original.improvements).length - 3} more stats
              </div>
            )}
          </div>
        ),
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <TradeWhisper
            whisper={row.original.whisper}
            itemName={row.original.name}
          />
        ),
      },
    ],
    []
  )

  const table = useReactTable({
    data: results,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upgrade Results</CardTitle>
        <CardDescription>
          {results.length} potential upgrade{results.length !== 1 ? 's' : ''}{' '}
          found for {currentItem.name || currentItem.base_type}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {results.length === 0 ? (
          <div className='text-muted-foreground py-8 text-center'>
            No upgrades found. Try adjusting your filters or price range.
          </div>
        ) : (
          <div className='rounded-md border'>
            <Table>
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead key={header.id}>
                        {header.isPlaceholder
                          ? null
                          : flexRender(
                              header.column.columnDef.header,
                              header.getContext()
                            )}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows.map((row) => (
                  <TableRow key={row.id}>
                    {row.getVisibleCells().map((cell) => (
                      <TableCell key={cell.id}>
                        {flexRender(
                          cell.column.columnDef.cell,
                          cell.getContext()
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function getRarityVariant(
  rarity: string
): 'default' | 'secondary' | 'outline' | 'destructive' {
  switch (rarity.toUpperCase()) {
    case 'UNIQUE':
      return 'default'
    case 'RARE':
      return 'secondary'
    case 'MAGIC':
      return 'outline'
    default:
      return 'outline'
  }
}

function formatStatName(stat: string): string {
  return stat.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
}
