import { useState, FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register } from '../api/auth'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const navigate = useNavigate()
  const { setTokens } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (password !== confirm) { setError('Passwords do not match'); return }
    if (password.length < 8) { setError('Password must be at least 8 characters'); return }
    setLoading(true)
    try {
      const data = await register(email, password)
      setTokens(data.access_token, data.refresh_token)
      navigate('/markets')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <span className="text-4xl">🔴</span>
          <h1 className="text-2xl font-bold text-white mt-2">Create Account</h1>
          <p className="text-muted text-sm mt-1">Get 100 Prediction Coins free on sign up</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-surface rounded-2xl p-6 border border-white/5 space-y-4">
          <div>
            <label className="text-xs text-muted block mb-1">Email</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-surface-2 text-white rounded-lg px-3 py-2 text-sm border border-white/10 focus:border-accent outline-none" />
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">Password</label>
            <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-surface-2 text-white rounded-lg px-3 py-2 text-sm border border-white/10 focus:border-accent outline-none" />
          </div>
          <div>
            <label className="text-xs text-muted block mb-1">Confirm Password</label>
            <input type="password" required value={confirm} onChange={(e) => setConfirm(e.target.value)}
              className="w-full bg-surface-2 text-white rounded-lg px-3 py-2 text-sm border border-white/10 focus:border-accent outline-none" />
          </div>

          {error && <p className="text-no text-xs">{error}</p>}

          <button type="submit" disabled={loading}
            className="w-full py-2.5 bg-accent hover:bg-accent-hover text-white font-medium rounded-lg transition-colors disabled:opacity-40">
            {loading ? 'Creating account…' : 'Create Account'}
          </button>

          <p className="text-center text-xs text-muted">
            Already have an account?{' '}
            <Link to="/login" className="text-accent hover:underline">Sign in</Link>
          </p>
        </form>
      </div>
    </div>
  )
}
