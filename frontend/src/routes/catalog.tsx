import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/catalog')({
  component: () => <div>Catalog coming soon</div>,
})
