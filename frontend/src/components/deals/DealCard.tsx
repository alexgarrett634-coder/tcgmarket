import { useNavigate } from 'react-router-dom'
import type { Deal } from '../../types'

function scoreClass(score: number) {
  if (score >= 40) return 'text-white bg-gold deal-exceptional'
  if (score >= 25) return 'text-white bg-gold/80'
  return 'text-white bg-yes/70'
}

function scoreLabel(score: number) {
  if (score >= 40) return 'Exceptional'
  if (score >= 25) return 'Great'
  return 'Good'
}

function CardPlaceholder() {
  return (
    <svg viewBox="0 0 48 64" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-12 h-16">
      <rect width="48" height="64" rx="3" fill="#2a2a38"/>
      <rect x="4" y="4" width="40" height="36" rx="2" fill="#333344"/>
      <rect x="4" y="46" width="26" height="4" rx="2" fill="#3a3a4e"/>
      <rect x="4" y="54" width="18" height="3" rx="2" fill="#333344"/>
    </svg>
  )
}

interface Props {
  deal: Deal
}

export default function DealCard({ deal }: Props) {
  const navigate = useNavigate()
  const savings = deal.market_price - deal.listed_price
  const displayName = deal.card_name ?? deal.card_id ?? 'Product'
  const isInternal = deal.source === 'internal'

  const handleView = (e: React.MouseEvent) => {
    e.preventDefault()
    if (isInternal) {
      navigate(deal.listing_url)
    } else {
      window.open(deal.listing_url, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div className="bg-surface rounded-xl border border-white/5 p-4 hover:border-accent/20 transition-colors">
      <div className="flex items-start gap-3">
        {/* Card image */}
        {deal.card_image ? (
          <img
            src={deal.card_image}
            alt={displayName}
            className="w-12 h-16 object-contain rounded flex-shrink-0"
          />
        ) : (
          <div className="flex-shrink-0"><CardPlaceholder /></div>
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${scoreClass(deal.deal_score)}`}>
              {scoreLabel(deal.deal_score)} {deal.deal_score.toFixed(0)}% off
            </span>
            <span className="text-xs text-muted capitalize">{isInternal ? 'Marketplace' : deal.source}</span>
          </div>
          <p className="text-sm font-semibold text-white truncate">{displayName}</p>
          {deal.condition && <p className="text-xs text-muted">{deal.condition}</p>}
        </div>

        <div className="text-right shrink-0">
          <div className="text-lg font-bold text-white">${deal.listed_price.toFixed(2)}</div>
          <div className="text-xs text-muted line-through">${deal.market_price.toFixed(2)}</div>
          <div className="text-xs text-yes">Save ${savings.toFixed(2)}</div>
        </div>
      </div>

      <button
        onClick={handleView}
        className="mt-3 block w-full text-center py-1.5 text-xs font-medium bg-accent/10 hover:bg-accent/20 text-accent rounded-lg transition-colors"
      >
        {isInternal ? 'View on Marketplace →' : 'View Listing →'}
      </button>
    </div>
  )
}
