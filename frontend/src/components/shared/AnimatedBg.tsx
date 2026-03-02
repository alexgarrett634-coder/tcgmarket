import { useEffect, useRef } from 'react'

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  color: string
  alpha: number
  alphaDir: number
}

const COLORS = [
  'rgba(227,53,13,',   // accent red
  'rgba(34,197,94,',   // yes green
  'rgba(124,58,237,',  // purple
  'rgba(14,165,233,',  // sky blue
  'rgba(245,158,11,',  // gold
  'rgba(255,255,255,', // white
]

function makeParticle(w: number, h: number): Particle {
  const color = COLORS[Math.floor(Math.random() * COLORS.length)]
  return {
    x: Math.random() * w,
    y: Math.random() * h,
    vx: (Math.random() - 0.5) * 0.4,
    vy: (Math.random() - 0.5) * 0.4,
    radius: Math.random() * 1.8 + 0.5,
    color,
    alpha: Math.random() * 0.5 + 0.1,
    alphaDir: Math.random() > 0.5 ? 1 : -1,
  }
}

export default function AnimatedBg() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animId: number
    let particles: Particle[] = []

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
      // Rebuild particles on resize to fill new dimensions
      particles = Array.from({ length: 70 }, () => makeParticle(canvas.width, canvas.height))
    }

    resize()
    window.addEventListener('resize', resize)

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      for (const p of particles) {
        // Move
        p.x += p.vx
        p.y += p.vy

        // Wrap edges
        if (p.x < -5) p.x = canvas.width + 5
        if (p.x > canvas.width + 5) p.x = -5
        if (p.y < -5) p.y = canvas.height + 5
        if (p.y > canvas.height + 5) p.y = -5

        // Pulse alpha
        p.alpha += p.alphaDir * 0.003
        if (p.alpha > 0.65) { p.alpha = 0.65; p.alphaDir = -1 }
        if (p.alpha < 0.08) { p.alpha = 0.08; p.alphaDir = 1 }

        // Draw
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
        ctx.fillStyle = `${p.color}${p.alpha.toFixed(2)})`
        ctx.fill()
      }

      animId = requestAnimationFrame(draw)
    }

    draw()

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none">
      {/* CSS gradient orbs */}
      <div className="landing-orb-a" />
      <div className="landing-orb-b" />
      <div className="landing-orb-c" />
      {/* Canvas particle layer */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
    </div>
  )
}
