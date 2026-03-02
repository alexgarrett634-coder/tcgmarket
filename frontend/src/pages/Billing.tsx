import { useMutation, useQuery } from '@tanstack/react-query'
import PricingTable from '../components/billing/PricingTable'
import { createPortalSession, getSubscription } from '../api/billing'
import { getWallet, getTransactions } from '../api/wallet'
import { useAuth } from '../context/AuthContext'

export default function Billing() {
  const { tier } = useAuth()
  const { data: sub } = useQuery({ queryKey: ['subscription'], queryFn: getSubscription })
  const { data: wallet } = useQuery({ queryKey: ['wallet'], queryFn: getWallet })
  const { data: txns } = useQuery({ queryKey: ['transactions'], queryFn: () => getTransactions({ limit: 20 }) })

  const portal = useMutation({
    mutationFn: createPortalSession,
    onSuccess: (data) => { window.location.href = data.url },
  })

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold text-white">Billing & Subscription</h1>

      {/* Current plan chip */}
      <div className="flex items-center gap-4 bg-surface rounded-xl border border-white/5 p-4">
        <div>
          <div className="text-xs text-muted">Current Plan</div>
          <div className="text-lg font-bold text-white capitalize">{sub?.tier ?? 'Free'}</div>
          {sub?.current_period_end && (
            <div className="text-xs text-muted">Renews {new Date(sub.current_period_end).toLocaleDateString()}</div>
          )}
        </div>
        {tier !== 'free' && (
          <button
            onClick={() => portal.mutate()}
            className="ml-auto text-sm px-4 py-2 border border-white/10 text-muted hover:text-white hover:border-white/30 rounded-lg transition-colors"
          >
            Manage Subscription
          </button>
        )}
      </div>

      {/* Wallet balances */}
      {wallet && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-surface rounded-xl border border-white/5 p-4">
            <div className="text-xs text-muted mb-1">Prediction Coins</div>
            <div className="text-2xl font-bold text-yellow-400">{wallet.prediction_coins.toLocaleString()} PC</div>
            <div className="text-xs text-muted mt-1">10 PC daily bonus (Pro+)</div>
          </div>
          {tier === 'enterprise' && (
            <div className="bg-surface rounded-xl border border-white/5 p-4">
              <div className="text-xs text-muted mb-1">Market Credits</div>
              <div className="text-2xl font-bold text-green-400">${wallet.real_credits_usd.toFixed(2)}</div>
              <div className="text-xs text-muted mt-1">Real-money balance</div>
            </div>
          )}
        </div>
      )}

      {/* Pricing table */}
      <div>
        <h2 className="text-lg font-semibold text-white mb-4">Plans</h2>
        <PricingTable />
      </div>

      {/* Transaction history */}
      {txns && txns.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Transaction History</h2>
          <div className="bg-surface rounded-xl border border-white/5 overflow-hidden">
            {txns.map((t) => (
              <div key={t.id} className="flex items-center justify-between px-4 py-3 border-b border-white/5 text-sm">
                <div>
                  <p className="text-white capitalize">{t.type.replace('_', ' ')}</p>
                  <p className="text-xs text-muted">{new Date(t.created_at).toLocaleDateString()}</p>
                </div>
                <div className={`font-medium ${t.amount >= 0 ? 'text-yes' : 'text-no'}`}>
                  {t.amount >= 0 ? '+' : ''}{t.amount} {t.currency === 'coins' ? 'PC' : 'MC'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
