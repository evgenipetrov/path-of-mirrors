import { ChevronsUpDown, Command } from 'lucide-react'
import { useGameContext, type Game } from '@/hooks/useGameContext'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar'

const GAMES = [
  { id: 'poe1' as Game, name: 'Path of Exile 1', shortName: 'POE1' },
  { id: 'poe2' as Game, name: 'Path of Exile 2', shortName: 'POE2' },
] as const

export function TeamSwitcher() {
  const { isMobile } = useSidebar()
  const { game, setGame } = useGameContext()

  const activeGame = GAMES.find((g) => g.id === game) || GAMES[0]

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size='lg'
              className='data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground'
            >
              <div className='bg-sidebar-primary text-sidebar-primary-foreground flex aspect-square size-8 items-center justify-center rounded-lg'>
                <Command className='size-4' />
              </div>
              <div className='grid flex-1 text-start text-sm leading-tight'>
                <span className='truncate font-semibold'>Path of Mirrors</span>
                <span className='truncate text-xs'>{activeGame.shortName}</span>
              </div>
              <ChevronsUpDown className='ms-auto' />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className='w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg'
            align='start'
            side={isMobile ? 'bottom' : 'right'}
            sideOffset={4}
          >
            <DropdownMenuLabel className='text-muted-foreground text-xs'>
              Game Context
            </DropdownMenuLabel>
            {GAMES.map((g, index) => (
              <DropdownMenuItem
                key={g.id}
                onClick={() => setGame(g.id)}
                className='gap-2 p-2'
              >
                <div className='flex size-6 items-center justify-center rounded-sm border'>
                  <Command className='size-4 shrink-0' />
                </div>
                {g.name}
                <DropdownMenuShortcut>⌘{index + 1}</DropdownMenuShortcut>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  )
}
