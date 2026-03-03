import client from './client'

export interface Order {
  id: number
  buyer_id: number
  seller_id: number
  listing_id: number
  quantity: number
  price_each: number
  subtotal: number
  commission_rate: number
  commission_amount: number
  payout_amount: number
  status: string  // pending, paid, shipped, completed, cancelled
  tracking_number: string | null
  shipping_address: Record<string, string> | null
  created_at: string
  paid_at: string | null
  shipped_at: string | null
  completed_at: string | null
}

export interface CreateOrderData {
  listing_id: number
  quantity: number
  shipping_address: {
    name: string
    line1: string
    line2?: string
    city: string
    state: string
    postal_code: string
    country: string
  }
}

export async function createOrder(data: CreateOrderData): Promise<{ order_id: number; client_secret: string | null; test_mode?: boolean; message?: string }> {
  const { data: res } = await client.post('/orders', data)
  return res
}

export async function checkoutIntent(data: CreateOrderData): Promise<{
  order_id: number
  client_secret: string | null
  subtotal: number
  platform_fee: number
  total: number
  fee_rate: number
  test_mode?: boolean
  message?: string
}> {
  const { data: res } = await client.post('/orders/checkout-intent', data)
  return res
}

export async function shippingLabelQuote(orderId: number, dims: {
  length_in: number; width_in: number; height_in: number; weight_oz: number
}): Promise<{ order_id: number; label_fee: number; carrier: string; service: string }> {
  const { data } = await client.post(`/orders/${orderId}/shipping-label/quote`, dims)
  return data
}

export async function createShippingLabel(orderId: number, dims: {
  length_in: number; width_in: number; height_in: number; weight_oz: number
}): Promise<{ label_id: number; order_id: number; label_fee: number; status: string; message: string }> {
  const { data } = await client.post(`/orders/${orderId}/shipping-label/create`, dims)
  return data
}

export async function getOrders(): Promise<Order[]> {
  const { data } = await client.get('/orders')
  return data
}

export async function getSellingOrders(): Promise<Order[]> {
  const { data } = await client.get('/orders/selling')
  return data
}

export async function getOrder(id: number): Promise<Order> {
  const { data } = await client.get(`/orders/${id}`)
  return data
}

export async function markShipped(id: number, tracking_number: string): Promise<Order> {
  const { data } = await client.post(`/orders/${id}/ship`, { tracking_number })
  return data
}

export async function markComplete(id: number): Promise<Order> {
  const { data } = await client.post(`/orders/${id}/complete`)
  return data
}
