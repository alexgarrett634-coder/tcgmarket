import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getDeals, subscribeDealsStream } from '../api/deals'
import DealCard from '../components/deals/DealCard'
import type { Deal } from '../types'
import { Search } from 'lucide-react'

export default function Deals() {
  const [liveDeal, setLiveDeal] = useState<Deal | null>(null)

  const { data: deals, isLoading } = useQuery({
    queryKey: ['deals'],
    queryFn: () => getDeals({ limit: 100 }),
    refetchInterval: 60_000,
  })

  useEffect(() => {
    const unsub = subscribeDealsStream((deal) => {
      setLiveDeal(deal)
      setTimeout(() => setLiveDeal(null), 5000)
    })
    return unsub
  }, [])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Deals Finder</h1>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-yes rounded-full animate-pulse" />
          <span className="text-xs text-yes">Live</span>
        </div>
      </div>

      {/* Live deal toast */}
      {liveDeal && (
        <div className="mb-4 px-4 py-3 bg-gold/10 border border-gold/30 rounded-xl text-sm flex items-center gap-3">
          <span className="text-gold font-semibold text-xs">New deal</span>
          <span className="text-white">{liveDeal.deal_score.toFixed(0)}% off · ${liveDeal.listed_price.toFixed(2)}</span>
          <a href={liveDeal.listing_url} target="_blank" rel="noopener noreferrer" className="ml-auto text-accent text-xs hover:underline">View →</a>
        </div>
      )}

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(9)].map((_, i) => <div key={i} className="bg-surface rounded-xl h-36 animate-pulse" />)}
        </div>
      ) : deals && deals.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {deals.map((d) => <DealCard key={d.id} deal={d} />)}
        </div>
      ) : (
        <div className="text-center py-20 text-muted">
          <Search size={32} className="mx-auto mb-3 opacity-40" />
          <p>No deals found yet. The scanner runs every 60 seconds.</p>
        </div>
      )}
    </div>
  )
}
