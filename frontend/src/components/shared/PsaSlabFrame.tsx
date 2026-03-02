/**
 * PsaSlabFrame — faithful recreation of a real PSA grading slab.
 *
 * Correct PSA anatomy:
 *  - Outer case: near-invisible clear acrylic (subtle edge highlights only)
 *  - Inner card holder: white/cream plastic framing the card on all 4 sides
 *  - Card: sits inside the clear window, fully visible
 *  - Label (bottom ~22%): white/silver background, blue PSA logo left, grade right
 *
 *  ┌──────────────────────────────┐   ← clear acrylic edge (1-2px visible)
 *  │┌────────────────────────────┐│   ← white inner holder (thick white border)
 *  ││                            ││
 *  ││       card image           ││
 *  ││                            ││
 *  │└────────────────────────────┘│
 *  │┌────────────────────────────┐│   ← PSA label (white bg, blue logo, grade #)
 *  ││[PSA]  Card Name    Grade   ││
 *  ││       Set / Year    [10]   ││
 *  │└────────────────────────────┘│
 *  └──────────────────────────────┘
 */

interface PsaSlabFrameProps {
  image: string | undefined
  alt: string
  grade: number
  /** 'sm' for grid/list thumbnails, 'lg' for listing detail */
  size?: 'sm' | 'lg'
  className?: string
}

const GRADE_LABEL: Record<number, string> = {
  10: 'GEM MT 10',
  9:  'MINT 9',
  8:  'NM-MT 8',
  7:  'NM 7',
  6:  'EX-MT 6',
}

const GRADE_COLOR: Record<number, { text: string; glow: string }> = {
  10: { text: '#D4AF37', glow: '#D4AF3788' },  // Gold — PSA 10 uses gold numbering
  9:  { text: '#D4AF37', glow: '#D4AF3766' },
  8:  { text: '#888888', glow: '#88888866' },   // Silver — PSA 8 uses silver
  7:  { text: '#888888', glow: '#88888844' },
  6:  { text: '#888888', glow: '#88888844' },
}

// Mock cert number for realism
const mockCert = (grade: number, alt: string) => {
  const hash = [...alt].reduce((a, c) => (a * 31 + c.charCodeAt(0)) | 0, grade * 7)
  return String(Math.abs(hash) % 90000000 + 10000000)
}

export default function PsaSlabFrame({ image, alt, grade, size = 'sm', className = '' }: PsaSlabFrameProps) {
  const isLg = size === 'lg'
  const gradeLabel = GRADE_LABEL[grade] ?? `GRADE ${grade}`
  const { text: gradeText, glow: gradeGlow } = GRADE_COLOR[grade] ?? GRADE_COLOR[8]
  const certNum = mockCert(grade, alt)

  // Sizing constants
  const outerPad  = isLg ? 3  : 1.5   // clear acrylic edge (barely visible)
  const innerPad  = isLg ? 10 : 5     // white inner holder thickness
  const labelH    = isLg ? 60 : 30    // label strip height
  const logoSz    = isLg ? 18 : 9     // PSA logo text size
  const gradeNumSz= isLg ? 30 : 15   // large grade number
  const certSz    = isLg ? 6  : 3     // cert # text size
  const nameSz    = isLg ? 7  : 3.5   // card name in label

  return (
    <div
      className={`relative select-none ${className}`}
      style={{
        // Outer clear acrylic — almost invisible, just a very subtle tinted border
        background: 'linear-gradient(145deg, rgba(230,240,255,0.6) 0%, rgba(200,220,245,0.4) 50%, rgba(215,230,250,0.6) 100%)',
        borderRadius: isLg ? 6 : 3,
        padding: outerPad,
        boxShadow: [
          '0 12px 40px rgba(0,0,0,0.6)',
          '0 2px 8px rgba(0,0,0,0.4)',
          `inset 0 1px 0 rgba(255,255,255,0.8)`,
          `inset 0 -1px 0 rgba(0,0,0,0.12)`,
          `inset 1px 0 0 rgba(255,255,255,0.5)`,
          `inset -1px 0 0 rgba(0,0,0,0.08)`,
        ].join(', '),
      }}
    >
      {/* White inner card holder */}
      <div
        style={{
          background: 'linear-gradient(180deg, #F8F7F5 0%, #F2F0EC 40%, #EDE9E4 100%)',
          borderRadius: isLg ? 4 : 2,
          padding: innerPad,
          paddingBottom: 0,
          boxShadow: [
            `inset 0 ${isLg ? 2 : 1}px 0 rgba(255,255,255,0.9)`,
            `inset 0 -${isLg ? 2 : 1}px 0 rgba(0,0,0,0.08)`,
            `inset ${isLg ? 2 : 1}px 0 0 rgba(255,255,255,0.7)`,
            `inset -${isLg ? 2 : 1}px 0 0 rgba(0,0,0,0.06)`,
          ].join(', '),
        }}
      >
        {/* Card image area — clear acrylic window */}
        <div
          style={{
            position: 'relative',
            borderRadius: isLg ? 2 : 1,
            overflow: 'hidden',
            boxShadow: 'inset 0 1px 4px rgba(0,0,0,0.25), inset 0 0 0 1px rgba(0,0,0,0.08)',
            background: '#1a1a1a',
          }}
        >
          {/* Holographic acrylic sheen — top-left diagonal glare */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              background: 'linear-gradient(135deg, rgba(255,255,255,0.22) 0%, rgba(200,220,255,0.08) 30%, transparent 60%)',
              pointerEvents: 'none',
              zIndex: 3,
            }}
          />
          {/* Subtle rainbow iridescence at the edge of the window */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: isLg ? 3 : 1.5,
              background: 'linear-gradient(90deg, rgba(255,80,80,0.3) 0%, rgba(255,200,0,0.3) 20%, rgba(80,255,80,0.3) 40%, rgba(0,150,255,0.3) 60%, rgba(180,0,255,0.3) 80%, rgba(255,80,80,0.3) 100%)',
              pointerEvents: 'none',
              zIndex: 4,
            }}
          />

          {image ? (
            <img
              src={image}
              alt={alt}
              style={{ display: 'block', width: '100%', aspectRatio: '3/4', objectFit: 'contain' }}
            />
          ) : (
            <div style={{ width: '100%', aspectRatio: '3/4', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg viewBox="0 0 60 84" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ width: isLg ? 80 : 40, height: isLg ? 112 : 56, opacity: 0.35 }}>
                <rect width="60" height="84" rx="4" fill="#2a2a38"/>
                <rect x="6" y="6" width="48" height="48" rx="2" fill="#333344"/>
                <rect x="6" y="62" width="32" height="5" rx="2" fill="#3a3a4e"/>
                <rect x="6" y="71" width="20" height="4" rx="2" fill="#333344"/>
              </svg>
            </div>
          )}
        </div>

        {/* PSA Authentication Label */}
        <div
          style={{
            height: labelH,
            marginTop: isLg ? 4 : 2,
            background: 'linear-gradient(180deg, #FFFFFF 0%, #F5F5F0 60%, #ECEAE4 100%)',
            borderRadius: `0 0 ${isLg ? 3 : 1.5}px ${isLg ? 3 : 1.5}px`,
            display: 'flex',
            alignItems: 'stretch',
            overflow: 'hidden',
            border: `${isLg ? 0.5 : 0.25}px solid rgba(0,0,0,0.12)`,
            borderTop: `${isLg ? 1 : 0.5}px solid rgba(0,0,0,0.15)`,
          }}
        >
          {/* Left: PSA logo block */}
          <div
            style={{
              width: isLg ? 36 : 18,
              flexShrink: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              // PSA blue background — real PSA logo area
              background: 'linear-gradient(180deg, #1E3A8A 0%, #1A3070 50%, #142558 100%)',
              borderRight: `${isLg ? 1 : 0.5}px solid rgba(0,0,0,0.2)`,
              gap: isLg ? 1 : 0.5,
              padding: isLg ? 3 : 1.5,
            }}
          >
            <span
              style={{
                color: '#FFFFFF',
                fontWeight: 900,
                fontSize: logoSz,
                letterSpacing: '0.05em',
                fontFamily: '"Arial Black", Arial, sans-serif',
                lineHeight: 1,
              }}
            >
              PSA
            </span>
            {/* Small red accent line under PSA text */}
            <div style={{ width: '80%', height: isLg ? 1.5 : 0.75, background: '#DC2626', borderRadius: 1 }} />
          </div>

          {/* Middle: card name + cert number */}
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              padding: isLg ? '4px 6px' : '2px 3px',
              gap: isLg ? 2 : 1,
              overflow: 'hidden',
            }}
          >
            <span
              style={{
                color: '#111111',
                fontSize: nameSz,
                fontWeight: 700,
                letterSpacing: '0.03em',
                fontFamily: 'Arial, sans-serif',
                lineHeight: 1,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {alt.toUpperCase()}
            </span>
            <span
              style={{
                color: '#555555',
                fontSize: nameSz * 0.85,
                letterSpacing: '0.06em',
                fontFamily: 'Arial, sans-serif',
                lineHeight: 1,
              }}
            >
              {gradeLabel}
            </span>
            <span
              style={{
                color: '#999999',
                fontSize: certSz,
                letterSpacing: '0.05em',
                fontFamily: '"Courier New", monospace',
                lineHeight: 1,
              }}
            >
              #{certNum}
            </span>
          </div>

          {/* Right: large grade number */}
          <div
            style={{
              width: isLg ? 48 : 24,
              flexShrink: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'linear-gradient(180deg, rgba(240,240,235,1) 0%, rgba(225,222,215,1) 100%)',
              borderLeft: `${isLg ? 0.5 : 0.25}px solid rgba(0,0,0,0.1)`,
            }}
          >
            <span
              style={{
                color: gradeText,
                fontWeight: 900,
                fontSize: gradeNumSz,
                lineHeight: 1,
                fontFamily: '"Arial Black", Arial, sans-serif',
                textShadow: `0 0 ${isLg ? 10 : 5}px ${gradeGlow}, 0 1px 2px rgba(0,0,0,0.2)`,
              }}
            >
              {grade}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
