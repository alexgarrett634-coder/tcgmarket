import { useNavigate } from 'react-router-dom'
import AnimatedBg from '../components/shared/AnimatedBg'
import { ShoppingCart, Tag, BarChart2, Eye, Briefcase, Search } from 'lucide-react'

const FEATURES = [
  { Icon: ShoppingCart, title: 'Buy & Sell Instantly', desc: 'List your Pokemon TCG cards and sealed products in seconds. Buyers find what they need — you get paid directly.' },
  { Icon: Tag,          title: 'Live Deals Finder', desc: 'Real-time eBay scanner spots active listings below market value and streams them to you instantly.' },
  { Icon: BarChart2,    title: 'Price Tracking', desc: 'PriceCharting and eBay prices in one place. 90-day price history charts so you always know the true market value.' },
  { Icon: Eye,          title: 'Watchlist & Alerts', desc: 'Watch your favorite cards and get email alerts when prices move above or below your thresholds.' },
  { Icon: Briefcase,    title: 'Portfolio Tracker', desc: "Track every card you own with live P&L calculations so you always know what your collection's worth." },
  { Icon: Search,       title: 'Full Card Database', desc: 'Every Pokemon TCG card ever printed — search by name, set, rarity, or condition across thousands of listings.' },
]

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div className="relative min-h-screen bg-bg text-white">
      <AnimatedBg />
      <div className="relative z-10">
        {/* Nav */}
        <nav className="flex items-center justify-between px-6 py-4 border-b border-white/5">
          <div className="flex items-center gap-2">
            <img src="/logo.svg" className="w-8 h-8" alt="TCGMarket" />
            <span className="text-lg font-bold">TCGMarket</span>
          </div>
          <div className="flex gap-3">
            <button onClick={() => navigate('/login')} className="text-sm text-muted hover:text-white transition-colors">Sign in</button>
            <button onClick={() => navigate('/register')} className="px-4 py-2 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-lg transition-colors">Start Selling Free</button>
          </div>
        </nav>

        {/* Hero */}
        <section className="max-w-5xl mx-auto text-center px-6 py-20">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-accent/10 text-accent rounded-full text-xs font-medium mb-6">
            <ShoppingCart size={12} strokeWidth={2} />
            TCG Marketplace
          </div>
          <h1 className="text-5xl font-black leading-tight mb-4">
            Buy &amp; Sell TCG Cards<br />at the Best Price.
          </h1>
          <p className="text-gray-400 text-lg max-w-xl mx-auto mb-8">
            The dedicated TCG marketplace for Pokémon, Yu-Gi-Oh!, One Piece, and more. List your cards in seconds, find deals, track price history, and manage your collection — all in one fast, dark dashboard.
          </p>
          <div className="flex items-center justify-center gap-4">
            <button onClick={() => navigate('/register')} className="px-8 py-3 bg-accent hover:bg-accent-hover text-white font-bold rounded-xl transition-colors text-lg">
              Start Selling — It's Free
            </button>
            <button onClick={() => navigate('/marketplace')} className="px-8 py-3 border border-white/20 hover:border-white/40 text-white rounded-xl transition-colors text-lg">
              Browse Marketplace
            </button>
          </div>
        </section>

        {/* Features */}
        <section className="max-w-5xl mx-auto px-6 py-16">
          <h2 className="text-2xl font-bold text-center mb-10">Everything you need for TCG trading</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f) => (
              <div key={f.title} className="bg-surface border border-white/5 rounded-xl p-5 hover:border-accent/20 transition-colors">
                <div className="mb-3 text-accent"><f.Icon size={22} strokeWidth={1.5} /></div>
                <h3 className="font-bold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-muted leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="max-w-2xl mx-auto px-6 py-16 text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to start trading?</h2>
          <p className="text-muted text-sm mb-8">Create a free account and start buying or selling TCG cards today.</p>
          <button onClick={() => navigate('/register')} className="px-10 py-3 bg-accent hover:bg-accent-hover text-white font-bold rounded-xl transition-colors text-lg">
            Create Free Account
          </button>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/5 px-6 py-8 text-center text-xs text-muted">
          <p>© 2025 TCGMarket. Not affiliated with The Pokémon Company, Konami, or Bandai. All card names and images are trademarks of their respective owners.</p>
        </footer>
      </div>
    </div>
  )
}
