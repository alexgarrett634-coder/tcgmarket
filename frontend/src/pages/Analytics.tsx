import { useQuery } from '@tanstack/react-query'
import client from '../api/client'
import UpgradePrompt from '../components/shared/UpgradePrompt'
import { useAuth } from '../context/AuthContext'

async function getMarketMovers() {
  const { data } = await client.get('/analytics/market-movers')
  return data as { id: number; title: string; probability: number; total_volume: number }[]
}

async function getPriceMovers() {
  const { data } = await client.get('/analytics/price-movers')
  return data as { card_id: string; min_price: number; max_price: number; change_pct: number }[]
}

export default function Analytics() {
  const { tier } = useAuth()

  const { data: marketMovers } = useQuery({ queryKey: ['market-movers'], queryFn: getMarketMovers, enabled: tier === 'enterprise' })
  const { data: priceMovers } = useQuery({ queryKey: ['price-movers'], queryFn: getPriceMovers, enabled: tier === 'enterprise' })

  if (tier !== 'enterprise') {
    return <UpgradePrompt message="Analytics is an Enterprise-exclusive feature." requiredTier="Enterprise" />
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-white">Analytics</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Market Movers */}
        <div className="bg-surface rounded-xl border border-white/5 p-4">
          <h2 className="text-sm font-semibold text-white mb-4">Top Markets by Volume</h2>
          <div className="space-y-2">
            {marketMovers?.slice(0, 10).map((m) => (
              <div key={m.id} className="flex items-center justify-between text-sm">
                <p className="text-white text-xs line-clamp-1 flex-1">{m.title}</p>
                <div className="flex items-center gap-3 shrink-0 ml-3">
                  <span className="text-muted text-xs">{m.total_volume.toLocaleString()}</span>
                  <span className="text-yes font-bold text-xs">{Math.round(m.probability * 100)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Price Movers */}
        <div className="bg-surface rounded-xl border border-white/5 p-4">
          <h2 className="text-sm font-semibold text-white mb-4">Biggest Price Moves (7d)</h2>
          <div className="space-y-2">
            {priceMovers?.slice(0, 10).map((p) => (
              <div key={p.card_id} className="flex items-center justify-between text-sm">
                <p className="text-white text-xs flex-1 truncate">{p.card_id}</p>
                <div className="flex items-center gap-3 shrink-0 ml-3">
                  <span className="text-muted text-xs">${p.min_price.toFixed(2)} → ${p.max_price.toFixed(2)}</span>
                  <span className={`font-bold text-xs ${p.change_pct >= 0 ? 'text-yes' : 'text-no'}`}>
                    {p.change_pct >= 0 ? '+' : ''}{p.change_pct.toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CSV export */}
      <div className="bg-surface rounded-xl border border-white/5 p-4">
        <h2 className="text-sm font-semibold text-white mb-4">Bulk Export</h2>
        <div className="flex gap-3">
          <a href="/api/v1/analytics/export/watchlist" className="px-4 py-2 bg-surface-2 hover:bg-white/10 text-white text-sm rounded-lg transition-colors">
            Export Watchlist CSV
          </a>
          <a href="/api/v1/analytics/export/portfolio" className="px-4 py-2 bg-surface-2 hover:bg-white/10 text-white text-sm rounded-lg transition-colors">
            Export Portfolio CSV
          </a>
        </div>
      </div>
    </div>
  )
}
