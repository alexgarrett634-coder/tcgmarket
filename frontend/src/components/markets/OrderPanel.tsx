import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { buyPosition } from '../../api/markets'
import { useAuth } from '../../context/AuthContext'

interface Props {
  marketId: number
  currency: 'coins' | 'usd'
  onSuccess?: (result: { shares: number; probability: number }) => void
}

export default function OrderPanel({ marketId, currency, onSuccess }: Props) {
  const { tier, wallet, refetchWallet } = useAuth()
  const qc = useQueryClient()
  const [side, setSide] = useState<'yes' | 'no'>('yes')
  const [amount, setAmount] = useState('')

  const buy = useMutation({
    mutationFn: () => buyPosition(marketId, side, parseFloat(amount)),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ['market', marketId] })
      qc.invalidateQueries({ queryKey: ['positions', marketId] })
      refetchWallet()
      setAmount('')
      onSuccess?.(data)
    },
  })

  const balance = currency === 'coins' ? wallet?.prediction_coins ?? 0 : wallet?.real_credits_usd ?? 0
  const unit = currency === 'coins' ? 'PC' : 'MC'
  const canAfford = parseFloat(amount) > 0 && parseFloat(amount) <= balance

  if (tier === 'free') {
    return (
      <div className="bg-surface rounded-xl p-4 text-center">
        <p className="text-muted text-sm mb-3">Upgrade to Pro to place predictions</p>
        <a href="/billing" className="inline-block px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-hover transition-colors">
          Upgrade to Pro
        </a>
      </div>
    )
  }

  return (
    <div className="bg-surface rounded-xl p-4 space-y-4">
      <h3 className="text-sm font-semibold text-white">Place Prediction</h3>

      {/* Side selector */}
      <div className="grid grid-cols-2 gap-2">
        {(['yes', 'no'] as const).map((s) => (
          <button
            key={s}
            onClick={() => setSide(s)}
            className={`py-2 rounded-lg text-sm font-bold transition-colors ${
              side === s
                ? s === 'yes' ? 'bg-yes text-white' : 'bg-no text-white'
                : 'bg-white/5 text-muted hover:text-white'
            }`}
          >
            {s.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Amount input */}
      <div>
        <label className="text-xs text-muted block mb-1">Amount ({unit})</label>
        <input
          type="number"
          min={1}
          max={balance}
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder={`Balance: ${balance.toLocaleString()} ${unit}`}
          className="w-full bg-surface-2 text-white text-sm rounded-lg px-3 py-2 border border-white/10 focus:border-accent outline-none"
        />
      </div>

      {buy.isError && (
        <p className="text-xs text-no">
          {(buy.error as any)?.response?.data?.detail?.message || 'Something went wrong'}
        </p>
      )}

      <button
        onClick={() => buy.mutate()}
        disabled={!canAfford || buy.isPending}
        className={`w-full py-2 rounded-lg text-sm font-bold transition-colors ${
          side === 'yes'
            ? 'bg-yes hover:bg-yes/80 text-white'
            : 'bg-no hover:bg-no/80 text-white'
        } disabled:opacity-40 disabled:cursor-not-allowed`}
      >
        {buy.isPending ? 'Placing…' : `Buy ${side.toUpperCase()}`}
      </button>

      {buy.isSuccess && (
        <p className="text-xs text-yes text-center">
          Got {buy.data.shares.toFixed(4)} {side.toUpperCase()} shares!
        </p>
      )}
    </div>
  )
}
