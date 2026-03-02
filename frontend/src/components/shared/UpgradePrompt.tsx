import { useNavigate } from 'react-router-dom'

interface Props {
  message?: string
  requiredTier?: string
}

export default function UpgradePrompt({ message, requiredTier = 'Pro' }: Props) {
  const navigate = useNavigate()
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <div className="text-5xl mb-4">🔒</div>
      <h2 className="text-xl font-bold text-white mb-2">{requiredTier} Feature</h2>
      <p className="text-muted text-sm mb-6 max-w-sm">
        {message || `This feature requires a ${requiredTier} subscription.`}
      </p>
      <button
        onClick={() => navigate('/billing')}
        className="px-6 py-2.5 bg-accent hover:bg-accent-hover text-white text-sm font-medium rounded-lg transition-colors"
      >
        Upgrade Now
      </button>
    </div>
  )
}
