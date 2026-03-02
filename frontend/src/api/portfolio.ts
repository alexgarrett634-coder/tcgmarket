import client from './client'
import type { PortfolioItem } from '../types'

export async function getPortfolio() {
  const { data } = await client.get('/portfolio')
  return data as { items: PortfolioItem[]; summary: { total_cost: number; total_value: number; total_pnl: number; total_pnl_pct: number | null } }
}

export async function addPortfolioItem(payload: Partial<PortfolioItem>) {
  const { data } = await client.post('/portfolio', payload)
  return data as { id: number }
}

export async function updatePortfolioItem(id: number, payload: Partial<PortfolioItem>) {
  const { data } = await client.patch(`/portfolio/${id}`, payload)
  return data
}

export async function deletePortfolioItem(id: number) {
  await client.delete(`/portfolio/${id}`)
}
