import client from './client'
import type { Market, MarketDetail, MarketPosition } from '../types'

export async function getMarkets(params?: { currency?: string; status?: string; item_type?: string; limit?: number; offset?: number }) {
  const { data } = await client.get('/markets', { params })
  return data as Market[]
}

export async function getMarket(id: number) {
  const { data } = await client.get(`/markets/${id}`)
  return data as MarketDetail
}

export async function getMyPositions(marketId: number) {
  const { data } = await client.get(`/markets/${marketId}/positions`)
  return data as MarketPosition[]
}

export async function buyPosition(marketId: number, side: 'yes' | 'no', amount: number) {
  const { data } = await client.post(`/markets/${marketId}/buy`, { side, amount })
  return data as { shares: number; probability: number; position_id: number }
}

export function subscribeMarketStream(onUpdate: (updates: { id: number; probability: number; total_volume: number }[]) => void): () => void {
  const token = localStorage.getItem('access_token')
  const url = `/api/v1/markets/stream${token ? `?token=${token}` : ''}`
  const es = new EventSource(url)
  es.onmessage = (e) => {
    try { onUpdate(JSON.parse(e.data)) } catch {}
  }
  return () => es.close()
}
