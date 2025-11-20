import { defineConfig } from 'orval'

export default defineConfig({
  pathOfMirrors: {
    input: {
      // Override with OPENAPI_URL env if needed
      target: process.env.OPENAPI_URL || 'http://localhost:8000/openapi.json',
    },
    output: {
      target: 'src/hooks/api/generated',
      client: 'react-query',
      mode: 'split',
      clean: true,
      prettier: true,
      override: {
        mutator: {
          path: './src/lib/api-client.ts',
          name: 'apiClient',
        },
      },
    },
  },
})
