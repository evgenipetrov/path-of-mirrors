/**
 * Item Slot Selector Component
 *
 * Dropdown for selecting which equipment slot to upgrade.
 */

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'

interface ItemSlotSelectorProps {
  availableSlots: string[]
  selectedSlot: string | null
  onSlotChange: (slot: string) => void
  disabled?: boolean
}

export function ItemSlotSelector({
  availableSlots,
  selectedSlot,
  onSlotChange,
  disabled = false,
}: ItemSlotSelectorProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor="item-slot">Equipment Slot</Label>
      <Select value={selectedSlot || undefined} onValueChange={onSlotChange} disabled={disabled}>
        <SelectTrigger id="item-slot" className="w-full">
          <SelectValue placeholder="Select a slot to upgrade" />
        </SelectTrigger>
        <SelectContent>
          {availableSlots.length === 0 && (
            <SelectItem value="_none" disabled>
              No items found in build
            </SelectItem>
          )}
          {availableSlots.map((slot) => (
            <SelectItem key={slot} value={slot}>
              {slot}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {selectedSlot && (
        <p className="text-sm text-muted-foreground">
          Searching for upgrades for {selectedSlot}
        </p>
      )}
    </div>
  )
}
