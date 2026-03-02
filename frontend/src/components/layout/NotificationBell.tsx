import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getNotifications, getUnseenCount, markAllSeen } from '../../api/notifications'
import { useNavigate } from 'react-router-dom'
import { Bell } from 'lucide-react'

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const qc = useQueryClient()
  const navigate = useNavigate()

  const { data: countData } = useQuery({
    queryKey: ['notif-count'],
    queryFn: getUnseenCount,
    refetchInterval: 30_000,
  })

  const { data: notifs } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => getNotifications({ limit: 20 }),
    enabled: open,
  })

  const markAll = useMutation({
    mutationFn: markAllSeen,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['notif-count'] })
      qc.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const count = countData?.count ?? 0

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-2 w-full text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
      >
        <Bell size={15} strokeWidth={1.75} className="flex-shrink-0" />
        Notifications
        {count > 0 && (
          <span className="ml-auto bg-accent text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
            {count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute bottom-full left-0 mb-2 w-72 bg-surface-2 border border-white/10 rounded-xl shadow-xl z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 border-b border-white/5">
            <span className="text-xs font-medium text-white">Notifications</span>
            {count > 0 && (
              <button onClick={() => markAll.mutate()} className="text-xs text-accent hover:underline">
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {!notifs || notifs.length === 0 ? (
              <p className="text-muted text-xs px-4 py-6 text-center">No notifications</p>
            ) : (
              notifs.map((n) => (
                <div
                  key={n.id}
                  onClick={() => { if (n.link) navigate(n.link); setOpen(false) }}
                  className={`px-4 py-3 border-b border-white/5 cursor-pointer hover:bg-white/5 transition-colors ${!n.seen ? 'bg-accent/5' : ''}`}
                >
                  <p className="text-xs font-medium text-white">{n.title}</p>
                  <p className="text-xs text-muted mt-0.5">{n.message}</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
