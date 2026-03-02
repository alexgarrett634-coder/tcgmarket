import { useNavigate } from 'react-router-dom'
import type { Market } from '../../types'
import { Zap, TrendingUp, Droplets } from 'lucide-react'

function SignalIcon({ signal }: { signal: string | null }) {
  if (signal?.includes('spike') || signal?.includes('crash'))
    return <TrendingUp size={14} className="text-gold" />
  if (signal?.includes('volume'))
    return <Droplets size={14} className="text-blue-400" />
  return <Zap size={14} className="text-accent" />
}

function timeLeft(dateStr: string) {
  const diff = new Date(dateStr).getTime() - Date.now()
  if (diff < 0) return 'Expired'
  const d = Math.floor(diff / 86400000)
  const h = Math.floor((diff % 86400000) / 3600000)
  if (d > 0) return `${d}d ${h}h`
  const m = Math.floor((diff % 3600000) / 60000)
  return `${h}h ${m}m`
}

interface Props {
  market: Market
  featured?: boolean
}

export default function MarketCard({ market, featured }: Props) {
  const navigate = useNavigate()
  const yesPct = Math.round(market.probability * 100)
  const noPct = 100 - yesPct

  return (
    <div
      onClick={() => navigate(`/markets/${market.id}`)}
      className={`relative rounded-xl border border-white/5 p-4 cursor-pointer transition-all hover:shadow-red-glow hover:border-accent/30 ${
        featured ? 'holo' : 'bg-surface'
      }`}
    >
      {/* Signal + currency badges */}
      <div className="flex items-center gap-2 mb-3">
        <SignalIcon signal={market.trigger_signal} />
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
          market.currency === 'coins'
            ? 'bg-yellow-400/10 text-yellow-400'
            : 'bg-green-500/10 text-green-400'
        }`}>
          {market.currency === 'coins' ? 'Virtual' : 'Real Money'}
        </span>
        <span className="ml-auto text-xs text-muted">{timeLeft(market.target_date)}</span>
      </div>

      {/* Title */}
      <p className="text-sm font-medium text-white leading-snug mb-4 line-clamp-2">
        {market.title}
      </p>

      {/* YES/NO probability bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs font-bold">
          <span className="text-yes">YES {yesPct}%</span>
          <span className="text-no">NO {noPct}%</span>
        </div>
        <div className="h-2 rounded-full bg-no/30 overflow-hidden">
          <div
            className="h-full bg-yes rounded-full transition-all duration-500"
            style={{ width: `${yesPct}%` }}
          />
        </div>
      </div>

      {/* Volume */}
      <div className="mt-3 text-xs text-muted">
        Vol: {market.total_volume.toLocaleString()} {market.currency === 'coins' ? 'PC' : 'MC'}
      </div>
    </div>
  )
}
