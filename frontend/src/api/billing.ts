import client from './client'
import type { Subscription } from '../types'

export async function getSubscription() {
  const { data } = await client.get('/billing/subscription')
  return data as Subscription
}

export async function createCheckout(tier: 'pro' | 'enterprise') {
  const { data } = await client.post('/billing/checkout', { tier })
  return data as { url: string }
}

export async function createPortalSession() {
  const { data } = await client.post('/billing/portal')
  return data as { url: string }
}
