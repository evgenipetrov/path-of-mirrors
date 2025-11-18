import { test, expect } from '@playwright/test'

test.describe('Game Context Switching', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto('/notes')
    await page.evaluate(() => localStorage.clear())
    await page.reload()
    await page.waitForLoadState('networkidle')
  })

  test('should default to POE1 on first visit', async ({ page }) => {
    // Check that page shows POE1 context
    await expect(page.getByText(/POE1/i)).toBeVisible()

    // Verify localStorage has poe1
    const gameContext = await page.evaluate(() => localStorage.getItem('pom-game-context'))
    expect(gameContext).toBe('poe1')
  })

  test('should persist game selection to localStorage', async ({ page }) => {
    // TODO: This test will be implemented once game selector UI is added
    // For now, we can verify localStorage behavior programmatically

    // Set game context via localStorage
    await page.evaluate(() => localStorage.setItem('pom-game-context', 'poe2'))

    // Reload page
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Verify POE2 is shown
    await expect(page.getByText(/POE2/i)).toBeVisible()

    // Verify localStorage still has poe2
    const gameContext = await page.evaluate(() => localStorage.getItem('pom-game-context'))
    expect(gameContext).toBe('poe2')
  })

  test('should filter notes by game context', async ({ page }) => {
    const timestamp = Date.now()
    const poe1Title = `POE1 Note ${timestamp}`
    const poe2Title = `POE2 Note ${timestamp}`

    // Create a note for POE1
    await page.evaluate(() => localStorage.setItem('pom-game-context', 'poe1'))
    await page.reload()
    await page.waitForLoadState('networkidle')

    await page.getByRole('button', { name: /create note/i }).click()
    await page.getByLabel(/title/i).fill(poe1Title)
    await page.getByRole('button', { name: /^create note$/i }).click()
    await expect(page.getByText(/note created successfully/i)).toBeVisible()

    // Switch to POE2
    await page.evaluate(() => localStorage.setItem('pom-game-context', 'poe2'))
    await page.reload()
    await page.waitForLoadState('networkidle')

    // POE1 note should not be visible
    await expect(page.getByText(poe1Title)).not.toBeVisible()

    // Create a note for POE2
    await page.getByRole('button', { name: /create note/i }).click()
    await page.getByLabel(/title/i).fill(poe2Title)
    await page.getByRole('button', { name: /^create note$/i }).click()
    await expect(page.getByText(/note created successfully/i)).toBeVisible()

    // POE2 note should be visible
    await expect(page.getByText(poe2Title)).toBeVisible()

    // Switch back to POE1
    await page.evaluate(() => localStorage.setItem('pom-game-context', 'poe1'))
    await page.reload()
    await page.waitForLoadState('networkidle')

    // POE1 note should be visible
    await expect(page.getByText(poe1Title)).toBeVisible()

    // POE2 note should not be visible
    await expect(page.getByText(poe2Title)).not.toBeVisible()
  })

  test('should persist game context across page refreshes', async ({ page }) => {
    // Set to POE2
    await page.evaluate(() => localStorage.setItem('pom-game-context', 'poe2'))
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Verify POE2 is shown
    await expect(page.getByText(/POE2/i)).toBeVisible()

    // Refresh multiple times
    for (let i = 0; i < 3; i++) {
      await page.reload()
      await page.waitForLoadState('networkidle')

      // Should still show POE2
      await expect(page.getByText(/POE2/i)).toBeVisible()

      // Verify localStorage
      const gameContext = await page.evaluate(() => localStorage.getItem('pom-game-context'))
      expect(gameContext).toBe('poe2')
    }
  })

  test('should maintain game context when navigating between pages', async ({ page }) => {
    // Set to POE2
    await page.evaluate(() => localStorage.setItem('pom-game-context', 'poe2'))
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Verify POE2
    await expect(page.getByText(/POE2/i)).toBeVisible()

    // Navigate to home
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Navigate back to notes
    await page.goto('/notes')
    await page.waitForLoadState('networkidle')

    // Should still be POE2
    await expect(page.getByText(/POE2/i)).toBeVisible()

    const gameContext = await page.evaluate(() => localStorage.getItem('pom-game-context'))
    expect(gameContext).toBe('poe2')
  })

  test('should create notes with correct game context', async ({ page }) => {
    const timestamp = Date.now()

    // Test creating note in POE1
    await page.evaluate(() => localStorage.setItem('pom-game-context', 'poe1'))
    await page.reload()
    await page.waitForLoadState('networkidle')

    const poe1Title = `POE1 Context Note ${timestamp}`
    await page.getByRole('button', { name: /create note/i }).click()
    await page.getByLabel(/title/i).fill(poe1Title)

    // Dialog should show POE1 in description
    await expect(page.getByText(/create a new note for POE1/i)).toBeVisible()

    await page.getByRole('button', { name: /^create note$/i }).click()
    await expect(page.getByText(/note created successfully/i)).toBeVisible()

    // Test creating note in POE2
    await page.evaluate(() => localStorage.setItem('pom-game-context', 'poe2'))
    await page.reload()
    await page.waitForLoadState('networkidle')

    const poe2Title = `POE2 Context Note ${timestamp}`
    await page.getByRole('button', { name: /create note/i }).click()
    await page.getByLabel(/title/i).fill(poe2Title)

    // Dialog should show POE2 in description
    await expect(page.getByText(/create a new note for POE2/i)).toBeVisible()

    await page.getByRole('button', { name: /^create note$/i }).click()
    await expect(page.getByText(/note created successfully/i)).toBeVisible()

    // Verify filtering works
    await expect(page.getByText(poe2Title)).toBeVisible()
    await expect(page.getByText(poe1Title)).not.toBeVisible()

    // Switch back and verify
    await page.evaluate(() => localStorage.setItem('pom-game-context', 'poe1'))
    await page.reload()
    await page.waitForLoadState('networkidle')

    await expect(page.getByText(poe1Title)).toBeVisible()
    await expect(page.getByText(poe2Title)).not.toBeVisible()
  })

  test('should handle invalid game context gracefully', async ({ page }) => {
    // Set invalid game context
    await page.evaluate(() => localStorage.setItem('pom-game-context', 'invalid-game'))
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Should default to POE1 (or show some game context)
    const hasValidGame = await page.getByText(/POE[12]/i).isVisible()
    expect(hasValidGame).toBe(true)
  })
})
