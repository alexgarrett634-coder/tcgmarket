import { useMutation } from '@tanstack/react-query'
import { createCheckout } from '../../api/billing'
import { useAuth } from '../../context/AuthContext'

const TIERS = [
  {
    name: 'Free',
    price: '$0',
    tier: null,
    features: [
      'Browse all prediction markets (read-only)',
      '20 card searches per day',
      'Top 5 deals teaser',
      'Current price data',
    ],
    cta: 'Current Plan',
    highlight: false,
  },
  {
    name: 'Pro',
    price: '$9.99/mo',
    tier: 'pro' as const,
    features: [
      'Everything in Free',
      'Virtual prediction markets (Prediction Coins)',
      'Unlimited card searches',
      '90-day price history',
      'Full deals feed (SSE real-time)',
      'Watchlist + email alerts (100 items)',
      'Portfolio tracking with P&L',
    ],
    cta: 'Upgrade to Pro',
    highlight: true,
  },
  {
    name: 'Enterprise',
    price: '$24.99/mo',
    tier: 'enterprise' as const,
    features: [
      'Everything in Pro',
      'Real-money prediction markets (KYC req.)',
      '365-day price history',
      'Unlimited deal alerts',
      'Personal API key',
      'CSV bulk export',
      'Analytics dashboard',
    ],
    cta: 'Upgrade to Enterprise',
    highlight: false,
  },
]

export default function PricingTable() {
  const { tier } = useAuth()
  const checkout = useMutation({
    mutationFn: (t: 'pro' | 'enterprise') => createCheckout(t).then((d) => { window.location.href = d.url }),
  })

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {TIERS.map((t) => (
        <div
          key={t.name}
          className={`rounded-xl border p-5 flex flex-col ${
            t.highlight
              ? 'border-accent bg-accent/5 shadow-red-glow'
              : 'border-white/10 bg-surface'
          }`}
        >
          {t.highlight && (
            <span className="text-xs font-bold text-accent mb-2">MOST POPULAR</span>
          )}
          <h3 className="text-lg font-bold text-white">{t.name}</h3>
          <p className="text-2xl font-bold text-white mt-1 mb-4">{t.price}</p>

          <ul className="space-y-2 flex-1 mb-6">
            {t.features.map((f) => (
              <li key={f} className="flex items-start gap-2 text-sm text-gray-300">
                <span className="text-yes mt-0.5 shrink-0">✓</span>
                {f}
              </li>
            ))}
          </ul>

          {t.tier === null ? (
            <div className="text-center text-xs text-muted py-2">
              {tier === 'free' ? '✓ Current Plan' : 'Included'}
            </div>
          ) : tier === t.tier ? (
            <div className="text-center text-xs text-yes py-2">✓ Current Plan</div>
          ) : (
            <button
              onClick={() => checkout.mutate(t.tier!)}
              disabled={checkout.isPending}
              className="w-full py-2.5 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-40"
            >
              {checkout.isPending ? 'Redirecting…' : t.cta}
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
