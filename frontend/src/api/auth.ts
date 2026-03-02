import client from './client'
import type { User } from '../types'

export async function register(email: string, password: string) {
  const { data } = await client.post('/auth/register', { email, password })
  return data as { access_token: string; refresh_token: string }
}

export async function login(email: string, password: string) {
  const { data } = await client.post('/auth/login', { email, password })
  return data as { access_token: string; refresh_token: string }
}

export async function getMe() {
  const { data } = await client.get('/auth/me')
  return data as User
}
