import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getCard, getCardPrices } from '../api/cards'
import { getListings } from '../api/listings'
import PriceHistoryChart from '../components/charts/PriceHistoryChart'
import { ShoppingCart } from 'lucide-react'

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

export default function CardDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: card } = useQuery({ queryKey: ['card', id], queryFn: () => getCard(id!) })
  const { data: prices, dataUpdatedAt } = useQuery({
    queryKey: ['card-prices', id],
    queryFn: () => getCardPrices(id!),
    refetchInterval: 60_000,
  })
  const { data: listings } = useQuery({
    queryKey: ['listings-for-card', id],
    queryFn: () => getListings({ card_id: id, status: 'active', limit: 10 }),
  })

  if (!card) return <div className="animate-pulse h-64 bg-surface rounded-xl" />

  function pickPrice(type: string) {
    return (prices?.current?.find((p) => p.price_type === type && p.source === 'pricecharting')
         ?? prices?.current?.find((p) => p.price_type === type))?.price_usd
  }
  const nmPrice     = pickPrice('near_mint')
  const marketPrice = pickPrice('market')
  const gradedPrice = pickPrice('graded')
  const psa10Price  = pickPrice('psa10')
  const headlinePrice = nmPrice ?? marketPrice
  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt).toLocaleTimeString() : null
  const lowestListing = listings && listings.length > 0 ? Math.min(...listings.map((l) => l.price)) : null

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-muted">
        <button onClick={() => navigate('/prices')} className="hover:text-white transition-colors">Prices</button>
        <span>/</span>
        <span className="text-white truncate">{card.name}</span>
      </div>

      {/* Card header */}
      <div className="bg-surface rounded-2xl border border-white/5 p-6">
        <div className="flex gap-6 flex-col sm:flex-row">
          {/* Card image */}
          <div className="flex-shrink-0 flex justify-center">
            {card.image_large ? (
              <img src={card.image_large} alt={card.name}
                className="w-44 rounded-xl object-contain shadow-lg" />
            ) : (
              <div className="w-44 h-60 bg-surface-2 rounded-xl flex items-center justify-center">
                <svg viewBox="0 0 60 84" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-20 h-28 opacity-40">
                  <rect width="60" height="84" rx="4" fill="#2a2a38"/>
                  <rect x="6" y="6" width="48" height="48" rx="2" fill="#333344"/>
                  <rect x="6" y="62" width="32" height="5" rx="2" fill="#3a3a4e"/>
                  <rect x="6" y="71" width="20" height="4" rx="2" fill="#333344"/>
                </svg>
              </div>
            )}
          </div>

          {/* Card info */}
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-white leading-tight">{card.name}</h1>
            <p className="text-muted text-sm mt-1">{card.set_name} · #{card.number}</p>
            <div className="flex flex-wrap gap-1 mt-2">
              {card.rarity && <span className="px-2 py-0.5 bg-white/10 rounded text-xs text-white">{card.rarity}</span>}
              {card.supertype && <span className="px-2 py-0.5 bg-white/10 rounded text-xs text-white">{card.supertype}</span>}
            </div>

            {/* Market price */}
            <div className="mt-5">
              {headlinePrice ? (
                <>
                  <div className="flex items-baseline gap-3">
                    <div className="text-4xl font-black text-white">${headlinePrice.toFixed(2)}</div>
                  </div>
                  <div className="text-xs text-muted mt-1 flex items-center gap-2">
                    Near Mint · PriceCharting
                    {lastUpdated && <span className="text-muted/60">· {lastUpdated}</span>}
                  </div>
                </>
              ) : (
                <div className="text-muted text-sm">No price data yet</div>
              )}
            </div>

            {/* Buy button */}
            {lowestListing !== null && (
              <button
                onClick={() => document.getElementById('listings-section')?.scrollIntoView({ behavior: 'smooth' })}
                className="mt-4 px-5 py-2.5 bg-accent hover:bg-accent-hover text-white text-sm font-semibold rounded-xl transition-colors"
              >
                Buy from ${lowestListing.toFixed(2)}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Condition price table */}
      {(headlinePrice || gradedPrice) && (
        <div className="bg-surface rounded-2xl border border-white/5 p-5">
          <h2 className="text-sm font-semibold text-white mb-4">Prices by Condition</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-muted border-b border-white/10">
                  <th className="text-left pb-2 font-medium">Condition</th>
                  <th className="text-right pb-2 font-medium">Market Price</th>
                  <th className="text-right pb-2 font-medium">vs NM</th>
                  <th className="text-right pb-2 font-medium">Listings</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {CONDITION_ORDER.map((cond) => {
                  // NM uses the real near_mint price; others use market * discount
                  const condPrice = cond === 'NM'
                    ? (nmPrice ?? marketPrice ?? 0)
                    : (marketPrice ?? 0) * CONDITION_DISCOUNT[cond]
                  const pct = Math.round((CONDITION_DISCOUNT[cond] - 1) * 100)
                  const condListings = listings?.filter((l) => l.condition === cond) ?? []
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
                      <td className="py-3 text-right text-xs">
                        {condListings.length > 0 ? (
                          <button
                            onClick={() => document.getElementById('listings-section')?.scrollIntoView({ behavior: 'smooth' })}
                            className="text-accent hover:underline"
                          >
                            {condListings.length} for sale
                          </button>
                        ) : (
                          <span className="text-muted">—</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
                {/* PSA avg graded row — average across PSA 7-9 */}
                {gradedPrice && (
                  <tr className="hover:bg-white/3 transition-colors border-t-2 border-white/10">
                    <td className="py-3">
                      <span className="font-semibold text-blue-400">PSA</span>
                      <span className="ml-2 text-xs text-muted hidden sm:inline">Graded (avg PSA 7–9)</span>
                    </td>
                    <td className="py-3 text-right font-bold text-white">${gradedPrice.toFixed(2)}</td>
                    <td className="py-3 text-right text-xs text-muted">graded</td>
                    <td className="py-3 text-right text-xs text-muted">—</td>
                  </tr>
                )}
                {/* PSA 10 / Gem MT row — real PSA 10 value */}
                {psa10Price && (
                  <tr className="hover:bg-white/3 transition-colors">
                    <td className="py-3">
                      <span className="font-semibold" style={{ color: '#D4AF37' }}>PSA 10</span>
                      <span className="ml-2 text-xs text-muted hidden sm:inline">Gem Mint</span>
                    </td>
                    <td className="py-3 text-right font-bold" style={{ color: '#D4AF37' }}>${psa10Price.toFixed(2)}</td>
                    <td className="py-3 text-right text-xs text-muted">gem mt</td>
                    <td className="py-3 text-right text-xs text-muted">—</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Price history chart */}
      <div className="bg-surface rounded-2xl border border-white/5 p-5">
        <h2 className="text-sm font-semibold text-white mb-4">
          Price History
          <span className="ml-2 text-muted font-normal">({prices?.history_days ?? 90} days)</span>
        </h2>
        <PriceHistoryChart data={prices?.history ?? []} />
      </div>

      {/* Marketplace listings for this card */}
      <div id="listings-section" className="bg-surface rounded-2xl border border-white/5 p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-white">
            Marketplace Listings
            {listings && listings.length > 0 && (
              <span className="ml-2 text-muted font-normal">({listings.length})</span>
            )}
          </h2>
          <button
            onClick={() => navigate(`/sell/new?card_id=${id}`)}
            className="text-xs text-accent hover:underline"
          >
            + Sell this card
          </button>
        </div>

        {!listings || listings.length === 0 ? (
          <div className="text-center py-8 text-muted">
            <ShoppingCart size={24} className="mx-auto mb-2 opacity-40" />
            <p className="text-sm">No listings yet</p>
            <button
              onClick={() => navigate(`/sell/new?card_id=${id}`)}
              className="mt-3 px-4 py-2 bg-accent hover:bg-accent-hover text-white text-xs font-medium rounded-lg transition-colors"
            >
              Be the first to sell
            </button>
          </div>
        ) : (
          <div className="space-y-1">
            <div className="grid grid-cols-12 gap-2 px-3 text-xs text-muted pb-2 border-b border-white/10">
              <div className="col-span-2">Condition</div>
              <div className="col-span-3">Grade</div>
              <div className="col-span-2">Seller</div>
              <div className="col-span-1 text-center">Qty</div>
              <div className="col-span-2 text-right">Price</div>
              <div className="col-span-2"></div>
            </div>
            {listings
              .slice()
              .sort((a, b) => a.price - b.price)
              .map((listing) => (
                <div key={listing.id}
                  className="grid grid-cols-12 gap-2 px-3 py-2.5 rounded-lg hover:bg-white/5 transition-colors items-center">
                  <div className="col-span-2">
                    <span className={`text-xs font-semibold ${CONDITION_COLOR[listing.condition] ?? 'text-white'}`}>
                      {listing.condition}
                    </span>
                  </div>
                  <div className="col-span-3">
                    {listing.grade ? (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 bg-blue-600 text-white text-xs font-bold rounded">
                        {listing.grading_company ?? 'PSA'} {listing.grade}
                      </span>
                    ) : (
                      <span className="text-xs text-muted">Raw</span>
                    )}
                  </div>
                  <div className="col-span-2 text-xs text-muted truncate">
                    {listing.seller_email?.split('@')[0] ?? 'Seller'}
                  </div>
                  <div className="col-span-1 text-center text-xs text-muted">×{listing.quantity}</div>
                  <div className="col-span-2 text-right text-sm font-bold text-white">
                    ${listing.price.toFixed(2)}
                  </div>
                  <div className="col-span-2 text-right">
                    <button
                      onClick={() => navigate(`/marketplace/${listing.id}`)}
                      className="text-xs px-3 py-1.5 bg-accent hover:bg-accent-hover text-white rounded-lg transition-colors font-medium"
                    >
                      Buy
                    </button>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    </div>
  )
}
