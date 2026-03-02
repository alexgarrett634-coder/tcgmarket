import { useNavigate } from 'react-router-dom'
import type { Listing } from '../../api/listings'
import PsaSlabFrame from '../shared/PsaSlabFrame'

const CONDITION_COLOR: Record<string, string> = {
  NM: 'text-yes',
  LP: 'text-green-400',
  MP: 'text-yellow-400',
  HP: 'text-orange-400',
  DMG: 'text-red-400',
}

interface Props {
  listing: Listing
}

export default function ListingCard({ listing }: Props) {
  const navigate = useNavigate()
  const image = listing.card?.image_small ?? listing.product?.image_url
  const name = listing.card?.name ?? listing.product?.name ?? listing.title
  const setName = listing.card?.set_name ?? listing.product?.set_name ?? ''
  const condColor = CONDITION_COLOR[listing.condition] ?? 'text-muted'

  return (
    <div
      onClick={() => navigate(`/marketplace/${listing.id}`)}
      className="bg-surface border border-white/5 rounded-xl overflow-hidden hover:border-accent/30 hover:shadow-red-glow transition-all cursor-pointer group"
    >
      {/* Image — PSA slab for graded, plain for ungraded */}
      {listing.grade ? (
        <div className="p-3 flex justify-center bg-gradient-to-b from-surface-2 to-surface">
          <PsaSlabFrame
            image={image}
            alt={name}
            grade={listing.grade}
            size="sm"
            className="w-full max-w-[140px]"
          />
        </div>
      ) : (
        <div className="aspect-[3/4] bg-surface-2 flex items-center justify-center overflow-hidden relative">
          {image ? (
            <img src={image} alt={name} className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300" />
          ) : (
            <svg viewBox="0 0 60 84" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-12 h-16 opacity-40">
              <rect width="60" height="84" rx="4" fill="#2a2a38"/>
              <rect x="6" y="6" width="48" height="48" rx="2" fill="#333344"/>
              <rect x="6" y="62" width="32" height="5" rx="2" fill="#3a3a4e"/>
              <rect x="6" y="71" width="20" height="4" rx="2" fill="#333344"/>
            </svg>
          )}
        </div>
      )}

      {/* Info */}
      <div className="p-3">
        <h3 className="font-bold text-white text-sm truncate">{name}</h3>
        {setName && <p className="text-xs text-muted truncate mb-1">{setName}</p>}
        <div className="flex items-center justify-between mt-2">
          <span className={`text-xs font-medium ${condColor}`}>{listing.condition}</span>
          <span className="text-white font-black text-lg">${listing.price.toFixed(2)}</span>
        </div>
        {listing.quantity > 1 && (
          <p className="text-xs text-muted mt-1">{listing.quantity} available</p>
        )}
      </div>
    </div>
  )
}
