import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@/test-utils'
import userEvent from '@testing-library/user-event'
import { Notes } from './index'
import * as apiHooks from '@/hooks/api'
import * as gameContextHook from '@/hooks/useGameContext'
import { SidebarProvider } from '@/components/ui/sidebar'
import { SearchProvider } from '@/context/search-provider'
// Mock layout-dependent UI to avoid provider requirements in tests
vi.mock('@/components/search', () => ({ Search: () => <div data-testid="search-mock" /> }))
vi.mock('@/components/config-drawer', () => ({ ConfigDrawer: () => <div /> }))
vi.mock('@/components/theme-switch', () => ({ ThemeSwitch: () => <div /> }))
vi.mock('@/components/profile-dropdown', () => ({ ProfileDropdown: () => <div /> }))

// Mock the API hooks
vi.mock('@/hooks/api', async () => {
  const actual = await vi.importActual('@/hooks/api')
  return {
    ...actual,
    useListNotesApiNotesGet: vi.fn(),
    useCreateNoteApiNotesPost: vi.fn(),
    useUpdateNoteApiNotesNoteIdPut: vi.fn(),
    useDeleteNoteApiNotesNoteIdDelete: vi.fn(),
  }
})

// Mock the game context
vi.mock('@/hooks/useGameContext', () => ({
  useGameContext: vi.fn(),
}))

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('Notes', () => {
  const mockNotes = [
    {
      id: '1',
      title: 'Note 1',
      content: 'Content 1',
      game_context: 'poe1',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    },
    {
      id: '2',
      title: 'Note 2',
      content: null,
      game_context: 'poe1',
      created_at: '2024-01-02T00:00:00Z',
      updated_at: '2024-01-02T00:00:00Z',
    },
  ]

  const defaultMocks = {
    useListNotesApiNotesGet: {
      data: mockNotes,
      isLoading: false,
      error: null,
    },
    useCreateNoteApiNotesPost: {
      mutateAsync: vi.fn(),
      isPending: false,
    },
    useUpdateNoteApiNotesNoteIdPut: {
      mutateAsync: vi.fn(),
      isPending: false,
    },
    useDeleteNoteApiNotesNoteIdDelete: {
      mutateAsync: vi.fn(),
      isPending: false,
    },
    useGameContext: {
      game: 'poe1' as const,
      setGame: vi.fn(),
    },
  }

  beforeEach(() => {
    vi.clearAllMocks()

    // Setup default mocks
    vi.mocked(apiHooks.useListNotesApiNotesGet).mockReturnValue(
      defaultMocks.useListNotesApiNotesGet as any
    )
    vi.mocked(apiHooks.useCreateNoteApiNotesPost).mockReturnValue(
      defaultMocks.useCreateNoteApiNotesPost as any
    )
    vi.mocked(apiHooks.useUpdateNoteApiNotesNoteIdPut).mockReturnValue(
      defaultMocks.useUpdateNoteApiNotesNoteIdPut as any
    )
    vi.mocked(apiHooks.useDeleteNoteApiNotesNoteIdDelete).mockReturnValue(
      defaultMocks.useDeleteNoteApiNotesNoteIdDelete as any
    )
    vi.mocked(gameContextHook.useGameContext).mockReturnValue(
      defaultMocks.useGameContext
    )
  })

  const renderNotes = () =>
    render(
      <SearchProvider>
        <SidebarProvider>
          <Notes />
        </SidebarProvider>
      </SearchProvider>
    )

  describe('rendering', () => {
    it('should render with notes data', () => {
      renderNotes()

      expect(screen.getByText('Notes')).toBeInTheDocument()
      expect(screen.getByText((_content, element) => {
        return element?.textContent === 'Manage your notes for POE1' || false
      })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create note/i })).toBeInTheDocument()
    })

    it('should show correct game context in header', () => {
      vi.mocked(gameContextHook.useGameContext).mockReturnValue({
        game: 'poe2',
        setGame: vi.fn(),
      })

      renderNotes()

      expect(screen.getByText((_content, element) => {
        return element?.textContent === 'Manage your notes for POE2' || false
      })).toBeInTheDocument()
    })

    it('should display notes count', () => {
      renderNotes()

      expect(screen.getByText(/2 notes for POE1/i)).toBeInTheDocument()
    })
  })

  describe('loading state', () => {
    it('should show loading spinner when fetching notes', () => {
      vi.mocked(apiHooks.useListNotesApiNotesGet).mockReturnValue({
        data: [],
        isLoading: true,
        error: null,
      } as any)

      renderNotes()

      expect(screen.getByText('Loading notes...')).toBeInTheDocument()
    })
  })

  describe('error state', () => {
    it('should display error message when fetch fails', () => {
      vi.mocked(apiHooks.useListNotesApiNotesGet).mockReturnValue({
        data: [],
        isLoading: false,
        error: new Error('Network error'),
      } as any)

      renderNotes()

      expect(screen.getByText('Error Loading Notes')).toBeInTheDocument()
      expect(screen.getByText(/failed to load notes/i)).toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    it('should show empty state when no notes exist', () => {
      vi.mocked(apiHooks.useListNotesApiNotesGet).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      } as any)

      renderNotes()

      expect(screen.getByText(/no notes yet/i)).toBeInTheDocument()
      expect(screen.getByText(/create your first note/i)).toBeInTheDocument()
    })
  })

  describe('create note', () => {
    it('should open form dialog when Create Note button is clicked', async () => {
      const user = userEvent.setup()
      renderNotes()

      await user.click(screen.getByRole('button', { name: /create note/i }))

      await waitFor(() => {
        expect(screen.getByText('Create New Note')).toBeInTheDocument()
      })
    })
  })

  describe('game context filtering', () => {
    it('should pass game context to API call', () => {
      renderNotes()

      expect(apiHooks.useListNotesApiNotesGet).toHaveBeenCalledWith({
        game: 'poe1',
      })
    })

    it('should pass poe2 game context to API call', () => {
      vi.mocked(gameContextHook.useGameContext).mockReturnValue({
        game: 'poe2',
        setGame: vi.fn(),
      })

      renderNotes()

      expect(apiHooks.useListNotesApiNotesGet).toHaveBeenCalledWith({
        game: 'poe2',
      })
    })
  })

  describe('mutation setup', () => {
    it('should configure create mutation with success handler', () => {
      renderNotes()

      expect(apiHooks.useCreateNoteApiNotesPost).toHaveBeenCalledWith(
        expect.objectContaining({
          mutation: expect.objectContaining({
            onSuccess: expect.any(Function),
            onError: expect.any(Function),
          }),
        })
      )
    })

    it('should configure update mutation with success handler', () => {
      renderNotes()

      expect(apiHooks.useUpdateNoteApiNotesNoteIdPut).toHaveBeenCalledWith(
        expect.objectContaining({
          mutation: expect.objectContaining({
            onSuccess: expect.any(Function),
            onError: expect.any(Function),
          }),
        })
      )
    })

    it('should configure delete mutation with success handler', () => {
      renderNotes()

      expect(apiHooks.useDeleteNoteApiNotesNoteIdDelete).toHaveBeenCalledWith(
        expect.objectContaining({
          mutation: expect.objectContaining({
            onSuccess: expect.any(Function),
            onError: expect.any(Function),
          }),
        })
      )
    })
  })
})
