import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/layout/Layout'

import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import Marketplace from './pages/Marketplace'
import ListingDetail from './pages/ListingDetail'
import NewListing from './pages/NewListing'
import SellerDashboard from './pages/SellerDashboard'
import Orders from './pages/Orders'
import Deals from './pages/Deals'
import Prices from './pages/Prices'
import CardDetail from './pages/CardDetail'
import Ygo from './pages/Ygo'
import YgoCardDetail from './pages/YgoCardDetail'
import OnePiece from './pages/OnePiece'
import OnePieceCardDetail from './pages/OnePieceCardDetail'
import Watchlist from './pages/Watchlist'
import Portfolio from './pages/Portfolio'
import Settings from './pages/Settings'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isLoggedIn, isLoading } = useAuth()
  if (isLoading) return <div className="flex items-center justify-center h-screen text-muted">Loading…</div>
  if (!isLoggedIn) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route element={<Layout />}>
            <Route path="/markets" element={<Navigate to="/marketplace/pokemon" replace />} />
          <Route path="/marketplace" element={<Navigate to="/marketplace/pokemon" replace />} />
          <Route path="/marketplace/pokemon" element={<Marketplace game="pokemon" />} />
          <Route path="/marketplace/ygo" element={<Marketplace game="ygo" />} />
          <Route path="/marketplace/op" element={<Marketplace game="op" />} />
          <Route path="/marketplace/:id" element={<ListingDetail />} />
            <Route path="/sell/new" element={<RequireAuth><NewListing /></RequireAuth>} />
            <Route path="/seller/dashboard" element={<RequireAuth><SellerDashboard /></RequireAuth>} />
            <Route path="/orders" element={<RequireAuth><Orders /></RequireAuth>} />
            <Route path="/deals" element={<Deals />} />
            <Route path="/prices" element={<Prices />} />
            <Route path="/prices/card/:id" element={<CardDetail />} />
            <Route path="/ygo" element={<Ygo />} />
            <Route path="/ygo/card/:id" element={<YgoCardDetail />} />
            <Route path="/op" element={<OnePiece />} />
            <Route path="/op/card/:id" element={<OnePieceCardDetail />} />
            <Route path="/watchlist" element={<RequireAuth><Watchlist /></RequireAuth>} />
            <Route path="/portfolio" element={<RequireAuth><Portfolio /></RequireAuth>} />
            <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
