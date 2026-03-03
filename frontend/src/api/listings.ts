import client from './client'

export interface Listing {
  id: number
  seller_id: number
  seller_email: string | null
  item_type: 'card' | 'sealed'
  card_id: string | null
  card: {
    id: string
    name: string
    set_name: string
    rarity: string | null
    image_small: string | null
    image_large: string | null
  } | null
  product_id: number | null
  product: {
    id: number
    name: string
    set_name: string
    product_type: string
    image_url: string | null
  } | null
  title: string
  description: string | null
  condition: string
  quantity: number
  price: number
  status: string
  grade: number | null
  grading_company: string | null
  image_url: string | null
  created_at: string
}

export interface ListingsFilters {
  status?: string
  item_type?: string
  card_id?: string
  condition?: string
  price_min?: number
  price_max?: number
  search?: string
  set_code?: string
  language?: string
  limit?: number
  offset?: number
}

export async function getListings(filters: ListingsFilters = {}): Promise<Listing[]> {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== '') params.append(k, String(v))
  })
  const { data } = await client.get(`/listings?${params}`)
  return data
}

export async function getListing(id: number): Promise<Listing> {
  const { data } = await client.get(`/listings/${id}`)
  return data
}

export async function getMyListings(status = ''): Promise<Listing[]> {
  const { data } = await client.get(`/listings/mine${status ? `?status=${status}` : ''}`)
  return data
}

export interface CreateListingData {
  item_type: 'card' | 'sealed'
  card_id?: string
  product_id?: number
  title?: string
  description?: string
  condition: string
  quantity: number
  price: number
  image_url?: string
}

export async function createListing(data: CreateListingData): Promise<Listing> {
  const { data: res } = await client.post('/listings', data)
  return res
}

export async function updateListing(id: number, data: Partial<{
  price: number
  quantity: number
  description: string
  status: string
}>): Promise<Listing> {
  const { data: res } = await client.patch(`/listings/${id}`, data)
  return res
}
