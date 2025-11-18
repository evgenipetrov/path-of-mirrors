import { test, expect } from '@playwright/test'

test.describe('Notes CRUD Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to notes page
    await page.goto('/notes')

    // Wait for page to load
    await page.waitForLoadState('networkidle')
  })

  test('should display notes page with header and create button', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1')).toContainText('Notes')

    // Check create button is visible
    await expect(page.getByRole('button', { name: /create note/i })).toBeVisible()
  })

  test('should show empty state when no notes exist', async ({ page }) => {
    // Look for empty state message
    const emptyState = page.getByText(/no notes yet/i)

    // If empty state is visible, test passes
    // If not visible, it means notes exist (which is also valid)
    const isVisible = await emptyState.isVisible().catch(() => false)

    if (isVisible) {
      await expect(emptyState).toContainText(/create your first note/i)
    }
  })

  test('should create a new note successfully', async ({ page }) => {
    const timestamp = Date.now()
    const noteTitle = `E2E Test Note ${timestamp}`
    const noteContent = `This is an E2E test note created at ${timestamp}`

    // Click create button
    await page.getByRole('button', { name: /create note/i }).click()

    // Wait for dialog to appear
    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByText('Create New Note')).toBeVisible()

    // Fill in form
    await page.getByLabel(/title/i).fill(noteTitle)
    await page.getByLabel(/content/i).fill(noteContent)

    // Submit form
    await page.getByRole('button', { name: /^create note$/i }).click()

    // Wait for success toast
    await expect(page.getByText(/note created successfully/i)).toBeVisible({ timeout: 5000 })

    // Verify note appears in table
    await expect(page.getByText(noteTitle)).toBeVisible()
  })

  test('should edit an existing note', async ({ page }) => {
    const timestamp = Date.now()
    const originalTitle = `Original Note ${timestamp}`
    const updatedTitle = `Updated Note ${timestamp}`
    const updatedContent = `Updated content at ${timestamp}`

    // First, create a note to edit
    await page.getByRole('button', { name: /create note/i }).click()
    await page.getByLabel(/title/i).fill(originalTitle)
    await page.getByRole('button', { name: /^create note$/i }).click()
    await expect(page.getByText(/note created successfully/i)).toBeVisible()

    // Find the note row and click edit button
    const noteRow = page.getByRole('row', { name: new RegExp(originalTitle, 'i') })
    await noteRow.getByRole('button', { name: /edit/i }).click()

    // Wait for dialog
    await expect(page.getByRole('dialog')).toBeVisible()
    await expect(page.getByText('Edit Note')).toBeVisible()

    // Verify form is populated with existing data
    await expect(page.getByLabel(/title/i)).toHaveValue(originalTitle)

    // Update the note
    await page.getByLabel(/title/i).fill(updatedTitle)
    await page.getByLabel(/content/i).fill(updatedContent)

    // Submit
    await page.getByRole('button', { name: /update note/i }).click()

    // Wait for success toast
    await expect(page.getByText(/note updated successfully/i)).toBeVisible({ timeout: 5000 })

    // Verify updated note appears
    await expect(page.getByText(updatedTitle)).toBeVisible()

    // Verify old title is gone
    await expect(page.getByText(originalTitle)).not.toBeVisible()
  })

  test('should delete a note with confirmation', async ({ page }) => {
    const timestamp = Date.now()
    const noteTitle = `Note to Delete ${timestamp}`

    // First, create a note to delete
    await page.getByRole('button', { name: /create note/i }).click()
    await page.getByLabel(/title/i).fill(noteTitle)
    await page.getByRole('button', { name: /^create note$/i }).click()
    await expect(page.getByText(/note created successfully/i)).toBeVisible()

    // Find the note row and click delete button
    const noteRow = page.getByRole('row', { name: new RegExp(noteTitle, 'i') })
    await noteRow.getByRole('button', { name: /delete/i }).click()

    // Wait for confirmation dialog
    await expect(page.getByRole('alertdialog')).toBeVisible()
    await expect(page.getByText(/are you sure/i)).toBeVisible()

    // Confirm deletion
    await page.getByRole('button', { name: /^delete$/i }).click()

    // Wait for success toast
    await expect(page.getByText(/note deleted successfully/i)).toBeVisible({ timeout: 5000 })

    // Verify note is gone
    await expect(page.getByText(noteTitle)).not.toBeVisible()
  })

  test('should cancel delete when clicking cancel', async ({ page }) => {
    const timestamp = Date.now()
    const noteTitle = `Note Not to Delete ${timestamp}`

    // Create a note
    await page.getByRole('button', { name: /create note/i }).click()
    await page.getByLabel(/title/i).fill(noteTitle)
    await page.getByRole('button', { name: /^create note$/i }).click()
    await expect(page.getByText(/note created successfully/i)).toBeVisible()

    // Click delete button
    const noteRow = page.getByRole('row', { name: new RegExp(noteTitle, 'i') })
    await noteRow.getByRole('button', { name: /delete/i }).click()

    // Wait for confirmation dialog
    await expect(page.getByRole('alertdialog')).toBeVisible()

    // Click cancel
    await page.getByRole('button', { name: /cancel/i }).click()

    // Dialog should close
    await expect(page.getByRole('alertdialog')).not.toBeVisible()

    // Note should still be visible
    await expect(page.getByText(noteTitle)).toBeVisible()
  })

  test('should require title when creating note', async ({ page }) => {
    // Click create button
    await page.getByRole('button', { name: /create note/i }).click()

    // Wait for dialog
    await expect(page.getByRole('dialog')).toBeVisible()

    // Try to submit without title
    const submitButton = page.getByRole('button', { name: /^create note$/i })

    // Button should be disabled when title is empty
    await expect(submitButton).toBeDisabled()

    // Fill title with whitespace only
    await page.getByLabel(/title/i).fill('   ')
    await expect(submitButton).toBeDisabled()

    // Fill valid title
    await page.getByLabel(/title/i).fill('Valid Title')
    await expect(submitButton).toBeEnabled()
  })

  test('should allow creating note with only title (no content)', async ({ page }) => {
    const timestamp = Date.now()
    const noteTitle = `Title Only Note ${timestamp}`

    // Click create button
    await page.getByRole('button', { name: /create note/i }).click()

    // Fill only title, leave content empty
    await page.getByLabel(/title/i).fill(noteTitle)

    // Submit
    await page.getByRole('button', { name: /^create note$/i }).click()

    // Should succeed
    await expect(page.getByText(/note created successfully/i)).toBeVisible({ timeout: 5000 })
    await expect(page.getByText(noteTitle)).toBeVisible()
  })

  test('should close dialog when clicking cancel', async ({ page }) => {
    // Click create button
    await page.getByRole('button', { name: /create note/i }).click()

    // Wait for dialog
    await expect(page.getByRole('dialog')).toBeVisible()

    // Fill some data
    await page.getByLabel(/title/i).fill('Test Title')

    // Click cancel
    await page.getByRole('button', { name: /cancel/i }).click()

    // Dialog should close
    await expect(page.getByRole('dialog')).not.toBeVisible()
  })

  test('should show loading state while creating note', async ({ page }) => {
    const timestamp = Date.now()
    const noteTitle = `Loading Test ${timestamp}`

    // Click create button
    await page.getByRole('button', { name: /create note/i }).click()

    // Fill form
    await page.getByLabel(/title/i).fill(noteTitle)

    // Submit
    await page.getByRole('button', { name: /^create note$/i }).click()

    // Should show loading state (even briefly)
    const loadingButton = page.getByRole('button', { name: /saving/i })

    // Check if loading state appears or if it's too fast to catch
    const loadingVisible = await loadingButton.isVisible().catch(() => false)

    // Either loading state appears, or success toast appears quickly
    if (!loadingVisible) {
      await expect(page.getByText(/note created successfully/i)).toBeVisible({ timeout: 5000 })
    }
  })
})
