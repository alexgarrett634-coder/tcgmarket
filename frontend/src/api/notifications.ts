import client from './client'
import type { Notification } from '../types'

export async function getNotifications(params?: { limit?: number; offset?: number }) {
  const { data } = await client.get('/notifications', { params })
  return data as Notification[]
}

export async function getUnseenCount() {
  const { data } = await client.get('/notifications/unseen-count')
  return data as { count: number }
}

export async function markAllSeen() {
  await client.post('/notifications/mark-all-seen')
}

export async function markSeen(id: number) {
  await client.patch(`/notifications/${id}/seen`)
}
