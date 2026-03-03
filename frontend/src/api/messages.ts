import client from './client'

export interface ListingMessage {
  id: number
  listing_id: number
  sender_id: number
  sender_email: string | null
  receiver_id: number
  content: string
  seen: boolean
  created_at: string
}

export async function getMessages(listingId: number): Promise<ListingMessage[]> {
  const { data } = await client.get(`/listings/${listingId}/messages`)
  return data
}

export async function sendMessage(listingId: number, content: string): Promise<ListingMessage> {
  const { data } = await client.post(`/listings/${listingId}/messages`, { content })
  return data
}
