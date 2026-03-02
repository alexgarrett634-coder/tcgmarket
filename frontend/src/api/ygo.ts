import client from './client'
import type { PricePoint } from '../types'

export interface YgoCard {
  id: string
  name: string
  set_name: string
  set_code: string
  number: string | null
  rarity: string | null
  supertype: string | null
  subtypes: string | null
  image_small: string | null
  image_large: string | null
  // enriched from ygoprodeck
  attribute: string | null
  race: string | null
  atk: number | null
  def: number | null
  desc: string | null
}

export async function searchYgoCards(q: string, page = 1, pageSize = 20) {
  const { data } = await client.get('/ygo/search', { params: { q, page, page_size: pageSize } })
  return data as { results: YgoCard[]; page: number; page_size: number }
}

export async function getYgoCard(id: string) {
  const { data } = await client.get(`/ygo/${id}`)
  return data as YgoCard
}

export async function getYgoCardPrices(id: string) {
  const { data } = await client.get(`/ygo/${id}/prices`)
  return data as { current: (PricePoint & { source: string; price_type: string })[]; history: PricePoint[]; history_days: number }
}

export async function getYgoCardSets() {
  const { data } = await client.get('/ygo/sets')
  return data as { set_code: string; set_name: string }[]
}
