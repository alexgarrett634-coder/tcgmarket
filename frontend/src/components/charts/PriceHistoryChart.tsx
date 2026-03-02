import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import type { PricePoint } from '../../types'

interface Props {
  data: PricePoint[]
  color?: string
}

function fmt(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function PriceHistoryChart({ data, color = '#e3350d' }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        No price history available
      </div>
    )
  }

  const chartData = data.map((d) => ({
    date: fmt(d.recorded_at),
    price: d.price_usd,
  }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id={`grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
        <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#6b7280' }} tickLine={false} axisLine={false} />
        <YAxis
          tick={{ fontSize: 10, fill: '#6b7280' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `$${v.toFixed(2)}`}
          width={52}
        />
        <Tooltip
          contentStyle={{ background: '#1a1a24', border: '1px solid #ffffff10', borderRadius: 8 }}
          labelStyle={{ color: '#9ca3af', fontSize: 11 }}
          itemStyle={{ color: '#ffffff', fontSize: 12 }}
          formatter={(v: number) => [`$${v.toFixed(2)}`, 'Price']}
        />
        <Area
          type="monotone"
          dataKey="price"
          stroke={color}
          strokeWidth={2}
          fill={`url(#grad-${color.replace('#', '')})`}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
