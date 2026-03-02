import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getListings } from '../api/listings'
import { getCardSets } from '../api/cards'
import type { Listing } from '../api/listings'
import { useAuth } from '../context/AuthContext'
import PsaSlabFrame from '../components/shared/PsaSlabFrame'
import { ShoppingCart } from 'lucide-react'

const CONDITIONS = ['NM', 'LP', 'MP', 'HP', 'DMG']
const CONDITION_COLOR: Record<string, string> = {
  'GEM MT': 'text-yellow-300',
  NM: 'text-yes',
  LP: 'text-green-400',
  MP: 'text-yellow-400',
  HP: 'text-orange-400',
  DMG: 'text-red-400',
}

const LANGUAGES = [
  { code: '', label: 'All Languages' },
  { code: 'en', label: 'English' },
  { code: 'ja', label: 'Japanese' },
  { code: 'fr', label: 'French' },
  { code: 'de', label: 'German' },
  { code: 'es', label: 'Spanish' },
  { code: 'it', label: 'Italian' },
  { code: 'pt', label: 'Portuguese' },
  { code: 'ko', label: 'Korean' },
]

const PAGE_SIZE = 50

function GridCard({ listing, onClick }: { listing: Listing; onClick: () => void }) {
  const image = listing.card?.image_small ?? listing.product?.image_url
  const name = listing.card?.name ?? listing.product?.name ?? listing.title
  const setName = listing.card?.set_name ?? listing.product?.set_name ?? ''
  const isPsa = !!listing.grade
  return (
    <div onClick={onClick}
      className="bg-surface border border-white/5 rounded-xl overflow-hidden hover:border-accent/30 hover:shadow-red-glow transition-all cursor-pointer group">
      <div className={`bg-surface-2 flex items-center justify-center overflow-hidden relative ${isPsa ? 'p-2' : 'aspect-[3/4]'}`}>
        {isPsa ? (
          <PsaSlabFrame image={image ?? undefined} alt={name} grade={listing.grade!} size="sm" className="w-full group-hover:scale-105 transition-transform duration-300" />
        ) : image ? (
          <img src={image} alt={name} className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300" />
        ) : (
          <svg viewBox="0 0 60 84" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full opacity-40">
              <rect width="60" height="84" rx="4" fill="#2a2a38"/>
              <rect x="6" y="6" width="48" height="48" rx="2" fill="#333344"/>
              <rect x="6" y="62" width="32" height="5" rx="2" fill="#3a3a4e"/>
              <rect x="6" y="71" width="20" height="4" rx="2" fill="#333344"/>
            </svg>
        )}
      </div>
      <div className="p-3">
        <h3 className="font-bold text-white text-sm truncate">{name}</h3>
        {setName && <p className="text-xs text-muted truncate mb-1">{setName}</p>}
        <div className="flex items-center justify-between mt-2">
          <span className={`text-xs font-medium ${CONDITION_COLOR[listing.condition] ?? 'text-muted'}`}>
            {listing.condition}
          </span>
          <span className="text-white font-black text-lg">${listing.price.toFixed(2)}</span>
        </div>
        {listing.quantity > 1 && (
          <p className="text-xs text-muted mt-1">{listing.quantity} available</p>
        )}
      </div>
    </div>
  )
}

function ListRow({ listing, onClick }: { listing: Listing; onClick: () => void }) {
  const image = listing.card?.image_small ?? listing.product?.image_url
  const name = listing.card?.name ?? listing.product?.name ?? listing.title
  const setName = listing.card?.set_name ?? listing.product?.set_name ?? ''
  const isPsa = !!listing.grade
  return (
    <div onClick={onClick}
      className="flex items-center gap-4 px-4 py-3 bg-surface border border-white/5 rounded-xl hover:border-accent/30 transition-all cursor-pointer group">
      <div className="flex-shrink-0 w-12 h-16 bg-surface-2 rounded-lg overflow-hidden flex items-center justify-center">
        {isPsa ? (
          <PsaSlabFrame image={image ?? undefined} alt={name} grade={listing.grade!} size="sm" className="w-full h-full" />
        ) : image ? (
          <img src={image} alt={name} className="w-full h-full object-contain group-hover:scale-105 transition-transform" />
        ) : (
          <svg viewBox="0 0 60 84" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-10 h-14 opacity-40">
              <rect width="60" height="84" rx="4" fill="#2a2a38"/>
              <rect x="6" y="6" width="48" height="48" rx="2" fill="#333344"/>
              <rect x="6" y="62" width="32" height="5" rx="2" fill="#3a3a4e"/>
              <rect x="6" y="71" width="20" height="4" rx="2" fill="#333344"/>
            </svg>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-white truncate">{name}</p>
        {setName && <p className="text-xs text-muted truncate">{setName}</p>}
      </div>
      <div className="hidden sm:flex items-center gap-6 flex-shrink-0">
        <span className={`text-xs font-semibold w-8 ${CONDITION_COLOR[listing.condition] ?? 'text-muted'}`}>
          {listing.condition}
        </span>
        {listing.grade && (
          <span className="bg-blue-600 text-white text-xs font-bold px-1.5 py-0.5 rounded whitespace-nowrap">
            PSA {listing.grade}
          </span>
        )}
        <span className="text-xs text-muted w-16 text-center">
          ×{listing.quantity}
        </span>
        <span className="text-xs text-muted w-24 text-right">
          {listing.seller_email?.split('@')[0] ?? 'Seller'}
        </span>
        <span className="text-white font-black text-lg w-20 text-right">
          ${listing.price.toFixed(2)}
        </span>
      </div>
      <div className="flex-shrink-0 sm:hidden text-right">
        <div className={`text-xs font-semibold ${CONDITION_COLOR[listing.condition] ?? 'text-muted'}`}>{listing.condition}</div>
        <div className="text-white font-bold">${listing.price.toFixed(2)}</div>
      </div>
      <div className="flex-shrink-0">
        <span className="px-3 py-1.5 bg-accent hover:bg-accent-hover text-white text-xs font-semibold rounded-lg transition-colors">
          Buy
        </span>
      </div>
    </div>
  )
}

const GAME_CONFIG = {
  pokemon: { language: 'en',  label: 'Pokémon',    desc: 'Buy Pokémon TCG cards from collectors' },
  ygo:     { language: 'ygo', label: 'Yu-Gi-Oh!',  desc: 'Buy Yu-Gi-Oh! cards from collectors' },
  op:      { language: 'op',  label: 'One Piece',   desc: 'Buy One Piece TCG cards from collectors' },
}

export default function Marketplace({ game }: { game?: 'pokemon' | 'ygo' | 'op' }) {
  const gameConfig = game ? GAME_CONFIG[game] : null
  const navigate = useNavigate()
  const { isLoggedIn } = useAuth()
  const [search, setSearch] = useState('')
  const [condition, setCondition] = useState('')
  const [priceMax, setPriceMax] = useState('')
  const [itemType, setItemType] = useState('')
  const [language, setLanguage] = useState(gameConfig?.language ?? '')
  const [setCode, setSetCode] = useState('')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [sortBy, setSortBy] = useState<'price_asc' | 'price_desc' | 'newest'>('newest')
  const [offset, setOffset] = useState(0)
  const [allListings, setAllListings] = useState<Listing[]>([])

  // Fetch sets for the selected language
  const { data: sets } = useQuery({
    queryKey: ['card-sets', language],
    queryFn: () => getCardSets(language || 'en'),
    enabled: true,
    staleTime: 5 * 60_000,
  })

  const filters = { search, condition, price_max: priceMax ? Number(priceMax) : undefined, item_type: itemType, language, set_code: setCode, limit: PAGE_SIZE, offset: 0 }

  const { data: firstPage, isLoading } = useQuery({
    queryKey: ['listings', filters],
    queryFn: async () => {
      const result = await getListings(filters)
      setAllListings(result)
      setOffset(0)
      return result
    },
    refetchInterval: 30_000,
  })

  const [loadingMore, setLoadingMore] = useState(false)

  const loadMore = useCallback(async () => {
    setLoadingMore(true)
    const nextOffset = allListings.length
    try {
      const more = await getListings({ ...filters, offset: nextOffset })
      setAllListings(prev => [...prev, ...more])
      setOffset(nextOffset)
    } finally {
      setLoadingMore(false)
    }
  }, [allListings.length, filters])

  const hasMore = (firstPage?.length ?? 0) === PAGE_SIZE && allListings.length % PAGE_SIZE === 0 && allListings.length > 0

  const sorted = [...allListings].sort((a, b) => {
    if (sortBy === 'price_asc') return a.price - b.price
    if (sortBy === 'price_desc') return b.price - a.price
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  })

  const resetFilters = () => {
    setSearch(''); setCondition(''); setPriceMax(''); setItemType('')
    setLanguage(gameConfig?.language ?? ''); setSetCode(''); setAllListings([])
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{gameConfig ? `${gameConfig.label} Marketplace` : 'Marketplace'}</h1>
          <p className="text-sm text-muted mt-0.5">
            {gameConfig ? gameConfig.desc : 'Buy TCG cards from collectors'}
            {allListings.length > 0 && <span> · {allListings.length.toLocaleString()} listings loaded</span>}
          </p>
        </div>
        {isLoggedIn && (
          <button
            onClick={() => navigate('/sell/new')}
            className="px-4 py-2 bg-accent hover:bg-accent-hover text-white text-sm font-semibold rounded-xl transition-colors"
          >
            + Sell a Card
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="space-y-3">
        {/* Row 1: search + condition + price */}
        <div className="flex flex-wrap gap-3">
          <input
            type="text"
            placeholder="Search listings…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setAllListings([]) }}
            className="flex-1 min-w-48 px-3 py-2 bg-surface border border-white/10 rounded-xl text-sm text-white placeholder-muted focus:outline-none focus:border-accent"
          />
          <select value={condition} onChange={(e) => { setCondition(e.target.value); setAllListings([]) }}
            className="px-3 py-2 bg-surface border border-white/10 rounded-xl text-sm text-white focus:outline-none focus:border-accent">
            <option value="">All conditions</option>
            {CONDITIONS.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <select value={itemType} onChange={(e) => { setItemType(e.target.value); setAllListings([]) }}
            className="px-3 py-2 bg-surface border border-white/10 rounded-xl text-sm text-white focus:outline-none focus:border-accent">
            <option value="">All types</option>
            <option value="card">Cards</option>
            <option value="sealed">Sealed</option>
          </select>
          <input
            type="number"
            placeholder="Max $"
            value={priceMax}
            onChange={(e) => { setPriceMax(e.target.value); setAllListings([]) }}
            className="w-28 px-3 py-2 bg-surface border border-white/10 rounded-xl text-sm text-white placeholder-muted focus:outline-none focus:border-accent"
          />
        </div>

        {/* Row 2: language + set */}
        <div className="flex flex-wrap gap-3">
          {!gameConfig && (
            <select value={language} onChange={(e) => { setLanguage(e.target.value); setSetCode(''); setAllListings([]) }}
              className="px-3 py-2 bg-surface border border-white/10 rounded-xl text-sm text-white focus:outline-none focus:border-accent">
              {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
          )}
          <select value={setCode} onChange={(e) => { setSetCode(e.target.value); setAllListings([]) }}
            className="flex-1 min-w-48 px-3 py-2 bg-surface border border-white/10 rounded-xl text-sm text-white focus:outline-none focus:border-accent">
            <option value="">All Sets</option>
            {(sets ?? []).map((s) => (
              <option key={s.set_code} value={s.set_code}>{s.set_name}</option>
            ))}
          </select>
          {(search || condition || priceMax || itemType || language || setCode) && (
            <button onClick={resetFilters} className="px-3 py-2 text-xs text-muted hover:text-white border border-white/10 rounded-xl transition-colors">
              Clear filters
            </button>
          )}
        </div>

        {/* Row 3: sort + view toggle */}
        <div className="flex items-center justify-between">
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)}
            className="px-3 py-1.5 bg-surface border border-white/10 rounded-lg text-xs text-white focus:outline-none focus:border-accent">
            <option value="newest">Newest first</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
          </select>

          <div className="flex bg-surface border border-white/10 rounded-lg overflow-hidden">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1.5 text-xs transition-colors ${viewMode === 'grid' ? 'bg-accent text-white' : 'text-muted hover:text-white'}`}
              title="Grid view"
            >
              ⊞
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 text-xs transition-colors ${viewMode === 'list' ? 'bg-accent text-white' : 'text-muted hover:text-white'}`}
              title="List view"
            >
              ≡
            </button>
          </div>
        </div>
      </div>

      {/* List view header */}
      {viewMode === 'list' && sorted.length > 0 && (
        <div className="hidden sm:grid grid-cols-12 gap-4 px-4 text-xs text-muted border-b border-white/10 pb-2">
          <div className="col-span-5">Card</div>
          <div className="col-span-1">Cond.</div>
          <div className="col-span-1 text-center">Qty</div>
          <div className="col-span-2 text-right">Seller</div>
          <div className="col-span-2 text-right">Price</div>
          <div className="col-span-1"></div>
        </div>
      )}

      {/* Listings */}
      {isLoading ? (
        viewMode === 'grid' ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
            {[...Array(15)].map((_, i) => (
              <div key={i} className="bg-surface rounded-xl aspect-[3/4] animate-pulse" />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="bg-surface rounded-xl h-20 animate-pulse" />
            ))}
          </div>
        )
      ) : sorted.length > 0 ? (
        <>
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {sorted.map((listing) => (
                <GridCard key={listing.id} listing={listing} onClick={() => navigate(`/marketplace/${listing.id}`)} />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {sorted.map((listing) => (
                <ListRow key={listing.id} listing={listing} onClick={() => navigate(`/marketplace/${listing.id}`)} />
              ))}
            </div>
          )}

          {/* Load More */}
          {hasMore && (
            <div className="flex justify-center pt-4">
              <button
                onClick={loadMore}
                disabled={loadingMore}
                className="px-8 py-2.5 bg-surface border border-white/10 hover:border-accent/40 text-white text-sm font-medium rounded-xl transition-colors disabled:opacity-50"
              >
                {loadingMore ? 'Loading…' : `Load More (showing ${sorted.length.toLocaleString()})`}
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="text-center py-24 text-muted">
          <ShoppingCart size={40} className="mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium text-white mb-2">No listings found</p>
          <p className="text-sm mb-6">Try adjusting your filters or be the first to list a card!</p>
          {isLoggedIn && (
            <button
              onClick={() => navigate('/sell/new')}
              className="px-6 py-2.5 bg-accent hover:bg-accent-hover text-white font-semibold rounded-xl transition-colors"
            >
              Create a Listing
            </button>
          )}
        </div>
      )}
    </div>
  )
}
