import { useAuth } from '../context/AuthContext'

export default function Settings() {
  const { user } = useAuth()

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-white">Settings</h1>

      <div className="bg-surface rounded-xl border border-white/5 p-5 space-y-4">
        <h2 className="text-sm font-semibold text-white">Account</h2>
        <div className="text-sm">
          <div className="text-xs text-muted mb-1">Email</div>
          <div className="text-white">{user?.email}</div>
        </div>
      </div>
    </div>
  )
}
