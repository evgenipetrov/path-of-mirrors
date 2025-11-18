import { describe, it, expect, beforeEach, vi } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { GameProvider, useGameContext, type Game } from './useGameContext'

describe('useGameContext', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('initialization', () => {
    it('should default to poe1 when no value in localStorage', () => {
      const { result } = renderHook(() => useGameContext(), {
        wrapper: GameProvider,
      })

      expect(result.current.game).toBe('poe1')
    })

    it('should initialize from localStorage when value is poe1', () => {
      localStorage.setItem('pom-game-context', 'poe1')

      const { result } = renderHook(() => useGameContext(), {
        wrapper: GameProvider,
      })

      expect(result.current.game).toBe('poe1')
    })

    it('should initialize from localStorage when value is poe2', () => {
      localStorage.setItem('pom-game-context', 'poe2')

      const { result } = renderHook(() => useGameContext(), {
        wrapper: GameProvider,
      })

      expect(result.current.game).toBe('poe2')
    })

    it('should default to poe1 when localStorage has invalid value', () => {
      localStorage.setItem('pom-game-context', 'invalid')

      const { result } = renderHook(() => useGameContext(), {
        wrapper: GameProvider,
      })

      expect(result.current.game).toBe('poe1')
    })
  })

  describe('setGame', () => {
    it('should update game state to poe2', () => {
      const { result } = renderHook(() => useGameContext(), {
        wrapper: GameProvider,
      })

      act(() => {
        result.current.setGame('poe2')
      })

      expect(result.current.game).toBe('poe2')
    })

    it('should update game state to poe1', () => {
      localStorage.setItem('pom-game-context', 'poe2')

      const { result } = renderHook(() => useGameContext(), {
        wrapper: GameProvider,
      })

      act(() => {
        result.current.setGame('poe1')
      })

      expect(result.current.game).toBe('poe1')
    })

    it('should persist to localStorage when changing to poe2', () => {
      const { result } = renderHook(() => useGameContext(), {
        wrapper: GameProvider,
      })

      act(() => {
        result.current.setGame('poe2')
      })

      expect(localStorage.getItem('pom-game-context')).toBe('poe2')
    })

    it('should persist to localStorage when changing to poe1', () => {
      localStorage.setItem('pom-game-context', 'poe2')

      const { result } = renderHook(() => useGameContext(), {
        wrapper: GameProvider,
      })

      act(() => {
        result.current.setGame('poe1')
      })

      expect(localStorage.getItem('pom-game-context')).toBe('poe1')
    })

    it('should handle multiple setGame calls', () => {
      const { result } = renderHook(() => useGameContext(), {
        wrapper: GameProvider,
      })

      act(() => {
        result.current.setGame('poe2')
      })
      expect(result.current.game).toBe('poe2')
      expect(localStorage.getItem('pom-game-context')).toBe('poe2')

      act(() => {
        result.current.setGame('poe1')
      })
      expect(result.current.game).toBe('poe1')
      expect(localStorage.getItem('pom-game-context')).toBe('poe1')

      act(() => {
        result.current.setGame('poe2')
      })
      expect(result.current.game).toBe('poe2')
      expect(localStorage.getItem('pom-game-context')).toBe('poe2')
    })
  })

  describe('error handling', () => {
    it('should throw error when used outside GameProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => {
        renderHook(() => useGameContext())
      }).toThrow('useGameContext must be used within a GameProvider')

      consoleSpy.mockRestore()
    })
  })

  describe('provider behavior', () => {
    it('should provide context to multiple consumers', () => {
      const { result: result1 } = renderHook(() => useGameContext(), {
        wrapper: GameProvider,
      })

      const { result: result2 } = renderHook(() => useGameContext(), {
        wrapper: GameProvider,
      })

      // Both should have the same initial value
      expect(result1.current.game).toBe('poe1')
      expect(result2.current.game).toBe('poe1')
    })

    it('should maintain type safety for Game type', () => {
      const { result } = renderHook(() => useGameContext(), {
        wrapper: GameProvider,
      })

      const game: Game = result.current.game
      expect(['poe1', 'poe2']).toContain(game)
    })
  })
})
