import { useState, FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../api/auth'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const navigate = useNavigate()
  const { setTokens } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await login(email, password)
      setTokens(data.access_token, data.refresh_token)
      navigate('/markets')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <img src="/logo.svg" className="w-12 h-12 mx-auto" alt="TCGMarket" />
          <h1 className="text-2xl font-bold text-white mt-2">TCGMarket</h1>
          <p className="text-muted text-sm mt-1">Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-surface rounded-2xl p-6 border border-white/5 space-y-4">
          <div>
            <label className="text-xs text-muted block mb-1">Email</label>
            <input
              type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-surface-2 text-white rounded-lg px-3 py-2 text-sm border border-white/10 focus:border-accent outline-none"
            />
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">Password</label>
            <input
              type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-surface-2 text-white rounded-lg px-3 py-2 text-sm border border-white/10 focus:border-accent outline-none"
            />
          </div>

          {error && <p className="text-no text-xs">{error}</p>}

          <button
            type="submit" disabled={loading}
            className="w-full py-2.5 bg-accent hover:bg-accent-hover text-white font-medium rounded-lg transition-colors disabled:opacity-40"
          >
            {loading ? 'Signing in…' : 'Sign In'}
          </button>

          <p className="text-center text-xs text-muted">
            No account?{' '}
            <Link to="/register" className="text-accent hover:underline">Register free</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
