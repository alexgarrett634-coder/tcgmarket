import client from './client'
import type { Deal } from '../types'

export async function getTop5Deals() {
  const { data } = await client.get('/deals/top5')
  return data as Deal[]
}

export async function getDeals(params?: { limit?: number; offset?: number }) {
  const { data } = await client.get('/deals', { params })
  return data as Deal[]
}

export async function createDealAlert(payload: { item_type: string; card_id?: string; product_id?: number; min_deal_score?: number }) {
  const { data } = await client.post('/deals/alerts', payload)
  return data
}

export async function deleteDealAlert(alertId: number) {
  await client.delete(`/deals/alerts/${alertId}`)
}

export function subscribeDealsStream(onDeal: (deal: Deal) => void): () => void {
  const es = new EventSource('/api/v1/deals/stream')
  es.onmessage = (e) => {
    try { onDeal(JSON.parse(e.data)) } catch {}
  }
  return () => es.close()
}
