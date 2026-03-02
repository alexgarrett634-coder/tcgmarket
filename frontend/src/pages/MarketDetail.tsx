import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMarket, getMyPositions } from '../api/markets'
import OrderPanel from '../components/markets/OrderPanel'
import RealMoneyDisclaimer from '../components/markets/RealMoneyDisclaimer'
import { useAuth } from '../context/AuthContext'
import { useState } from 'react'

function timeLeft(dateStr: string) {
  const diff = new Date(dateStr).getTime() - Date.now()
  if (diff < 0) return 'Expired'
  const d = Math.floor(diff / 86400000)
  const h = Math.floor((diff % 86400000) / 3600000)
  return d > 0 ? `${d}d ${h}h remaining` : `${h}h remaining`
}

export default function MarketDetail() {
  const { id } = useParams<{ id: string }>()
  const marketId = parseInt(id!)
  const { isLoggedIn, tier } = useAuth()
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(false)

  const { data: market, isLoading } = useQuery({
    queryKey: ['market', marketId],
    queryFn: () => getMarket(marketId),
    refetchInterval: 5000,
  })

  const { data: positions } = useQuery({
    queryKey: ['positions', marketId],
    queryFn: () => getMyPositions(marketId),
    enabled: isLoggedIn,
  })

  if (isLoading) return <div className="animate-pulse space-y-4"><div className="h-8 bg-surface rounded w-1/2" /><div className="h-48 bg-surface rounded" /></div>
  if (!market) return <div className="text-muted">Market not found</div>

  const yesPct = Math.round(market.probability * 100)
  const noPct = 100 - yesPct
  const isRealMoney = market.currency === 'usd'
  const showDisclaimer = isRealMoney && tier === 'enterprise' && !disclaimerAccepted

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-surface rounded-xl border border-white/5 p-6">
        <div className="flex items-center gap-2 mb-3">
          <span className={`text-xs px-2 py-0.5 rounded-full ${isRealMoney ? 'bg-green-500/10 text-green-400' : 'bg-yellow-400/10 text-yellow-400'}`}>
            {isRealMoney ? '💵 Real Money' : '🪙 Virtual'}
          </span>
          <span className="text-xs text-muted">{market.status}</span>
          <span className="ml-auto text-xs text-muted">{timeLeft(market.target_date)}</span>
        </div>
        <h1 className="text-xl font-bold text-white mb-4">{market.title}</h1>

        {/* Big probability display */}
        <div className="flex gap-4 mb-4">
          <div className="flex-1 bg-yes/10 rounded-xl p-4 text-center">
            <div className="text-3xl font-black text-yes">{yesPct}%</div>
            <div className="text-xs text-muted mt-1">YES</div>
          </div>
          <div className="flex-1 bg-no/10 rounded-xl p-4 text-center">
            <div className="text-3xl font-black text-no">{noPct}%</div>
            <div className="text-xs text-muted mt-1">NO</div>
          </div>
        </div>

        <div className="h-3 rounded-full bg-no/30 overflow-hidden">
          <div className="h-full bg-yes rounded-full transition-all duration-500" style={{ width: `${yesPct}%` }} />
        </div>

        <div className="mt-3 text-xs text-muted">
          Volume: {market.total_volume.toLocaleString()} {market.currency === 'coins' ? 'PC' : 'MC'}
          {market.target_value && (
            <> · Target: ${market.target_value.toFixed(2)}</>
          )}
        </div>

        {market.status === 'resolved' && (
          <div className={`mt-3 px-3 py-2 rounded-lg text-sm font-medium ${market.resolved_outcome === 'yes' ? 'bg-yes/10 text-yes' : 'bg-no/10 text-no'}`}>
            Resolved: {market.resolved_outcome?.toUpperCase()} at ${market.resolved_price?.toFixed(2)}
          </div>
        )}
      </div>

      {/* Order panel or disclaimer */}
      {market.status === 'open' && (
        showDisclaimer ? (
          <RealMoneyDisclaimer onAccept={() => setDisclaimerAccepted(true)} />
        ) : (
          <OrderPanel marketId={marketId} currency={market.currency} />
        )
      )}

      {/* My positions */}
      {positions && positions.length > 0 && (
        <div className="bg-surface rounded-xl border border-white/5 p-4">
          <h3 className="text-sm font-semibold text-white mb-3">My Positions</h3>
          <div className="space-y-2">
            {positions.map((p) => (
              <div key={p.id} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className={p.side === 'yes' ? 'text-yes' : 'text-no'}>{p.side.toUpperCase()}</span>
                  <span className="text-muted">{p.shares.toFixed(4)} shares</span>
                </div>
                <div className="text-right">
                  <span className="text-muted">Cost: {p.cost} {p.currency === 'coins' ? 'PC' : 'MC'}</span>
                  {p.settled && <span className="ml-2 text-xs text-yes">Payout: {p.payout?.toFixed(2)}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
