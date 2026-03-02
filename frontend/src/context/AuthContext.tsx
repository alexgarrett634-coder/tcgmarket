import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getMe } from '../api/auth'
import { getSubscription } from '../api/billing'
import { getWallet } from '../api/wallet'
import type { User, Subscription, Wallet } from '../types'

interface AuthContextValue {
  user: User | null
  subscription: Subscription | null
  wallet: Wallet | null
  tier: 'free' | 'pro' | 'enterprise'
  isLoggedIn: boolean
  isLoading: boolean
  setTokens: (access: string, refresh: string) => void
  logout: () => void
  refetchWallet: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient()
  const [hasToken, setHasToken] = useState(() => !!localStorage.getItem('access_token'))

  const { data: user, isLoading: userLoading } = useQuery({
    queryKey: ['me'],
    queryFn: getMe,
    enabled: hasToken,
    retry: false,
  })

  const { data: subscription } = useQuery({
    queryKey: ['subscription'],
    queryFn: getSubscription,
    enabled: !!user,
    retry: false,
  })

  const { data: wallet, refetch: refetchWallet } = useQuery({
    queryKey: ['wallet'],
    queryFn: getWallet,
    enabled: !!user,
    retry: false,
  })

  function setTokens(access: string, refresh: string) {
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
    setHasToken(true)
    qc.invalidateQueries({ queryKey: ['me'] })
  }

  function logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setHasToken(false)
    qc.clear()
  }

  const tier = (subscription?.tier ?? 'free') as 'free' | 'pro' | 'enterprise'

  return (
    <AuthContext.Provider value={{
      user: user ?? null,
      subscription: subscription ?? null,
      wallet: wallet ?? null,
      tier,
      isLoggedIn: !!user,
      isLoading: hasToken && userLoading,
      setTokens,
      logout,
      refetchWallet: () => refetchWallet(),
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
