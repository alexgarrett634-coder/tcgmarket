import { useState } from 'react'

interface Props {
  onAccept: () => void
}

export default function RealMoneyDisclaimer({ onAccept }: Props) {
  const [checked, setChecked] = useState(false)

  return (
    <div className="bg-surface border border-yellow-500/30 rounded-xl p-6 space-y-4">
      <div className="flex items-start gap-3">
        <span className="text-2xl">⚠️</span>
        <div>
          <h3 className="text-white font-semibold mb-1">Real-Money Prediction Markets</h3>
          <p className="text-sm text-muted leading-relaxed">
            Real-money prediction markets are regulated financial instruments. Participation may be restricted in your jurisdiction. By continuing you confirm:
          </p>
        </div>
      </div>

      <ul className="text-sm text-muted space-y-1 pl-4 list-disc">
        <li>You are at least 18 years old</li>
        <li>You are not located in a restricted jurisdiction (US states where prediction markets are prohibited)</li>
        <li>You understand you may lose your entire stake</li>
        <li>This is not financial advice</li>
      </ul>

      <label className="flex items-center gap-3 cursor-pointer">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => setChecked(e.target.checked)}
          className="w-4 h-4 accent-accent"
        />
        <span className="text-sm text-white">I understand and agree to the above terms</span>
      </label>

      <button
        disabled={!checked}
        onClick={onAccept}
        className="w-full py-2.5 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
      >
        Access Real-Money Markets
      </button>
    </div>
  )
}
