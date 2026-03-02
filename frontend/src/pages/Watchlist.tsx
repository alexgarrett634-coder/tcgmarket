import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getWatchlist, removeFromWatchlist } from '../api/watchlist'
import { Eye } from 'lucide-react'

export default function Watchlist() {
  const qc = useQueryClient()
  const { data: items, isLoading } = useQuery({ queryKey: ['watchlist'], queryFn: getWatchlist })

  const remove = useMutation({
    mutationFn: removeFromWatchlist,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  })

  if (isLoading) return <div className="animate-pulse space-y-3">{[...Array(5)].map((_, i) => <div key={i} className="h-14 bg-surface rounded-xl" />)}</div>

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Watchlist</h1>

      {!items || items.length === 0 ? (
        <div className="text-center py-20 text-muted">
          <Eye size={32} className="mx-auto mb-3 opacity-40" />
          <p>No items in watchlist. Search for a card and add it.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.id} className="bg-surface rounded-xl border border-white/5 px-4 py-3 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white">{item.card_id || `Product #${item.product_id}`}</p>
                <p className="text-xs text-muted">{item.preferred_source}</p>
                {item.alert_above && <span className="text-xs text-yes">Alert ↑ ${item.alert_above}</span>}
                {item.alert_below && <span className="text-xs text-no ml-2">Alert ↓ ${item.alert_below}</span>}
              </div>
              <button
                onClick={() => remove.mutate(item.id)}
                className="text-muted hover:text-no transition-colors text-sm"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
