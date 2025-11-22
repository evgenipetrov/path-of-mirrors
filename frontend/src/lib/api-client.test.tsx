import type { ReactNode } from 'react'
import { QueryClient } from '@tanstack/react-query'
import { QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import MockAdapter from 'axios-mock-adapter'
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { useNotesHealthApiV1GameNotesHealthGet } from '../hooks/api/generated/pathOfMirrors'
import { createTestQueryClient } from '../test-utils'
import { AXIOS_INSTANCE, apiClient } from './api-client'

describe('API Client', () => {
  let mock: MockAdapter
  let queryClient: QueryClient

  beforeEach(() => {
    mock = new MockAdapter(AXIOS_INSTANCE)
    queryClient = createTestQueryClient()
  })

  afterEach(() => {
    mock.reset()
    queryClient.clear()
  })

  describe('apiClient function', () => {
    it('should accept AxiosRequestConfig and return response data', async () => {
      const mockData = { status: 'healthy', timestamp: '2025-01-01T00:00:00Z' }
      mock.onGet('/api/v1/poe1/notes/health').reply(200, mockData)

      const result = await apiClient({
        url: '/api/v1/poe1/notes/health',
        method: 'GET',
      })

      expect(result).toEqual(mockData)
    })

    it('should merge config with options parameter', async () => {
      const mockData = { status: 'healthy' }
      mock.onGet('/test').reply((config) => {
        expect(config.headers?.['X-Custom-Header']).toBe('test-value')
        return [200, mockData]
      })

      await apiClient(
        { url: '/test', method: 'GET' },
        { headers: { 'X-Custom-Header': 'test-value' } }
      )
    })

    it('should support cancellation', async () => {
      mock.onGet('/slow-endpoint').reply(
        () =>
          new Promise((resolve) => {
            setTimeout(() => resolve([200, { data: 'slow' }]), 1000)
          })
      )

      const promise = apiClient({ url: '/slow-endpoint', method: 'GET' })

      // @ts-expect-error - cancel is added to promise
      promise.cancel()

      await expect(promise).rejects.toThrow('Query was cancelled')
    })

    it('should handle errors', async () => {
      mock.onGet('/error').reply(500, { detail: 'Internal Server Error' })

      await expect(
        apiClient({ url: '/error', method: 'GET' })
      ).rejects.toThrow()
    })
  })

  describe('Generated hooks integration', () => {
    it('should work with useNotesHealthApiV1GameNotesHealthGet hook', async () => {
      const mockData = {
        status: 'healthy',
        timestamp: '2025-01-01T00:00:00Z',
        context: 'notes',
      }

      mock.onGet('/api/v1/poe1/notes/health').reply(200, mockData)

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )

      const { result } = renderHook(
        () => useNotesHealthApiV1GameNotesHealthGet('poe1'),
        { wrapper }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(result.current.data).toEqual(mockData)
    })

    it('should handle hook errors gracefully', async () => {
      mock.onGet('/api/v1/poe1/notes/health').reply(404, {
        detail: 'Not Found',
      })

      const wrapper = ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )

      const { result } = renderHook(
        () => useNotesHealthApiV1GameNotesHealthGet('poe1'),
        { wrapper }
      )

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toBeDefined()
    })
  })
})
