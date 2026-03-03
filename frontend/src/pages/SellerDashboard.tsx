import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getMySellerProfile, onboardSeller, getStripeDashboardLink } from '../api/sellers'
import { getMyListings, updateListing } from '../api/listings'
import { getSellingOrders, markShipped, shippingLabelQuote, createShippingLabel } from '../api/orders'
import type { Order } from '../api/orders'

interface ShippingDims {
  length_in: number; width_in: number; height_in: number; weight_oz: number
}
const DEFAULT_DIMS: ShippingDims = { length_in: 0, width_in: 0, height_in: 0, weight_oz: 0 }

const STATUS_COLOR: Record<string, string> = {
  pending: 'text-yellow-400',
  paid: 'text-blue-400',
  shipped: 'text-purple-400',
  completed: 'text-yes',
  cancelled: 'text-red-400',
}

export default function SellerDashboard() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [tab, setTab] = useState<'listings' | 'orders'>('listings')
  const [trackingInputs, setTrackingInputs] = useState<Record<number, string>>({})
  const [labelModal, setLabelModal] = useState<number | null>(null) // order_id
  const [labelDims, setLabelDims] = useState<ShippingDims>(DEFAULT_DIMS)
  const [labelQuote, setLabelQuote] = useState<number | null>(null)
  const [labelCreated, setLabelCreated] = useState<Record<number, string>>({})
  const [labelLoading, setLabelLoading] = useState(false)

  const { data: profile, refetch: refetchProfile } = useQuery({
    queryKey: ['seller-profile'],
    queryFn: getMySellerProfile,
  })
  const { data: listings, isLoading: listingsLoading } = useQuery({
    queryKey: ['my-listings'],
    queryFn: () => getMyListings(),
    enabled: !!profile?.onboarding_complete,
  })
  const { data: orders, isLoading: ordersLoading } = useQuery({
    queryKey: ['selling-orders'],
    queryFn: getSellingOrders,
    enabled: !!profile?.onboarding_complete,
  })

  async function handleOnboard() {
    const result = await onboardSeller()
    if (result.onboarding_url) {
      window.location.href = result.onboarding_url
    } else if (result.test_mode) {
      await refetchProfile()
    }
  }

  async function handleCancelListing(id: number) {
    await updateListing(id, { status: 'cancelled' })
    qc.invalidateQueries({ queryKey: ['my-listings'] })
  }

  async function handleShip(orderId: number) {
    const tracking = trackingInputs[orderId] ?? ''
    await markShipped(orderId, tracking)
    qc.invalidateQueries({ queryKey: ['selling-orders'] })
  }

  async function handleLabelQuote() {
    if (!labelModal) return
    setLabelLoading(true)
    try {
      const q = await shippingLabelQuote(labelModal, labelDims)
      setLabelQuote(q.label_fee)
    } finally {
      setLabelLoading(false)
    }
  }

  async function handleCreateLabel() {
    if (!labelModal) return
    setLabelLoading(true)
    try {
      const result = await createShippingLabel(labelModal, labelDims)
      setLabelCreated(prev => ({ ...prev, [labelModal]: result.message }))
      setLabelModal(null)
      setLabelQuote(null)
      setLabelDims(DEFAULT_DIMS)
    } finally {
      setLabelLoading(false)
    }
  }

  if (!profile?.onboarding_complete) {
    return (
      <div className="max-w-lg mx-auto text-center py-16">
        <div className="text-5xl mb-4">🏪</div>
        <h1 className="text-2xl font-black text-white mb-2">Seller Hub</h1>
        <p className="text-muted text-sm mb-4">Connect your bank account via Stripe to start selling and receiving payouts directly to your bank.</p>
        <div className="bg-accent/10 border border-accent/30 rounded-xl p-4 mb-6 text-sm text-left">
          <p className="text-white font-semibold mb-1">What happens when you connect?</p>
          <ul className="text-muted space-y-1 text-xs">
            <li>• Stripe securely links your bank account</li>
            <li>• You receive payouts within 2–7 days of each sale</li>
            <li>• TCGMarket collects 6% platform fee from buyers</li>
          </ul>
        </div>
        <button
          onClick={handleOnboard}
          className="px-8 py-3 bg-accent hover:bg-accent-hover text-white font-bold rounded-xl transition-colors w-full"
        >
          Connect Bank Account via Stripe
        </button>
        <p className="text-xs text-muted mt-3">Powered by Stripe Connect. Your banking info is never stored by TCGMarket.</p>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Seller Hub</h1>
        <div className="flex gap-3">
          <button
            onClick={async () => {
              try {
                const { url } = await getStripeDashboardLink()
                window.open(url, '_blank')
              } catch {
                alert('Stripe dashboard link unavailable (Stripe not configured)')
              }
            }}
            className="px-3 py-2 border border-white/20 hover:border-white/40 text-sm text-white rounded-lg transition-colors"
          >
            Stripe Dashboard ↗
          </button>
          <button
            onClick={() => navigate('/sell/new')}
            className="px-4 py-2 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-lg transition-colors"
          >
            + New Listing
          </button>
        </div>
      </div>

      {/* Stats */}
      {profile && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-surface border border-white/5 rounded-xl p-4 text-center">
            <p className="text-2xl font-black text-white">{profile.active_listings}</p>
            <p className="text-xs text-muted mt-1">Active Listings</p>
          </div>
          <div className="bg-surface border border-white/5 rounded-xl p-4 text-center">
            <p className="text-2xl font-black text-white">{profile.sold_listings}</p>
            <p className="text-xs text-muted mt-1">Sold</p>
          </div>
          <div className="bg-surface border border-white/5 rounded-xl p-4 text-center">
            <p className="text-2xl font-black text-yes">${profile.total_earnings.toFixed(2)}</p>
            <p className="text-xs text-muted mt-1">Total Earnings</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-5 border-b border-white/5">
        {(['listings', 'orders'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors capitalize ${tab === t ? 'text-white border-b-2 border-accent' : 'text-muted hover:text-white'}`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Listings tab */}
      {tab === 'listings' && (
        <div>
          {listingsLoading ? (
            <div className="space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-surface rounded-xl animate-pulse" />)}</div>
          ) : listings?.length ? (
            <div className="space-y-3">
              {listings.map((l) => (
                <div key={l.id} className="bg-surface border border-white/5 rounded-xl p-4 flex items-center gap-4">
                  {(l.card?.image_small ?? l.product?.image_url) && (
                    <img
                      src={l.card?.image_small ?? l.product?.image_url ?? ''}
                      alt={l.title}
                      className="w-10 h-14 object-contain rounded"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-white text-sm truncate">{l.title}</p>
                    <p className="text-xs text-muted">{l.condition} · {l.quantity} available</p>
                  </div>
                  <span className={`text-sm font-black ${l.status === 'active' ? 'text-white' : 'text-muted'}`}>
                    ${l.price.toFixed(2)}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full ${l.status === 'active' ? 'bg-yes/10 text-yes' : 'bg-white/5 text-muted'}`}>
                    {l.status}
                  </span>
                  {l.status === 'active' && (
                    <button
                      onClick={() => handleCancelListing(l.id)}
                      className="text-xs text-muted hover:text-red-400 transition-colors"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 text-muted">
              <p className="text-4xl mb-3">📦</p>
              <p>No listings yet.</p>
              <button onClick={() => navigate('/sell/new')} className="mt-4 px-5 py-2 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-lg transition-colors">
                Create your first listing
              </button>
            </div>
          )}
        </div>
      )}

      {/* Shipping label modal */}
      {labelModal !== null && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-surface border border-white/10 rounded-2xl p-6 w-full max-w-sm">
            <h3 className="text-white font-black text-lg mb-4">Generate Shipping Label</h3>
            <p className="text-xs text-muted mb-4">Order #{labelModal} — Enter package dimensions to get a shipping quote.</p>
            <div className="space-y-3 mb-4">
              {[
                { key: 'length_in', label: 'Length (in)' },
                { key: 'width_in', label: 'Width (in)' },
                { key: 'height_in', label: 'Height (in)' },
                { key: 'weight_oz', label: 'Weight (oz)' },
              ].map(({ key, label }) => (
                <div key={key} className="flex items-center gap-3">
                  <label className="text-sm text-muted w-28 flex-shrink-0">{label}</label>
                  <input
                    type="number"
                    min={0}
                    step={0.1}
                    value={(labelDims as any)[key] || ''}
                    onChange={(e) => setLabelDims(d => ({ ...d, [key]: parseFloat(e.target.value) || 0 }))}
                    className="flex-1 px-3 py-2 bg-surface-2 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-accent"
                  />
                </div>
              ))}
            </div>
            {labelQuote !== null && (
              <div className="bg-surface-2 rounded-xl p-3 mb-4 flex justify-between items-center">
                <span className="text-sm text-muted">USPS Estimated Fee</span>
                <span className="text-gold font-black text-lg">${labelQuote.toFixed(2)}</span>
              </div>
            )}
            <div className="flex gap-2">
              <button onClick={() => setLabelModal(null)} className="flex-1 py-2 border border-white/20 rounded-lg text-sm text-muted hover:text-white transition-colors">
                Cancel
              </button>
              {labelQuote === null ? (
                <button onClick={handleLabelQuote} disabled={labelLoading} className="flex-1 py-2 bg-surface-2 border border-white/20 hover:border-accent text-white text-sm rounded-lg transition-colors disabled:opacity-50">
                  {labelLoading ? 'Getting quote…' : 'Get Quote'}
                </button>
              ) : (
                <button onClick={handleCreateLabel} disabled={labelLoading} className="flex-1 py-2 bg-accent hover:bg-accent-hover text-white font-bold text-sm rounded-lg transition-colors disabled:opacity-50">
                  {labelLoading ? 'Creating…' : `Generate — $${labelQuote.toFixed(2)}`}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Orders tab */}
      {tab === 'orders' && (
        <div>
          {ordersLoading ? (
            <div className="space-y-3">{[...Array(3)].map((_, i) => <div key={i} className="h-20 bg-surface rounded-xl animate-pulse" />)}</div>
          ) : orders?.length ? (
            <div className="space-y-3">
              {orders.map((o) => (
                <div key={o.id} className="bg-surface border border-white/5 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-white text-sm">Order #{o.id}</span>
                    <span className={`text-xs font-medium ${STATUS_COLOR[o.status] ?? 'text-muted'}`}>{o.status.toUpperCase()}</span>
                  </div>
                  <div className="text-xs text-muted mb-1">
                    {o.quantity}× @ ${o.price_each.toFixed(2)} · You receive: <span className="text-yes">${o.payout_amount.toFixed(2)}</span>
                  </div>
                  {o.shipping_address && (
                    <div className="text-xs text-muted">
                      Ship to: {o.shipping_address.name}, {o.shipping_address.city}, {o.shipping_address.state} {o.shipping_address.postal_code}
                    </div>
                  )}
                  {o.status === 'paid' && (
                    <div className="space-y-2 mt-3">
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          placeholder="Tracking number"
                          value={trackingInputs[o.id] ?? ''}
                          onChange={(e) => setTrackingInputs(t => ({ ...t, [o.id]: e.target.value }))}
                          className="flex-1 px-2 py-1.5 bg-surface-2 border border-white/10 rounded-lg text-xs text-white placeholder-muted focus:outline-none focus:border-accent"
                        />
                        <button
                          onClick={() => handleShip(o.id)}
                          className="px-3 py-1.5 bg-accent hover:bg-accent-hover text-white text-xs font-medium rounded-lg transition-colors"
                        >
                          Mark Shipped
                        </button>
                      </div>
                      {labelCreated[o.id] ? (
                        <p className="text-xs text-gold">{labelCreated[o.id]}</p>
                      ) : (
                        <button
                          onClick={() => { setLabelModal(o.id); setLabelQuote(null); setLabelDims(DEFAULT_DIMS) }}
                          className="text-xs text-accent hover:text-accent-hover transition-colors underline"
                        >
                          Generate Shipping Label
                        </button>
                      )}
                    </div>
                  )}
                  {o.tracking_number && (
                    <p className="text-xs text-muted mt-2">Tracking: <span className="text-white">{o.tracking_number}</span></p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 text-muted">
              <p className="text-4xl mb-3">📋</p>
              <p>No orders yet.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
