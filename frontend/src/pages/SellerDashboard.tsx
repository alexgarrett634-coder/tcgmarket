import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getMySellerProfile, onboardSeller, getStripeDashboardLink } from '../api/sellers'
import { getMyListings, updateListing } from '../api/listings'
import { getSellingOrders, markShipped } from '../api/orders'
import type { Order } from '../api/orders'

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

  if (!profile?.onboarding_complete) {
    return (
      <div className="max-w-lg mx-auto text-center py-16">
        <div className="text-5xl mb-4">🏪</div>
        <h1 className="text-2xl font-black text-white mb-2">Seller Hub</h1>
        <p className="text-muted text-sm mb-8">Connect your Stripe account to start selling and receiving payouts.</p>
        <button
          onClick={handleOnboard}
          className="px-8 py-3 bg-accent hover:bg-accent-hover text-white font-bold rounded-xl transition-colors"
        >
          Connect Stripe & Start Selling
        </button>
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
                    <div className="flex items-center gap-2 mt-3">
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
