import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { searchCards, getCardPrices, getCardSets } from '../api/cards'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'

const POPULAR_SEARCHES = [
  'Charizard', 'Pikachu', 'Mewtwo', 'Umbreon', 'Rayquaza',
  'Lugia', 'Eevee', 'Gengar', 'Mew', 'Blastoise',
]

const HIGH_VALUE = [
  { name: 'Charizard ex', set: '151', id: 'sv3pt5-6' },
  { name: 'Umbreon ex', set: 'Prismatic Evolutions', id: 'sv8pt5-161' },
  { name: 'Charizard VMAX', set: "Champion's Path", id: 'swsh35-74' },
  { name: 'Umbreon VMAX', set: 'Evolving Skies', id: 'swsh7-215' },
]

const SETS_PAGE_SIZE = 60

function pickBestPrice(current: { source: string; price_type: string; price_usd: number }[] | undefined, type: string) {
  if (!current) return undefined
  return current.find((p) => p.price_type === type && p.source === 'pricecharting')
      ?? current.find((p) => p.price_type === type)
}

function PriceChip({ cardId }: { cardId: string }) {
  const { data } = useQuery({
    queryKey: ['card-prices-chip', cardId],
    queryFn: () => getCardPrices(cardId),
    staleTime: 60_000,
  })
  const price = pickBestPrice(data?.current, 'near_mint') ?? pickBestPrice(data?.current, 'market')
  if (!price) return <span className="text-xs text-muted">—</span>
  return <span className="text-sm font-bold text-accent">${price.price_usd.toFixed(2)}</span>
}

export default function Prices() {
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
    queryKey: ['card-search', debouncedQ],
    queryFn: () => searchCards(debouncedQ),
    enabled: debouncedQ.length >= 2,
  })

  const { data: allSets } = useQuery<{ set_code: string; set_name: string }[]>({
    queryKey: ['all-sets'],
    queryFn: () => getCardSets(),
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
        <h1 className="text-2xl font-bold text-white">Card Prices</h1>
        <p className="text-sm text-muted mt-1">Real-time Pokemon TCG market prices · 22,755+ cards</p>
      </div>

      {/* Search bar */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            type="text"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search by card name, set, or Pokémon…"
            className="w-full bg-surface text-white rounded-xl px-4 py-3 pl-9 text-sm border border-white/10 focus:border-accent outline-none"
            autoFocus
          />
          {q && (
            <button type="button" onClick={() => { setQ(''); setDebouncedQ('') }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-white text-lg leading-none">×</button>
          )}
        </div>
        <button type="submit" className="px-6 py-3 bg-accent hover:bg-accent-hover text-white text-sm font-semibold rounded-xl transition-colors">
          Search
        </button>
      </form>

      {/* Popular searches */}
      {!showResults && (
        <div className="flex flex-wrap gap-2 items-center">
          <span className="text-xs text-muted">Popular:</span>
          {POPULAR_SEARCHES.map((term) => (
            <button key={term} onClick={() => { setQ(term); setDebouncedQ(term) }}
              className="px-3 py-1.5 bg-surface border border-white/10 hover:border-accent/40 rounded-full text-xs text-white transition-colors">
              {term}
            </button>
          ))}
        </div>
      )}

      {/* Search results */}
      {showResults && (
        isLoading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {[...Array(10)].map((_, i) => <div key={i} className="bg-surface rounded-xl h-56 animate-pulse" />)}
          </div>
        ) : cards.length > 0 ? (
          <div className="space-y-3">
            <p className="text-xs text-muted">{cards.length} results for &ldquo;{debouncedQ}&rdquo;</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {cards.map((card) => (
                <div key={card.id} onClick={() => navigate(`/prices/card/${card.id}`)}
                  className="bg-surface rounded-xl border border-white/5 overflow-hidden cursor-pointer hover:border-accent/40 hover:shadow-glow transition-all group">
                  <div className="bg-black/20">
                    {card.image_small ? (
                      <img src={card.image_small} alt={card.name}
                        className="w-full object-contain group-hover:scale-105 transition-transform duration-300"
                        style={{ height: 160 }} />
                    ) : (
                      <div className="w-full h-40 flex items-center justify-center">
                        <svg viewBox="0 0 60 84" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-16 h-24 opacity-60">
                          <rect width="60" height="84" rx="4" fill="#2a2a38"/>
                          <rect x="6" y="6" width="48" height="48" rx="2" fill="#333344"/>
                          <rect x="6" y="62" width="32" height="5" rx="2" fill="#3a3a4e"/>
                          <rect x="6" y="71" width="20" height="4" rx="2" fill="#333344"/>
                        </svg>
                      </div>
                    )}
                  </div>
                  <div className="p-3 space-y-1">
                    <p className="text-sm font-semibold text-white truncate">{card.name}</p>
                    <p className="text-xs text-muted truncate">{card.set_name}</p>
                    {card.rarity && <p className="text-xs text-muted/70 truncate">{card.rarity}</p>}
                    <div className="pt-1.5 border-t border-white/5 flex items-center justify-between">
                      <span className="text-xs text-muted">Market</span>
                      <PriceChip cardId={card.id} />
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
            <p className="text-sm">Try a Pokémon name or set name</p>
          </div>
        )
      )}

      {/* Browse when no search */}
      {!showResults && (
        <div className="space-y-8">
          {/* Browse sets — loaded from API */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white">
                Browse Sets
                {allSets && <span className="ml-2 text-xs text-muted font-normal">({allSets.length} sets)</span>}
              </h2>
              {allSets && allSets.length > SETS_PAGE_SIZE && (
                <button onClick={() => setShowAllSets(v => !v)}
                  className="text-xs text-accent hover:underline">
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
                    className="bg-surface border border-white/5 hover:border-accent/40 rounded-xl p-4 text-left transition-all hover:shadow-glow group">
                    <p className="text-sm font-semibold text-white group-hover:text-accent transition-colors truncate">{set.set_name}</p>
                    <p className="text-xs text-muted mt-0.5 uppercase tracking-wide">{set.set_code}</p>
                  </button>
                ))}
            </div>
          </div>

          {/* High value cards */}
          <div className="space-y-3">
            <h2 className="text-base font-semibold text-white">High-Value Cards</h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {HIGH_VALUE.map((c) => (
                <div key={c.id} onClick={() => navigate(`/prices/card/${c.id}`)}
                  className="bg-surface border border-white/5 hover:border-accent/40 rounded-xl p-4 cursor-pointer transition-all hover:shadow-glow">
                  <p className="text-sm font-semibold text-white">{c.name}</p>
                  <p className="text-xs text-muted mt-0.5 mb-2">{c.set}</p>
                  <PriceChip cardId={c.id} />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
