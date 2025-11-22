/**
 * API client functions for upgrade finder features.
 */

import { AXIOS_INSTANCE } from '@/lib/api-client'
import type { PoBParseRequest, PoBParseResponse, UpgradeSearchRequest, UpgradeSearchResponse } from './types'

/**
 * Parse Path of Building file or import code.
 *
 * @param request - PoB parse request with either XML or import code
 * @returns Parsed build data with items
 */
export async function parsePob(
  request: PoBParseRequest
): Promise<PoBParseResponse> {
  const { game, ...body } = request
  const { data } = await AXIOS_INSTANCE.post<PoBParseResponse>(
    `/api/v1/${game}/builds/parse`,
    body
  )

  return data
}

/**
 * Search for item upgrades.
 *
 * @param request - Upgrade search request with filters
 * @returns Ranked list of upgrade results
 */
export async function searchUpgrades(
  request: UpgradeSearchRequest
): Promise<UpgradeSearchResponse> {
  const { data } = await AXIOS_INSTANCE.post<UpgradeSearchResponse>(
    '/api/v1/upgrades/search',
    request
  )

  return data
}
