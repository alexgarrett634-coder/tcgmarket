import { NavLink, useNavigate } from 'react-router-dom'
import {
  ShoppingCart, Tag, BarChart2, PackagePlus,
  ClipboardList, Store, Eye, Briefcase, Settings, Layers, Anchor,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import NotificationBell from './NotificationBell'

const pokemonNav = [
  { to: '/marketplace', label: 'Marketplace', Icon: ShoppingCart },
  { to: '/deals',       label: 'Deals',       Icon: Tag },
  { to: '/prices',      label: 'Pokémon TCG', Icon: BarChart2 },
]

const ygoNav = [
  { to: '/ygo', label: 'Yu-Gi-Oh!', Icon: Layers },
]

const opNav = [
  { to: '/op', label: 'One Piece', Icon: Anchor },
]

const authNav = [
  { to: '/sell/new',          label: 'Sell',       Icon: PackagePlus },
  { to: '/orders',            label: 'Orders',     Icon: ClipboardList },
  { to: '/seller/dashboard',  label: 'Seller Hub', Icon: Store },
  { to: '/watchlist',         label: 'Watchlist',  Icon: Eye },
  { to: '/portfolio',         label: 'Portfolio',  Icon: Briefcase },
  { to: '/settings',          label: 'Settings',   Icon: Settings },
]

function NavItem({ to, label, Icon }: { to: string; label: string; Icon: React.ElementType }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150 border-l-2 ${
          isActive
            ? 'border-accent bg-accent/10 text-white'
            : 'border-transparent text-gray-400 hover:text-white hover:bg-white/5 hover:translate-x-0.5'
        }`
      }
    >
      <Icon size={15} strokeWidth={1.75} className="flex-shrink-0" />
      {label}
    </NavLink>
  )
}

export default function Sidebar() {
  const { isLoggedIn, logout, user } = useAuth()
  const navigate = useNavigate()

  return (
    <aside className="fixed top-0 left-0 h-full w-56 bg-surface flex flex-col z-20" style={{ borderRight: '1px solid rgba(255,255,255,0.06)' }}>
      {/* Logo */}
      <div
        className="px-4 py-5 flex items-center gap-2.5 cursor-pointer select-none"
        onClick={() => navigate('/')}
        style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}
      >
        <img src="/logo.svg" className="w-7 h-7" alt="TCGMarket" />
        <span className="text-base font-semibold text-white tracking-tight">TCGMarket</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        <p className="px-3 pt-1 pb-0.5 text-[10px] font-semibold uppercase tracking-widest text-muted/60">Pokémon</p>
        {pokemonNav.map((item) => (
          <NavItem key={item.to} {...item} />
        ))}

        <div className="my-2 mx-2" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }} />
        <p className="px-3 pt-1 pb-0.5 text-[10px] font-semibold uppercase tracking-widest text-muted/60">Yu-Gi-Oh!</p>
        {ygoNav.map((item) => (
          <NavItem key={item.to} {...item} />
        ))}

        <div className="my-2 mx-2" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }} />
        <p className="px-3 pt-1 pb-0.5 text-[10px] font-semibold uppercase tracking-widest text-muted/60">One Piece</p>
        {opNav.map((item) => (
          <NavItem key={item.to} {...item} />
        ))}

        {isLoggedIn && authNav.length > 0 && (
          <>
            <div className="my-2 mx-2" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }} />
            {authNav.map((item) => (
              <NavItem key={item.to} {...item} />
            ))}
          </>
        )}
      </nav>

      {/* Bottom */}
      <div className="px-3 pb-4 pt-3 space-y-1" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        {isLoggedIn && (
          <>
            <NotificationBell />
            {user?.email && (
              <p className="px-1 py-1 text-xs text-gray-500 truncate">{user.email}</p>
            )}
            <button
              onClick={logout}
              className="w-full text-left px-3 py-2 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
            >
              Sign out
            </button>
          </>
        )}
        {!isLoggedIn && (
          <NavLink
            to="/login"
            className="block px-3 py-2 text-sm text-center bg-accent hover:bg-accent-hover text-white rounded-lg transition-colors font-medium"
          >
            Sign in
          </NavLink>
        )}
      </div>
    </aside>
  )
}
