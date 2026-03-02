import client from './client'

export interface SellerProfile {
  is_seller: boolean
  onboarding_complete: boolean
  stripe_account_id: string | null
  active_listings: number
  sold_listings: number
  total_earnings: number
}

export async function onboardSeller(): Promise<{ onboarding_url: string | null; onboarding_complete: boolean; test_mode?: boolean; message?: string }> {
  const { data } = await client.post('/sellers/onboard')
  return data
}

export async function getMySellerProfile(): Promise<SellerProfile> {
  const { data } = await client.get('/sellers/me')
  return data
}

export async function getStripeDashboardLink(): Promise<{ url: string }> {
  const { data } = await client.get('/sellers/me/dashboard-link')
  return data
}
