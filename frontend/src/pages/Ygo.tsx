import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchYgoCards, getYgoCardPrices, getYgoCardSets } from '../api/ygo'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'

const POPULAR_SEARCHES = [
  'Blue-Eyes White Dragon', 'Dark Magician', 'Exodia', 'Red-Eyes Black Dragon',
  'Jinzo', 'Mirror Force', 'Pot of Greed', 'Chaos Emperor Dragon',
]

const HIGH_VALUE = [
  { name: 'Blue-Eyes White Dragon', set: 'Legend of Blue Eyes White Dragon', code: 'LOB-EN001' },
  { name: 'Dark Magician', set: 'Legend of Blue Eyes White Dragon', code: 'LOB-EN005' },
  { name: 'Exodia the Forbidden One', set: 'Legend of Blue Eyes White Dragon', code: 'LOB-EN124' },
  { name: 'Chaos Emperor Dragon', set: 'IOC', code: 'IOC-000' },
]

const SETS_PAGE_SIZE = 60

function pickBest(current: { source: string; price_type: string; price_usd: number }[] | undefined, type: string) {
  return current?.find((p) => p.price_type === type && p.source === 'pricecharting')
      ?? current?.find((p) => p.price_type === type)
}

function YgoPriceChip({ cardId }: { cardId: string }) {
  const { data } = useQuery({
    queryKey: ['ygo-prices-chip', cardId],
    queryFn: () => getYgoCardPrices(cardId),
    staleTime: 60_000,
  })
  const price = pickBest(data?.current, 'near_mint') ?? pickBest(data?.current, 'market')
  if (!price) return <span className="text-xs text-muted">—</span>
  return <span className="text-sm font-bold text-yellow-400">${price.price_usd.toFixed(2)}</span>
}

export default function Ygo() {
  const [q, setQ] = useState('')
  const [debouncedQ, setDebouncedQ] = useState('')
  const [showAllSets, setShowAllSets] = useState(false)
  const navigate = useNavigate()
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    clearTimeout(debounceRef.current)
    if (q.length >= 2) {
      debounceRef.current = setTimeout(() => setDebouncedQ(q), 350)
    } else {
      setDebouncedQ('')
    }
    return () => clearTimeout(debounceRef.current)
  }, [q])

  const { data, isLoading } = useQuery({
    queryKey: ['ygo-search', debouncedQ],
    queryFn: () => searchYgoCards(debouncedQ),
    enabled: debouncedQ.length >= 2,
  })

  const { data: allSets } = useQuery({
    queryKey: ['ygo-sets'],
    queryFn: getYgoCardSets,
    staleTime: 300_000,
  })

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (q.length >= 1) setDebouncedQ(q)
  }

  const cards = data?.results ?? []
  const showResults = debouncedQ.length >= 2

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Yu-Gi-Oh! Prices</h1>
        <p className="text-sm text-muted mt-1">Real-time YGO card market prices · PriceCharting data</p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            type="text"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by card name or set…"
            className="w-full bg-surface text-white rounded-xl px-4 py-3 pl-9 text-sm border border-white/10 focus:border-yellow-400/50 outline-none"
            autoFocus
          />
          {q && (
            <button type="button" onClick={() => { setQ(''); setDebouncedQ('') }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-white text-lg leading-none">×</button>
          )}
        </div>
        <button type="submit" className="px-6 py-3 bg-yellow-500 hover:bg-yellow-400 text-black text-sm font-semibold rounded-xl transition-colors">
          Search
        </button>
      </form>

      {/* Popular searches */}
      {!showResults && (
        <div className="flex flex-wrap gap-2 items-center">
          <span className="text-xs text-muted">Popular:</span>
          {POPULAR_SEARCHES.map((term) => (
            <button key={term} onClick={() => { setQ(term); setDebouncedQ(term) }}
              className="px-3 py-1.5 bg-surface border border-white/10 hover:border-yellow-400/40 rounded-full text-xs text-white transition-colors">
              {term}
            </button>
          ))}
        </div>
      )}

      {/* Search results */}
      {showResults && (
        isLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {[...Array(10)].map((_, i) => <div key={i} className="bg-surface rounded-xl h-40 animate-pulse" />)}
          </div>
        ) : cards.length > 0 ? (
          <div className="space-y-3">
            <p className="text-xs text-muted">{cards.length} results for &ldquo;{debouncedQ}&rdquo;</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {cards.map((card) => (
                <div key={card.id} onClick={() => navigate(`/ygo/card/${card.id}`)}
                  className="bg-surface rounded-xl border border-white/5 overflow-hidden cursor-pointer hover:border-yellow-400/40 hover:shadow-lg transition-all group">
                  {/* Card image */}
                  <div className="aspect-[3/4] bg-surface-2 flex items-center justify-center overflow-hidden">
                    {card.image_small ? (
                      <img src={card.image_small} alt={card.name}
                        className="w-full h-full object-contain"
                        onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
                    ) : (
                      <span className="text-2xl opacity-30">⚔️</span>
                    )}
                  </div>
                  <div className="p-3">
                    <p className="text-sm font-semibold text-white truncate">{card.name}</p>
                    <p className="text-xs text-yellow-400/70 truncate">{card.set_code}</p>
                    <div className="pt-2 mt-1 border-t border-white/5 flex items-center justify-between">
                      <span className="text-xs text-muted">NM</span>
                      <YgoPriceChip cardId={card.id} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-16 text-muted">
            <Search size={28} className="mx-auto mb-3 opacity-40" />
            <p className="text-white font-medium mb-1">No cards found for &ldquo;{debouncedQ}&rdquo;</p>
            <p className="text-sm">Try a card name or set code like &ldquo;LOB&rdquo;</p>
          </div>
        )
      )}

      {/* Browse when no search */}
      {!showResults && (
        <div className="space-y-8">
          {/* Browse sets */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white">
                Browse Sets
                {allSets && <span className="ml-2 text-xs text-muted font-normal">({allSets.length} sets)</span>}
              </h2>
              {allSets && allSets.length > SETS_PAGE_SIZE && (
                <button onClick={() => setShowAllSets(v => !v)}
                  className="text-xs text-yellow-400 hover:underline">
                  {showAllSets ? 'Show less' : `Show all ${allSets.length}`}
                </button>
              )}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {(allSets ?? [])
                .slice(0, showAllSets ? undefined : SETS_PAGE_SIZE)
                .map((set) => (
                  <button key={set.set_code}
                    onClick={() => { setQ(set.set_name); setDebouncedQ(set.set_name) }}
                    className="bg-surface border border-white/5 hover:border-yellow-400/40 rounded-xl p-4 text-left transition-all hover:shadow-lg group">
                    <p className="text-sm font-semibold text-white group-hover:text-yellow-400 transition-colors truncate">{set.set_name}</p>
                    <p className="text-xs text-muted mt-0.5 uppercase tracking-wide">{set.set_code}</p>
                  </button>
                ))}
            </div>
          </div>

          {/* High value cards */}
          <div className="space-y-3">
            <h2 className="text-base font-semibold text-white">Popular Cards</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {HIGH_VALUE.map((c) => (
                <div key={c.code}
                  onClick={() => { setQ(c.name); setDebouncedQ(c.name) }}
                  className="bg-surface border border-white/5 hover:border-yellow-400/40 rounded-xl p-4 cursor-pointer transition-all hover:shadow-lg">
                  <p className="text-sm font-semibold text-white">{c.name}</p>
                  <p className="text-xs text-muted mt-0.5">{c.set}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
