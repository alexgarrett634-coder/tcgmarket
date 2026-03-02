import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getMarkets, subscribeMarketStream } from '../api/markets'
import MarketCard from '../components/markets/MarketCard'
import type { Market } from '../types'
import { Zap } from 'lucide-react'

const FILTERS = [
  { label: 'All', value: '' },
  { label: '🪙 Virtual', value: 'coins' },
  { label: '💵 Real Money', value: 'usd' },
]

export default function Markets() {
  const [currency, setCurrency] = useState('')
  const [liveProbs, setLiveProbs] = useState<Record<number, number>>({})

  const { data: markets, isLoading } = useQuery({
    queryKey: ['markets', currency],
    queryFn: () => getMarkets({ currency, limit: 100 }),
  })

  // Subscribe to live SSE probability stream
  useEffect(() => {
    const unsub = subscribeMarketStream((updates) => {
      setLiveProbs((prev) => {
        const next = { ...prev }
        updates.forEach((u) => { next[u.id] = u.probability })
        return next
      })
    })
    return unsub
  }, [])

  // Merge live probs into market list
  const enriched: Market[] = (markets ?? []).map((m) => ({
    ...m,
    probability: liveProbs[m.id] ?? m.probability,
  }))

  const featured = enriched.slice(0, 3)
  const rest = enriched.slice(3)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Prediction Markets</h1>
        <div className="flex gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setCurrency(f.value)}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                currency === f.value
                  ? 'bg-accent text-white'
                  : 'bg-surface text-muted hover:text-white'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-surface rounded-xl h-40 animate-pulse" />
          ))}
        </div>
      ) : (
        <>
          {featured.length > 0 && (
            <div className="mb-6">
              <p className="text-xs text-muted uppercase tracking-wider mb-3">Featured</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {featured.map((m) => <MarketCard key={m.id} market={m} featured />)}
              </div>
            </div>
          )}

          {rest.length > 0 && (
            <div>
              <p className="text-xs text-muted uppercase tracking-wider mb-3">All Markets</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {rest.map((m) => <MarketCard key={m.id} market={m} />)}
              </div>
            </div>
          )}

          {enriched.length === 0 && (
            <div className="text-center py-20 text-muted">
              <Zap size={32} className="mx-auto mb-3 opacity-40" />
              <p>No markets available yet. They are auto-generated as prices move.</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}
