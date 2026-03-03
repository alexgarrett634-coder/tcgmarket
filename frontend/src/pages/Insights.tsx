import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import client from '../api/client'

interface PredictionResult {
  card_id: string
  card_name: string
  set_name: string
  current_ebay_median: number
  predicted_2mo_value: number
  change_pct: number
  days_since_release: number | null
  new_release: boolean
  ebay_sample_size: number
  ebay_price_range: { min: number; max: number }
}

async function predictCard(cardId: string): Promise<PredictionResult> {
  const { data } = await client.get(`/insights/predict/${cardId}`)
  return data
}

async function searchCards(q: string): Promise<{ id: string; name: string; set_name: string; image_small: string | null }[]> {
  const { data } = await client.get('/cards', { params: { q, language: 'en', limit: 8 } })
  return data
}

export default function Insights() {
  const { isLoggedIn } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [selectedCard, setSelectedCard] = useState<{ id: string; name: string; set_name: string } | null>(null)
  const [searchOpen, setSearchOpen] = useState(false)

  const { data: searchResults } = useQuery({
    queryKey: ['insights-search', query],
    queryFn: () => searchCards(query),
    enabled: query.length >= 2,
    staleTime: 30_000,
  })

  const { data: prediction, isLoading: predLoading, error: predError } = useQuery({
    queryKey: ['insights-predict', selectedCard?.id],
    queryFn: () => predictCard(selectedCard!.id),
    enabled: !!selectedCard && isLoggedIn,
    retry: false,
  })

  const changePositive = prediction && prediction.change_pct > 0
  const changeColor = prediction
    ? prediction.change_pct > 0 ? 'text-yes' : prediction.change_pct < -10 ? 'text-no' : 'text-yellow-400'
    : ''

  return (
    <div className="max-w-2xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-black text-white mb-1">Price Predictions</h1>
        <p className="text-muted text-sm">eBay-based value forecasts · 2-month outlook · New-release decay model</p>
      </div>

      {/* Paywall banner for non-subscribers */}
      {!isLoggedIn && (
        <div className="bg-surface border border-accent/30 rounded-2xl p-6 mb-8 text-center">
          <div className="text-4xl mb-3">🔮</div>
          <h2 className="text-lg font-black text-white mb-1">Insights Subscription</h2>
          <p className="text-muted text-sm mb-4">Sign in and subscribe for <span className="text-gold font-bold">$10/month</span> to unlock eBay-based price predictions for any card.</p>
          <div className="flex gap-3 justify-center">
            <button onClick={() => navigate('/register')} className="px-5 py-2.5 bg-accent hover:bg-accent-hover text-white font-bold rounded-xl transition-colors text-sm">
              Get Started
            </button>
            <button onClick={() => navigate('/login')} className="px-5 py-2.5 border border-white/20 hover:border-white/40 text-white rounded-xl transition-colors text-sm">
              Sign In
            </button>
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative mb-6">
        <input
          type="text"
          placeholder="Search for a Pokémon card…"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setSearchOpen(true) }}
          onFocus={() => setSearchOpen(true)}
          className="w-full px-4 py-3 bg-surface border border-white/10 rounded-xl text-white placeholder-muted focus:outline-none focus:border-accent text-sm"
        />
        {searchOpen && searchResults && searchResults.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-surface border border-white/10 rounded-xl overflow-hidden z-10 shadow-xl">
            {searchResults.map((card) => (
              <button
                key={card.id}
                onClick={() => {
                  setSelectedCard(card)
                  setQuery(card.name)
                  setSearchOpen(false)
                }}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-white/5 transition-colors text-left"
              >
                {card.image_small && (
                  <img src={card.image_small} alt={card.name} className="w-8 h-11 object-contain rounded" />
                )}
                <div>
                  <p className="text-sm text-white font-medium">{card.name}</p>
                  <p className="text-xs text-muted">{card.set_name}</p>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Prediction result */}
      {selectedCard && isLoggedIn && (
        <div>
          {predLoading && (
            <div className="bg-surface border border-white/5 rounded-2xl p-8 text-center">
              <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-muted text-sm">Fetching eBay data…</p>
            </div>
          )}

          {predError && (
            <div className="bg-surface border border-white/5 rounded-2xl p-6 text-center">
              {(predError as any)?.response?.status === 403 ? (
                <>
                  <div className="text-4xl mb-3">🔒</div>
                  <h3 className="text-white font-bold mb-1">Insights Subscription Required</h3>
                  <p className="text-muted text-sm mb-4">Subscribe for $10/month to unlock price predictions.</p>
                  <button
                    onClick={() => navigate('/settings')}
                    className="px-5 py-2 bg-accent hover:bg-accent-hover text-white font-bold rounded-xl transition-colors text-sm"
                  >
                    Subscribe — $10/month
                  </button>
                </>
              ) : (
                <p className="text-muted text-sm">No eBay data available for this card. Try another card.</p>
              )}
            </div>
          )}

          {prediction && (
            <div className="space-y-4">
              {/* Card header */}
              <div className="bg-surface border border-white/5 rounded-2xl p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-black text-white">{prediction.card_name}</h2>
                    <p className="text-muted text-sm">{prediction.set_name}</p>
                    {prediction.new_release && (
                      <span className="inline-block mt-1.5 text-xs px-2 py-0.5 bg-yellow-400/15 text-yellow-300 rounded-full font-medium">
                        New Release · {prediction.days_since_release}d ago
                      </span>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-black text-gold">${prediction.predicted_2mo_value.toFixed(2)}</p>
                    <p className="text-xs text-muted">predicted in 2 months</p>
                    <p className={`text-sm font-bold mt-0.5 ${changeColor}`}>
                      {prediction.change_pct > 0 ? '+' : ''}{prediction.change_pct}%
                    </p>
                  </div>
                </div>
              </div>

              {/* Price breakdown */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-surface border border-white/5 rounded-xl p-4 text-center">
                  <p className="text-lg font-black text-white">${prediction.current_ebay_median.toFixed(2)}</p>
                  <p className="text-xs text-muted mt-0.5">eBay Median Now</p>
                </div>
                <div className="bg-surface border border-white/5 rounded-xl p-4 text-center">
                  <p className="text-lg font-black text-gold">${prediction.predicted_2mo_value.toFixed(2)}</p>
                  <p className="text-xs text-muted mt-0.5">2-Month Forecast</p>
                </div>
                <div className="bg-surface border border-white/5 rounded-xl p-4 text-center">
                  <p className={`text-lg font-black ${changeColor}`}>{prediction.change_pct > 0 ? '+' : ''}{prediction.change_pct}%</p>
                  <p className="text-xs text-muted mt-0.5">Est. Change</p>
                </div>
              </div>

              {/* eBay data */}
              <div className="bg-surface border border-white/5 rounded-xl p-4">
                <p className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">eBay Listings ({prediction.ebay_sample_size} sampled)</p>
                <div className="flex gap-4 text-sm">
                  <div><span className="text-muted">Low: </span><span className="text-white">${prediction.ebay_price_range.min.toFixed(2)}</span></div>
                  <div><span className="text-muted">High: </span><span className="text-white">${prediction.ebay_price_range.max.toFixed(2)}</span></div>
                  <div><span className="text-muted">Median: </span><span className="text-white">${prediction.current_ebay_median.toFixed(2)}</span></div>
                </div>
              </div>

              {/* Methodology note */}
              <div className="bg-surface-2 rounded-xl p-4 text-xs text-muted">
                <p className="font-semibold text-gray-400 mb-1">How predictions work</p>
                <p>Predictions are based on the median of current active eBay listings. For cards released within the past 60 days, a depreciation factor of up to 30% is applied (decaying linearly to 0% by day 60), reflecting typical post-launch price normalization.</p>
              </div>
            </div>
          )}
        </div>
      )}

      {!selectedCard && isLoggedIn && (
        <div className="text-center py-16 text-muted">
          <p className="text-5xl mb-4">🔮</p>
          <p className="font-medium text-gray-400">Search for a card above to see its price prediction</p>
          <p className="text-sm mt-1">Powered by live eBay data</p>
        </div>
      )}
    </div>
  )
}
