import { useQuery } from '@tanstack/react-query'
import { getPortfolio } from '../api/portfolio'
import { Briefcase } from 'lucide-react'

function pnlColor(pnl: number) {
  if (pnl > 0) return 'text-yes'
  if (pnl < 0) return 'text-no'
  return 'text-muted'
}

export default function Portfolio() {
  const { data, isLoading } = useQuery({ queryKey: ['portfolio'], queryFn: getPortfolio })

  if (isLoading) return <div className="animate-pulse space-y-3">{[...Array(5)].map((_, i) => <div key={i} className="h-16 bg-surface rounded-xl" />)}</div>

  const summary = data?.summary
  const items = data?.items ?? []

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Portfolio</h1>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Total Cost', value: `$${summary.total_cost.toFixed(2)}`, color: 'text-white' },
            { label: 'Total Value', value: `$${summary.total_value.toFixed(2)}`, color: 'text-white' },
            { label: 'P&L', value: `${summary.total_pnl >= 0 ? '+' : ''}$${summary.total_pnl.toFixed(2)}`, color: pnlColor(summary.total_pnl) },
            { label: 'P&L %', value: summary.total_pnl_pct != null ? `${summary.total_pnl_pct >= 0 ? '+' : ''}${summary.total_pnl_pct.toFixed(1)}%` : '—', color: pnlColor(summary.total_pnl) },
          ].map((s) => (
            <div key={s.label} className="bg-surface rounded-xl border border-white/5 p-4">
              <div className="text-xs text-muted mb-1">{s.label}</div>
              <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {items.length === 0 ? (
        <div className="text-center py-20 text-muted">
          <Briefcase size={32} className="mx-auto mb-3 opacity-40" />
          <p>No items in portfolio yet.</p>
        </div>
      ) : (
        <div className="bg-surface rounded-xl border border-white/5 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 text-muted text-xs">
                <th className="text-left px-4 py-3">Item</th>
                <th className="text-right px-4 py-3">Qty</th>
                <th className="text-right px-4 py-3">Cost</th>
                <th className="text-right px-4 py-3">Value</th>
                <th className="text-right px-4 py-3">P&L</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-white/5 hover:bg-white/2 transition-colors">
                  <td className="px-4 py-3">
                    <p className="text-white font-medium">{item.card_id || `Product #${item.product_id}`}</p>
                    <p className="text-xs text-muted">{item.condition}</p>
                  </td>
                  <td className="px-4 py-3 text-right text-white">{item.quantity}</td>
                  <td className="px-4 py-3 text-right text-muted">${item.total_cost.toFixed(2)}</td>
                  <td className="px-4 py-3 text-right text-white">${item.total_value.toFixed(2)}</td>
                  <td className={`px-4 py-3 text-right font-medium ${pnlColor(item.pnl)}`}>
                    {item.pnl >= 0 ? '+' : ''}${item.pnl.toFixed(2)}
                    {item.pnl_pct != null && (
                      <span className="text-xs ml-1">({item.pnl_pct.toFixed(1)}%)</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
