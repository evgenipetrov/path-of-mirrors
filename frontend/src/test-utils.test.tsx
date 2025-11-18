import { describe, it, expect } from 'vitest'
import { render, screen } from './test-utils'

describe('Test Infrastructure', () => {
  it('should render a simple component', () => {
    render(<div>Hello Test</div>)
    expect(screen.getByText('Hello Test')).toBeInTheDocument()
  })

  it('should have access to testing-library matchers', () => {
    render(<button>Click me</button>)
    const button = screen.getByRole('button', { name: /click me/i })
    expect(button).toBeInTheDocument()
    expect(button).toBeVisible()
  })
})
