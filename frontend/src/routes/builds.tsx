import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/builds')({
  component: () => <div>Builds coming soon</div>,
})
