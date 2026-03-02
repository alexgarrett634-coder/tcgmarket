import client from './client'
import type { WatchlistItem } from '../types'

export async function getWatchlist() {
  const { data } = await client.get('/watchlist')
  return data as WatchlistItem[]
}

export async function addToWatchlist(payload: Partial<WatchlistItem>) {
  const { data } = await client.post('/watchlist', payload)
  return data as { id: number }
}

export async function updateWatchlistItem(id: number, payload: Partial<WatchlistItem>) {
  const { data } = await client.patch(`/watchlist/${id}`, payload)
  return data
}

export async function removeFromWatchlist(id: number) {
  await client.delete(`/watchlist/${id}`)
}
