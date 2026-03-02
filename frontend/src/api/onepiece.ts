import client from './client'
import type { PricePoint } from '../types'

export interface OpCard {
  id: string
  name: string
  set_name: string
  set_code: string
  number: string | null
  rarity: string | null
  supertype: string | null
  image_small: string | null
  image_large: string | null
}

export async function searchOpCards(q: string, page = 1, pageSize = 20) {
  const { data } = await client.get('/op/search', { params: { q, page, page_size: pageSize } })
  return data as { results: OpCard[]; page: number; page_size: number }
}

export async function getOpCard(id: string) {
  const { data } = await client.get(`/op/${id}`)
  return data as OpCard
}

export async function getOpCardPrices(id: string) {
  const { data } = await client.get(`/op/${id}/prices`)
  return data as { current: (PricePoint & { source: string; price_type: string })[]; history: PricePoint[]; history_days: number }
}

export async function getOpCardSets() {
  const { data } = await client.get('/op/sets')
  return data as { set_code: string; set_name: string }[]
}
