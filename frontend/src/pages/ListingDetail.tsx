import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getListing } from '../api/listings'
import { createOrder } from '../api/orders'
import { useAuth } from '../context/AuthContext'
import PsaSlabFrame from '../components/shared/PsaSlabFrame'

const CONDITION_LABEL: Record<string, string> = {
  'GEM MT': 'Gem Mint (PSA 10)',
  NM: 'Near Mint',
  LP: 'Lightly Played',
  MP: 'Moderately Played',
  HP: 'Heavily Played',
  DMG: 'Damaged',
}

const CONDITION_COLOR: Record<string, string> = {
  'GEM MT': 'text-yellow-300 bg-yellow-400/15',
  NM: 'text-yes bg-yes/10',
  LP: 'text-green-400 bg-green-400/10',
  MP: 'text-yellow-400 bg-yellow-400/10',
  HP: 'text-orange-400 bg-orange-400/10',
  DMG: 'text-red-400 bg-red-400/10',
}

export default function ListingDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { isLoggedIn } = useAuth()

  const [qty, setQty] = useState(1)
  const [buying, setBuying] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [addr, setAddr] = useState({ name: '', line1: '', city: '', state: '', postal_code: '', country: 'US' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const { data: listing, isLoading } = useQuery({
    queryKey: ['listing', id],
    queryFn: () => getListing(Number(id)),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="aspect-[3/4] bg-surface rounded-2xl animate-pulse" />
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => <div key={i} className="h-8 bg-surface rounded-lg animate-pulse" />)}
        </div>
      </div>
    )
  }

  if (!listing) return <div className="text-center py-20 text-muted">Listing not found</div>

  const image = listing.card?.image_large ?? listing.card?.image_small ?? listing.product?.image_url
  const name = listing.card?.name ?? listing.product?.name ?? listing.title
  const total = listing.price * qty

  async function handleBuy() {
    setShowForm(true)
  }

  async function handleSubmitOrder() {
    setError('')
    setBuying(true)
    try {
      const result = await createOrder({
        listing_id: listing!.id,
        quantity: qty,
        shipping_address: addr,
      })
      if (result.test_mode) {
        setSuccess(`Order #${result.order_id} created (test mode — no payment charged). ${result.message}`)
      } else {
        setSuccess(`Order #${result.order_id} created! Redirecting to payment…`)
        // In production: use Stripe.js to confirm the payment intent
        // stripe.confirmPayment({ clientSecret: result.client_secret, ... })
      }
      setShowForm(false)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setBuying(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <button onClick={() => navigate(-1)} className="text-sm text-muted hover:text-white mb-6 flex items-center gap-1">
        ← Back
      </button>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Image */}
        <div className="bg-surface-2 rounded-2xl flex items-center justify-center overflow-hidden p-2">
          {listing.grade ? (
            <PsaSlabFrame image={image} alt={name} grade={listing.grade} size="lg" className="w-full max-w-xs mx-auto" />
          ) : image ? (
            <img src={image} alt={name} className="w-full h-full object-contain aspect-[3/4]" />
          ) : (
            <svg viewBox="0 0 60 84" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-28 h-40 opacity-40">
              <rect width="60" height="84" rx="4" fill="#2a2a38"/>
              <rect x="6" y="6" width="48" height="48" rx="2" fill="#333344"/>
              <rect x="6" y="62" width="32" height="5" rx="2" fill="#3a3a4e"/>
              <rect x="6" y="71" width="20" height="4" rx="2" fill="#333344"/>
            </svg>
          )}
        </div>

        {/* Details */}
        <div className="flex flex-col gap-4">
          <div>
            <h1 className="text-2xl font-black text-white">{name}</h1>
            {(listing.card?.set_name ?? listing.product?.set_name) && (
              <p className="text-muted text-sm mt-1">{listing.card?.set_name ?? listing.product?.set_name}</p>
            )}
            {listing.card?.rarity && (
              <p className="text-muted text-xs">{listing.card.rarity}</p>
            )}
          </div>

          {/* Condition */}
          <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium w-fit ${CONDITION_COLOR[listing.condition] ?? 'text-muted bg-white/5'}`}>
            {listing.condition} — {CONDITION_LABEL[listing.condition] ?? listing.condition}
          </div>

          {/* Price */}
          <div className="bg-surface border border-white/5 rounded-xl p-4">
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-3xl font-black text-white">${listing.price.toFixed(2)}</span>
              <span className="text-muted text-sm">per card</span>
            </div>
            <p className="text-xs text-muted">Sold by {listing.seller_email ?? 'anonymous seller'}</p>
            <p className="text-xs text-muted mt-0.5">{listing.quantity} available</p>
          </div>

          {/* Description */}
          {listing.description && (
            <div className="bg-surface border border-white/5 rounded-xl p-4">
              <p className="text-sm text-gray-300">{listing.description}</p>
            </div>
          )}

          {/* Buy section */}
          {listing.status === 'active' && !success && !showForm && (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <label className="text-sm text-muted">Qty:</label>
                <input
                  type="number"
                  min={1}
                  max={listing.quantity}
                  value={qty}
                  onChange={(e) => setQty(Math.min(listing.quantity, Math.max(1, Number(e.target.value))))}
                  className="w-16 px-2 py-1.5 bg-surface border border-white/10 rounded-lg text-sm text-white text-center focus:outline-none focus:border-accent"
                />
              </div>
              <button
                onClick={handleBuy}
                className="flex-1 py-3 bg-accent hover:bg-accent-hover text-white font-bold rounded-xl transition-colors"
              >
                Buy Now — ${total.toFixed(2)}
              </button>
            </div>
          )}

          {listing.status !== 'active' && !success && (
            <div className="px-4 py-3 bg-white/5 rounded-xl text-sm text-muted text-center">
              This listing is {listing.status}
            </div>
          )}

          {/* Shipping form */}
          {showForm && !success && !isLoggedIn && (
            <div className="bg-surface border border-accent/20 rounded-xl p-4 space-y-3 text-center">
              <p className="text-white font-semibold text-sm">Sign in to complete your purchase</p>
              <p className="text-muted text-xs">Create a free account to buy cards and track your orders.</p>
              <div className="flex gap-2 justify-center">
                <button onClick={() => navigate('/login')} className="px-4 py-2 border border-white/20 rounded-lg text-sm text-white hover:border-white/40 transition-colors">Sign In</button>
                <button onClick={() => navigate('/register')} className="px-4 py-2 bg-accent hover:bg-accent-hover text-white text-sm font-semibold rounded-lg transition-colors">Create Account</button>
              </div>
              <button onClick={() => setShowForm(false)} className="text-xs text-muted hover:text-white transition-colors">Cancel</button>
            </div>
          )}
          {showForm && !success && isLoggedIn && (
            <div className="bg-surface border border-white/10 rounded-xl p-4 space-y-3">
              <h3 className="font-bold text-white text-sm">Shipping Address</h3>
              {(['name', 'line1', 'city', 'state', 'postal_code'] as const).map((field) => (
                <input
                  key={field}
                  placeholder={field.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  value={addr[field]}
                  onChange={(e) => setAddr(a => ({ ...a, [field]: e.target.value }))}
                  className="w-full px-3 py-2 bg-surface-2 border border-white/10 rounded-lg text-sm text-white placeholder-muted focus:outline-none focus:border-accent"
                />
              ))}
              {error && <p className="text-red-400 text-xs">{error}</p>}
              <div className="flex gap-2">
                <button
                  onClick={() => setShowForm(false)}
                  className="flex-1 py-2 border border-white/20 rounded-lg text-sm text-muted hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmitOrder}
                  disabled={buying}
                  className="flex-1 py-2 bg-accent hover:bg-accent-hover text-white font-bold rounded-lg text-sm transition-colors disabled:opacity-50"
                >
                  {buying ? 'Processing…' : `Confirm — $${total.toFixed(2)}`}
                </button>
              </div>
            </div>
          )}

          {/* Success */}
          {success && (
            <div className="px-4 py-3 bg-yes/10 border border-yes/20 rounded-xl text-sm text-yes">
              {success}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
