import { createFileRoute } from '@tanstack/react-router'
import { UnauthorisedError } from '@/features/errors/unauthorized-error'

// Search params type for redirect
type SignInSearch = {
  redirect?: string
}

export const Route = createFileRoute('/sign-in')({
  component: SignInPage,
  validateSearch: (search: Record<string, unknown>): SignInSearch => {
    return {
      redirect:
        typeof search.redirect === 'string' ? search.redirect : undefined,
    }
  },
})

function SignInPage() {
  // For now, show unauthorized error page
  // TODO: Implement actual sign-in page
  return <UnauthorisedError />
}
