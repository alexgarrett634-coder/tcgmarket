import client from './client'
import type { Card, PricePoint, Market } from '../types'

export async function searchCards(q: string, page = 1, pageSize = 20) {
  const { data } = await client.get('/cards/search', { params: { q, page, page_size: pageSize } })
  return data as { results: Card[]; page: number; page_size: number }
}

export async function getCard(id: string) {
  const { data } = await client.get(`/cards/${id}`)
  return data as Card
}

export async function getCardPrices(id: string) {
  const { data } = await client.get(`/cards/${id}/prices`)
  return data as { current: (PricePoint & { source: string; price_type: string })[]; history: PricePoint[]; history_days: number }
}

export async function getCardMarkets(id: string) {
  const { data } = await client.get(`/cards/${id}/markets`)
  return data as Market[]
}

export async function getCardSets(language = 'en') {
  const { data } = await client.get('/cards/sets', { params: { language } })
  return data as { set_code: string; set_name: string }[]
}
