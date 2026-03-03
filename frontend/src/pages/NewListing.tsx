import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { getMySellerProfile, onboardSeller } from '../api/sellers'
import { createListing } from '../api/listings'
import client from '../api/client'

const CONDITIONS = ['NM', 'LP', 'MP', 'HP', 'DMG'] as const
const CONDITION_LABEL: Record<string, string> = {
  NM: 'Near Mint — No visible wear',
  LP: 'Lightly Played — Minor scratches',
  MP: 'Moderately Played — Visible wear',
  HP: 'Heavily Played — Major wear',
  DMG: 'Damaged — Creases, tears',
}

interface CardResult {
  id: string
  name: string
  set_name: string
  rarity?: string
  image_small?: string
}

export default function NewListing() {
  const navigate = useNavigate()

  const { data: sellerProfile, isLoading: profileLoading, refetch } = useQuery({
    queryKey: ['seller-profile'],
    queryFn: getMySellerProfile,
  })

  const [onboarding, setOnboarding] = useState(false)
  const [cardSearch, setCardSearch] = useState('')
  const [cardResults, setCardResults] = useState<CardResult[]>([])
  const [selectedCard, setSelectedCard] = useState<CardResult | null>(null)
  const [condition, setCondition] = useState<string>('NM')
  const [price, setPrice] = useState('')
  const [quantity, setQuantity] = useState('1')
  const [description, setDescription] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  // Search cards
  useEffect(() => {
    if (cardSearch.length < 2) { setCardResults([]); return }
    const timeout = setTimeout(async () => {
      try {
        const { data } = await client.get(`/cards/search?q=${encodeURIComponent(cardSearch)}&limit=8`)
        setCardResults(data.results ?? data ?? [])
      } catch { setCardResults([]) }
    }, 300)
    return () => clearTimeout(timeout)
  }, [cardSearch])

  async function handleOnboard() {
    setOnboarding(true)
    try {
      const result = await onboardSeller()
      if (result.onboarding_url) {
        window.location.href = result.onboarding_url
      } else if (result.test_mode) {
        await refetch()
      }
    } finally {
      setOnboarding(false)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedCard) { setError('Please select a card'); return }
    if (!price || Number(price) <= 0) { setError('Enter a valid price'); return }
    setError('')
    setSubmitting(true)
    try {
      await createListing({
        item_type: 'card',
        card_id: selectedCard.id,
        condition,
        quantity: Number(quantity),
        price: Number(price),
        description: description || undefined,
        image_url: imageUrl.trim() || undefined,
      })
      navigate('/marketplace')
    } catch (e: any) {
      setError(e?.response?.data?.detail?.message ?? e?.response?.data?.detail ?? 'Failed to create listing')
    } finally {
      setSubmitting(false)
    }
  }

  const priceNum = Number(price)

  if (profileLoading) return <div className="text-muted text-center py-20">Loading…</div>

  // Not a seller yet — show onboarding prompt
  if (!sellerProfile?.onboarding_complete) {
    return (
      <div className="max-w-lg mx-auto text-center py-16">
        <div className="text-5xl mb-4">🏪</div>
        <h1 className="text-2xl font-black text-white mb-2">Become a Seller</h1>
        <p className="text-muted text-sm mb-6 leading-relaxed">
          To list cards for sale, you need to connect a Stripe account so buyers can pay you directly.
        </p>
        <div className="bg-surface border border-white/10 rounded-xl p-5 text-left mb-6 space-y-2">
          <div className="flex items-center gap-3 text-sm text-gray-300">
            <span className="text-yes">✓</span> Instant payouts to your bank via Stripe
          </div>
          <div className="flex items-center gap-3 text-sm text-gray-300">
            <span className="text-yes">✓</span> Fast, secure payments for buyers
          </div>
          <div className="flex items-center gap-3 text-sm text-gray-300">
            <span className="text-yes">✓</span> Free to list — no upfront costs
          </div>
        </div>
        <button
          onClick={handleOnboard}
          disabled={onboarding}
          className="w-full py-3 bg-accent hover:bg-accent-hover text-white font-bold rounded-xl transition-colors disabled:opacity-50"
        >
          {onboarding ? 'Setting up…' : 'Connect Stripe & Start Selling'}
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-lg mx-auto">
      <button onClick={() => navigate(-1)} className="text-sm text-muted hover:text-white mb-6 flex items-center gap-1">
        ← Back
      </button>
      <h1 className="text-2xl font-black text-white mb-6">Create a Listing</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Card search */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Card *</label>
          {selectedCard ? (
            <div className="flex items-center gap-3 p-3 bg-surface border border-accent/30 rounded-xl">
              {selectedCard.image_small && (
                <img src={selectedCard.image_small} alt={selectedCard.name} className="w-10 h-14 object-contain" />
              )}
              <div className="flex-1 min-w-0">
                <p className="font-bold text-white text-sm truncate">{selectedCard.name}</p>
                <p className="text-muted text-xs">{selectedCard.set_name}</p>
              </div>
              <button type="button" onClick={() => { setSelectedCard(null); setCardSearch('') }} className="text-muted hover:text-white text-xs">Change</button>
            </div>
          ) : (
            <div className="relative">
              <input
                type="text"
                placeholder="Search by card name…"
                value={cardSearch}
                onChange={(e) => setCardSearch(e.target.value)}
                className="w-full px-3 py-2.5 bg-surface border border-white/10 rounded-xl text-sm text-white placeholder-muted focus:outline-none focus:border-accent"
              />
              {cardResults.length > 0 && (
                <div className="absolute top-full mt-1 w-full bg-surface border border-white/10 rounded-xl shadow-xl z-10 max-h-60 overflow-y-auto">
                  {cardResults.map((card) => (
                    <button
                      key={card.id}
                      type="button"
                      onClick={() => { setSelectedCard(card); setCardSearch(''); setCardResults([]) }}
                      className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/5 transition-colors text-left"
                    >
                      {card.image_small && <img src={card.image_small} alt={card.name} className="w-8 h-11 object-contain" />}
                      <div>
                        <p className="text-sm font-medium text-white">{card.name}</p>
                        <p className="text-xs text-muted">{card.set_name} · {card.rarity}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Condition */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Condition *</label>
          <div className="grid grid-cols-5 gap-2">
            {CONDITIONS.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setCondition(c)}
                title={CONDITION_LABEL[c]}
                className={`py-2 rounded-lg text-xs font-bold transition-colors ${condition === c ? 'bg-accent text-white' : 'bg-surface border border-white/10 text-muted hover:text-white'}`}
              >
                {c}
              </button>
            ))}
          </div>
          <p className="text-xs text-muted mt-1">{CONDITION_LABEL[condition]}</p>
        </div>

        {/* Price + Qty */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Price (USD) *</label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted text-sm">$</span>
              <input
                type="number"
                min="0.01"
                step="0.01"
                placeholder="0.00"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="w-full pl-7 pr-3 py-2.5 bg-surface border border-white/10 rounded-xl text-sm text-white focus:outline-none focus:border-accent"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Quantity</label>
            <input
              type="number"
              min="1"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              className="w-full px-3 py-2.5 bg-surface border border-white/10 rounded-xl text-sm text-white focus:outline-none focus:border-accent"
            />
          </div>
        </div>

        {/* Product photo URL */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Product Photo URL (optional)</label>
          <input
            type="url"
            placeholder="https://i.imgur.com/your-photo.jpg"
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            className="w-full px-3 py-2.5 bg-surface border border-white/10 rounded-xl text-sm text-white placeholder-muted focus:outline-none focus:border-accent"
          />
          {imageUrl.trim() && (
            <img src={imageUrl.trim()} alt="Preview" className="mt-2 h-24 object-contain rounded-lg border border-white/10" onError={(e) => (e.currentTarget.style.display = 'none')} />
          )}
          <p className="text-xs text-muted mt-1">Upload your photo to Imgur, Google Photos, or similar and paste the direct link here.</p>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Description (optional)</label>
          <textarea
            rows={3}
            placeholder="Describe the card's condition, any notable details…"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2.5 bg-surface border border-white/10 rounded-xl text-sm text-white placeholder-muted focus:outline-none focus:border-accent resize-none"
          />
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <button
          type="submit"
          disabled={submitting || !selectedCard}
          className="w-full py-3 bg-accent hover:bg-accent-hover text-white font-bold rounded-xl transition-colors disabled:opacity-50"
        >
          {submitting ? 'Creating…' : 'Create Listing'}
        </button>
      </form>
    </div>
  )
}
