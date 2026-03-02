import client from './client'
import type { Wallet, WalletTransaction } from '../types'

export async function getWallet() {
  const { data } = await client.get('/wallet')
  return data as Wallet
}

export async function getTransactions(params?: { limit?: number; offset?: number }) {
  const { data } = await client.get('/wallet/transactions', { params })
  return data as WalletTransaction[]
}

export async function depositUSD(amount_usd: number) {
  const { data } = await client.post('/wallet/deposit', { amount_usd })
  return data as { client_secret: string; amount: number }
}

export async function withdrawUSD(amount_usd: number) {
  const { data } = await client.post('/wallet/withdraw', { amount_usd })
  return data
}
