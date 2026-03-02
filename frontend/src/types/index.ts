export interface User {
  id: number
  email: string
  email_verified: boolean
  created_at: string
}

export interface Subscription {
  tier: 'free' | 'pro' | 'enterprise'
  status: string
  current_period_end: string | null
}

export interface Wallet {
  prediction_coins: number
  real_credits_usd: number
  updated_at: string
}

export interface Market {
  id: number
  title: string
  item_type: string
  card_id: string | null
  product_id: number | null
  market_type: string
  currency: 'coins' | 'usd'
  probability: number
  total_volume: number
  target_date: string
  status: string
  resolved_outcome: string | null
  trigger_signal: string | null
  created_at: string
}

export interface MarketDetail extends Market {
  description: string | null
  target_value: number | null
  resolved_price: number | null
  pool_yes: number
  pool_no: number
}

export interface MarketPosition {
  id: number
  side: 'yes' | 'no'
  shares: number
  cost: number
  currency: string
  settled: boolean
  payout: number | null
  created_at: string
}

export interface Deal {
  id: number
  item_type: string
  card_id: string | null
  card_name: string | null
  card_image: string | null
  source: string
  listing_url: string
  listed_price: number
  market_price: number
  deal_score: number
  condition: string
  seller?: string
  discovered_at: string
}

export interface Card {
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

export interface PricePoint {
  recorded_at: string
  price_usd: number
  price_type: string
}

export interface WatchlistItem {
  id: number
  item_type: string
  card_id: string | null
  product_id: number | null
  preferred_source: string
  alert_above: number | null
  alert_below: number | null
  alert_enabled: boolean
  notes: string | null
  created_at: string
}

export interface PortfolioItem {
  id: number
  item_type: string
  card_id: string | null
  product_id: number | null
  quantity: number
  condition: string
  purchase_price: number | null
  purchase_date: string | null
  current_price: number | null
  total_cost: number
  total_value: number
  pnl: number
  pnl_pct: number | null
  notes: string | null
  created_at: string
}

export interface Notification {
  id: number
  type: string
  title: string
  message: string
  link: string | null
  seen: boolean
  created_at: string
}

export interface WalletTransaction {
  id: number
  type: string
  currency: string
  amount: number
  market_id: number | null
  note: string | null
  created_at: string
}
