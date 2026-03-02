import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getOrders, markComplete } from '../api/orders'

const STATUS_COLOR: Record<string, string> = {
  pending: 'text-yellow-400 bg-yellow-400/10',
  paid: 'text-blue-400 bg-blue-400/10',
  shipped: 'text-purple-400 bg-purple-400/10',
  completed: 'text-yes bg-yes/10',
  cancelled: 'text-red-400 bg-red-400/10',
}

const STATUS_STEP: Record<string, number> = {
  pending: 0, paid: 1, shipped: 2, completed: 3, cancelled: -1,
}

export default function Orders() {
  const qc = useQueryClient()
  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: getOrders,
    refetchInterval: 30_000,
  })

  async function handleComplete(id: number) {
    await markComplete(id)
    qc.invalidateQueries({ queryKey: ['orders'] })
  }

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-white mb-6">My Orders</h1>
        <div className="space-y-3">{[...Array(4)].map((_, i) => <div key={i} className="h-24 bg-surface rounded-xl animate-pulse" />)}</div>
      </div>
    )
  }

  if (!orders?.length) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-white mb-6">My Orders</h1>
        <div className="text-center py-24 text-muted">
          <p className="text-5xl mb-4">📋</p>
          <p className="text-lg font-medium text-white mb-2">No orders yet</p>
          <p className="text-sm">When you buy a listing, your orders will appear here.</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">My Orders</h1>
      <div className="space-y-4">
        {orders.map((o) => {
          const step = STATUS_STEP[o.status] ?? 0
          return (
            <div key={o.id} className="bg-surface border border-white/5 rounded-xl p-5">
              {/* Order header */}
              <div className="flex items-center justify-between mb-3">
                <div>
                  <span className="font-bold text-white text-sm">Order #{o.id}</span>
                  <span className="text-muted text-xs ml-3">{new Date(o.created_at).toLocaleDateString()}</span>
                </div>
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${STATUS_COLOR[o.status] ?? 'text-muted bg-white/5'}`}>
                  {o.status.toUpperCase()}
                </span>
              </div>

              {/* Progress bar */}
              {o.status !== 'cancelled' && (
                <div className="flex items-center gap-1 mb-3">
                  {['Paid', 'Shipped', 'Delivered'].map((label, i) => (
                    <div key={label} className="flex items-center gap-1 flex-1">
                      <div className={`h-1.5 flex-1 rounded-full transition-colors ${i < step ? 'bg-accent' : 'bg-white/10'}`} />
                      {i === 2 && <span className={`text-xs ${step >= 3 ? 'text-yes' : 'text-muted'}`}>{label}</span>}
                    </div>
                  ))}
                </div>
              )}

              {/* Amount */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted">{o.quantity}× @ ${o.price_each.toFixed(2)}</span>
                <span className="font-bold text-white">${o.subtotal.toFixed(2)}</span>
              </div>

              {/* Tracking */}
              {o.tracking_number && (
                <div className="mt-3 px-3 py-2 bg-surface-2 rounded-lg text-xs text-gray-300">
                  Tracking: <span className="font-mono text-white">{o.tracking_number}</span>
                </div>
              )}

              {/* Mark complete */}
              {(o.status === 'shipped' || o.status === 'paid') && (
                <button
                  onClick={() => handleComplete(o.id)}
                  className="mt-3 w-full py-2 border border-yes/30 hover:bg-yes/10 text-yes text-sm font-medium rounded-lg transition-colors"
                >
                  Mark as Received
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
