import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getOpCard, getOpCardPrices } from '../api/onepiece'

const CONDITION_ORDER = ['NM', 'LP', 'MP', 'HP', 'DMG']
const CONDITION_LABEL: Record<string, string> = {
  NM: 'Near Mint',
  LP: 'Lightly Played',
  MP: 'Moderately Played',
  HP: 'Heavily Played',
  DMG: 'Damaged',
}
const CONDITION_DISCOUNT: Record<string, number> = {
  NM: 1.0,
  LP: 0.88,
  MP: 0.70,
  HP: 0.50,
  DMG: 0.30,
}
const CONDITION_COLOR: Record<string, string> = {
  NM: 'text-yes',
  LP: 'text-green-400',
  MP: 'text-yellow-400',
  HP: 'text-orange-400',
  DMG: 'text-red-400',
}

export default function OnePieceCardDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: card } = useQuery({ queryKey: ['op-card', id], queryFn: () => getOpCard(id!) })
  const { data: prices, dataUpdatedAt } = useQuery({
    queryKey: ['op-card-prices', id],
    queryFn: () => getOpCardPrices(id!),
    refetchInterval: 60_000,
  })

  if (!card) return <div className="animate-pulse h-64 bg-surface rounded-xl" />

  const nmPrice     = prices?.current?.find((p) => p.price_type === 'near_mint')?.price_usd
  const marketPrice = prices?.current?.find((p) => p.price_type === 'market')?.price_usd
  const gradedPrice = prices?.current?.find((p) => p.price_type === 'graded')?.price_usd
  const psa10Price  = prices?.current?.find((p) => p.price_type === 'psa10')?.price_usd
  const headlinePrice = nmPrice ?? marketPrice
  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : null

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-muted">
        <button onClick={() => navigate('/op')} className="hover:text-white transition-colors">One Piece</button>
        <span>/</span>
        <span className="text-white truncate">{card.name}</span>
      </div>

      {/* Card header */}
      <div className="bg-surface rounded-2xl border border-white/5 p-6">
        <div className="flex gap-6 flex-col sm:flex-row">
          {/* Card image */}
          <div className="flex-shrink-0 flex justify-center">
            {card.image_small ? (
              <img
                src={card.image_large || card.image_small}
                alt={card.name}
                className="w-44 rounded-xl shadow-lg border border-red-400/20 object-contain"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
              />
            ) : (
              <div className="w-44 h-60 bg-surface-2 rounded-xl flex flex-col items-center justify-center gap-2 border border-red-400/20">
                <div className="text-2xl">⚓</div>
                <span className="text-xs text-red-400/60 font-semibold tracking-widest uppercase">One Piece</span>
              </div>
            )}
          </div>

          {/* Card info */}
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-white leading-tight">{card.name}</h1>
            <p className="text-muted text-sm mt-1">{card.set_name}</p>
            {card.set_code && card.set_code !== card.set_name && (
              <p className="text-red-400/80 text-xs mt-0.5 font-mono">{card.set_code}</p>
            )}
            <div className="flex flex-wrap gap-1 mt-2">
              {card.rarity && <span className="px-2 py-0.5 bg-white/10 rounded text-xs text-white">{card.rarity}</span>}
              {card.supertype && card.supertype !== 'Card' && (
                <span className="px-2 py-0.5 bg-red-400/10 text-red-300 rounded text-xs">{card.supertype}</span>
              )}
            </div>

            {/* Market price */}
            <div className="mt-5">
              {headlinePrice ? (
                <>
                  <div className="text-4xl font-black text-white">${headlinePrice.toFixed(2)}</div>
                  <div className="text-xs text-muted mt-1 flex items-center gap-2">
                    Near Mint · PriceCharting
                    {lastUpdated && <span className="text-muted/60">· {lastUpdated}</span>}
                  </div>
                </>
              ) : (
                <div className="text-muted text-sm">No price data yet</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Condition price table */}
      {(headlinePrice || gradedPrice || psa10Price) && (
        <div className="bg-surface rounded-2xl border border-white/5 p-5">
          <h2 className="text-sm font-semibold text-white mb-4">Prices by Condition</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-muted border-b border-white/10">
                  <th className="text-left pb-2 font-medium">Condition</th>
                  <th className="text-right pb-2 font-medium">Market Price</th>
                  <th className="text-right pb-2 font-medium">vs NM</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {CONDITION_ORDER.map((cond) => {
                  const condPrice = cond === 'NM'
                    ? (nmPrice ?? marketPrice ?? 0)
                    : (marketPrice ?? 0) * CONDITION_DISCOUNT[cond]
                  const pct = Math.round((CONDITION_DISCOUNT[cond] - 1) * 100)
                  if (condPrice === 0) return null
                  return (
                    <tr key={cond} className="hover:bg-white/3 transition-colors">
                      <td className="py-3">
                        <span className={`font-semibold ${CONDITION_COLOR[cond]}`}>{cond}</span>
                        <span className="ml-2 text-xs text-muted hidden sm:inline">{CONDITION_LABEL[cond]}</span>
                      </td>
                      <td className="py-3 text-right font-bold text-white">${condPrice.toFixed(2)}</td>
                      <td className="py-3 text-right text-xs">
                        {cond === 'NM' ? (
                          <span className="text-muted">—</span>
                        ) : (
                          <span className="text-red-400">{pct}%</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
                {gradedPrice && (
                  <tr className="hover:bg-white/3 transition-colors border-t-2 border-white/10">
                    <td className="py-3">
                      <span className="font-semibold text-blue-400">PSA</span>
                      <span className="ml-2 text-xs text-muted hidden sm:inline">Graded (avg PSA 7–9)</span>
                    </td>
                    <td className="py-3 text-right font-bold text-white">${gradedPrice.toFixed(2)}</td>
                    <td className="py-3 text-right text-xs text-muted">graded</td>
                  </tr>
                )}
                {psa10Price && (
                  <tr className="hover:bg-white/3 transition-colors">
                    <td className="py-3">
                      <span className="font-semibold" style={{ color: '#D4AF37' }}>PSA 10</span>
                      <span className="ml-2 text-xs text-muted hidden sm:inline">Gem Mint</span>
                    </td>
                    <td className="py-3 text-right font-bold" style={{ color: '#D4AF37' }}>${psa10Price.toFixed(2)}</td>
                    <td className="py-3 text-right text-xs text-muted">gem mt</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Source note */}
      <div className="text-center text-xs text-muted py-2">
        Prices sourced from PriceCharting · Updated on last import
      </div>
    </div>
  )
}
