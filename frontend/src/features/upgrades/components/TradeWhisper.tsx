/**
 * Trade Whisper Component
 *
 * Button to copy Trade API whisper command to clipboard.
 */
import { useState } from 'react'
import { Copy, Check } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'

interface TradeWhisperProps {
  whisper: string
  itemName: string
}

export function TradeWhisper({ whisper, itemName }: TradeWhisperProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(whisper)
      setCopied(true)
      toast.success('Whisper copied!', {
        description: `Trade whisper for ${itemName} copied to clipboard`,
      })
      setTimeout(() => setCopied(false), 2000)
    } catch (_err) {
      toast.error('Failed to copy', {
        description: 'Could not copy whisper to clipboard',
      })
    }
  }

  return (
    <Button
      variant='outline'
      size='sm'
      onClick={handleCopy}
      className='flex items-center gap-2'
    >
      {copied ? (
        <>
          <Check className='h-4 w-4' />
          Copied!
        </>
      ) : (
        <>
          <Copy className='h-4 w-4' />
          Copy Whisper
        </>
      )}
    </Button>
  )
}
