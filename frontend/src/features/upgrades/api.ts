/**
 * API client functions for upgrade finder features.
 */

import { AXIOS_INSTANCE } from '@/lib/api-client'
import type { PoBParseRequest, PoBParseResponse } from './types'

/**
 * Parse Path of Building file or import code.
 *
 * @param request - PoB parse request with either XML or import code
 * @returns Parsed build data with items
 */
export async function parsePob(
  request: PoBParseRequest
): Promise<PoBParseResponse> {
  console.log('Parsing PoB with request:', {
    hasXml: !!request.pob_xml,
    hasCode: !!request.pob_code,
    game: request.game,
    codeLength: request.pob_code?.length || 0,
  })

  const { data } = await AXIOS_INSTANCE.post<PoBParseResponse>(
    '/api/v1/pob/parse',
    request
  )

  console.log('Parse successful, got build:', data.name)
  return data
}
