/**
 * PsaSlabFrame — accurate recreation of a real PSA grading slab.
 *
 * Real PSA anatomy (top → bottom):
 *  ┌────────────────────────────────────┐  ← clear acrylic outer (dark edges)
 *  │ ┌──────────────────────────────┐  │
 *  │ │ ██ RED BANNER  ██  #3       │  │  ← top label red stripe
 *  │ │ ████████████████████████████│  │
 *  │ │  |||||  CARD NAME  GEM MT   │  │  ← white label body: name, grade text
 *  │ │         Set Name   [PSA] 10 │  │  ← cert, PSA logo, large grade number
 *  │ └──────────────────────────────┘  │
 *  │ ┌──────────────────────────────┐  │
 *  │ │                              │  │
 *  │ │       [ card image ]         │  │  ← card in clear acrylic window
 *  │ │                              │  │
 *  │ └──────────────────────────────┘  │
 *  └────────────────────────────────────┘
 */

interface PsaSlabFrameProps {
  image: string | undefined
  alt: string
  grade: number
  size?: 'sm' | 'lg'
  className?: string
}

const GRADE_LABEL: Record<number, string> = {
  10: 'GEM MT',
  9: 'MINT',
  8: 'NM-MT',
  7: 'NM',
  6: 'EX-MT',
  5: 'EX',
}

const mockCert = (grade: number, alt: string) => {
  const hash = [...alt].reduce((a, c) => (a * 31 + c.charCodeAt(0)) | 0, grade * 7)
  return String(Math.abs(hash) % 90000000 + 10000000)
}

// Simple barcode SVG — alternating narrow/wide bars
function Barcode({ width, height }: { width: number; height: number }) {
  const bars = [2,1,2,1,1,2,1,1,2,1,2,1,1,2,1,2,1,1,2,1,2,2,1,1,2,1,2,1]
  const total = bars.reduce((a, b) => a + b, 0)
  let x = 0
  const rects: { x: number; w: number }[] = []
  bars.forEach((b, i) => {
    if (i % 2 === 0) rects.push({ x: (x / total) * width, w: (b / total) * width })
    x += b
  })
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {rects.map((r, i) => (
        <rect key={i} x={r.x} y={0} width={r.w} height={height} fill="#000" />
      ))}
    </svg>
  )
}

export default function PsaSlabFrame({ image, alt, grade, size = 'sm', className = '' }: PsaSlabFrameProps) {
  const isLg = size === 'lg'
  const gradeLabel = GRADE_LABEL[grade] ?? 'GRADE'
  const certNum = mockCert(grade, alt)

  // Size constants
  const outerPad    = isLg ? 6   : 3
  const innerRadius = isLg ? 4   : 2
  const labelH      = isLg ? 76  : 38
  const redBannerH  = isLg ? 20  : 10
  const logoSz      = isLg ? 11  : 5.5
  const nameSz      = isLg ? 9   : 4.5
  const gradeSz     = isLg ? 26  : 13
  const gradeTextSz = isLg ? 7   : 3.5
  const certSz      = isLg ? 5.5 : 2.75
  const barcodeW    = isLg ? 28  : 14
  const barcodeH    = isLg ? 16  : 8

  // Grade number colour: gold for 10/9, silver for rest
  const gradeColor = grade >= 9 ? '#C8A83A' : '#777777'
  const gradeShadow = grade >= 9
    ? '0 0 8px rgba(200,168,58,0.5), 0 1px 2px rgba(0,0,0,0.4)'
    : '0 1px 2px rgba(0,0,0,0.3)'

  return (
    <div
      className={`relative select-none ${className}`}
      style={{
        background: 'linear-gradient(160deg, #3a3a3a 0%, #1c1c1c 40%, #2a2a2a 100%)',
        borderRadius: isLg ? 8 : 4,
        padding: outerPad,
        boxShadow: [
          '0 16px 48px rgba(0,0,0,0.7)',
          '0 4px 12px rgba(0,0,0,0.5)',
          'inset 0 1px 0 rgba(255,255,255,0.12)',
          'inset 0 -1px 0 rgba(0,0,0,0.3)',
        ].join(', '),
      }}
    >
      {/* ── PSA Label (top) ── */}
      <div
        style={{
          borderRadius: innerRadius,
          overflow: 'hidden',
          marginBottom: isLg ? 5 : 2.5,
          boxShadow: '0 1px 4px rgba(0,0,0,0.5)',
          height: labelH,
        }}
      >
        {/* Red top banner */}
        <div
          style={{
            height: redBannerH,
            background: 'linear-gradient(180deg, #CC1111 0%, #AA0000 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: isLg ? '0 8px' : '0 4px',
          }}
        >
          <span style={{
            color: '#FFFFFF',
            fontSize: isLg ? 7 : 3.5,
            fontWeight: 700,
            letterSpacing: '0.08em',
            fontFamily: 'Arial, sans-serif',
            textTransform: 'uppercase',
          }}>
            {alt.toUpperCase().slice(0, isLg ? 28 : 22)}
          </span>
          <span style={{
            color: '#FFFFFF',
            fontSize: isLg ? 7 : 3.5,
            fontWeight: 700,
            fontFamily: 'Arial, sans-serif',
            letterSpacing: '0.05em',
          }}>
            #{certNum.slice(-4)}
          </span>
        </div>

        {/* White label body */}
        <div
          style={{
            flex: 1,
            height: labelH - redBannerH,
            background: 'linear-gradient(180deg, #FFFFFF 0%, #F4F2EE 100%)',
            display: 'flex',
            alignItems: 'stretch',
          }}
        >
          {/* Left: barcode + cert */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: isLg ? '4px 6px' : '2px 3px',
            gap: isLg ? 3 : 1.5,
            borderRight: '0.5px solid rgba(0,0,0,0.1)',
            minWidth: isLg ? 44 : 22,
          }}>
            <Barcode width={barcodeW} height={barcodeH} />
            <span style={{
              color: '#444',
              fontSize: certSz,
              fontFamily: '"Courier New", monospace',
              letterSpacing: '0.04em',
              lineHeight: 1,
            }}>
              {certNum}
            </span>
          </div>

          {/* Middle: card name + set line */}
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            padding: isLg ? '4px 8px' : '2px 4px',
            gap: isLg ? 3 : 1.5,
            overflow: 'hidden',
          }}>
            <span style={{
              color: '#111',
              fontSize: nameSz,
              fontWeight: 800,
              letterSpacing: '0.04em',
              fontFamily: '"Arial Black", Arial, sans-serif',
              lineHeight: 1,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              textTransform: 'uppercase',
            }}>
              {alt}
            </span>
            <span style={{
              color: '#555',
              fontSize: certSz,
              fontFamily: 'Arial, sans-serif',
              letterSpacing: '0.06em',
              lineHeight: 1,
              textTransform: 'uppercase',
            }}>
              {gradeLabel} {grade}
            </span>
            {/* PSA logo row */}
            <div style={{ display: 'flex', alignItems: 'center', gap: isLg ? 3 : 1.5 }}>
              <div style={{
                background: 'linear-gradient(180deg, #1E3A8A 0%, #142558 100%)',
                borderRadius: isLg ? 2 : 1,
                padding: isLg ? '1px 4px' : '0.5px 2px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: isLg ? 1 : 0.5,
              }}>
                <span style={{
                  color: '#FFF',
                  fontWeight: 900,
                  fontSize: logoSz,
                  fontFamily: '"Arial Black", Arial, sans-serif',
                  letterSpacing: '0.05em',
                  lineHeight: 1,
                }}>PSA</span>
              </div>
              <span style={{
                color: '#888',
                fontSize: certSz * 0.9,
                fontFamily: 'Arial, sans-serif',
                letterSpacing: '0.05em',
              }}>
                GRADED
              </span>
            </div>
          </div>

          {/* Right: large grade number */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: isLg ? '4px 10px' : '2px 5px',
            borderLeft: '0.5px solid rgba(0,0,0,0.1)',
            background: 'linear-gradient(180deg, #F8F8F6 0%, #EEECEA 100%)',
            minWidth: isLg ? 44 : 22,
          }}>
            <span style={{
              color: gradeColor,
              fontWeight: 900,
              fontSize: gradeSz,
              lineHeight: 1,
              fontFamily: '"Arial Black", Arial, sans-serif',
              textShadow: gradeShadow,
            }}>
              {grade}
            </span>
            <span style={{
              color: gradeColor,
              fontSize: gradeTextSz,
              fontWeight: 700,
              fontFamily: 'Arial, sans-serif',
              letterSpacing: '0.04em',
              lineHeight: 1,
              marginTop: isLg ? 2 : 1,
            }}>
              {gradeLabel}
            </span>
          </div>
        </div>
      </div>

      {/* ── Card in clear acrylic window (below label) ── */}
      <div
        style={{
          borderRadius: innerRadius,
          overflow: 'hidden',
          position: 'relative',
          background: 'linear-gradient(160deg, rgba(220,230,245,0.25) 0%, rgba(200,215,235,0.15) 100%)',
          boxShadow: [
            'inset 0 2px 6px rgba(0,0,0,0.35)',
            'inset 0 0 0 1px rgba(0,0,0,0.15)',
          ].join(', '),
        }}
      >
        {/* Acrylic glare highlight */}
        <div style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(135deg, rgba(255,255,255,0.18) 0%, rgba(200,220,255,0.06) 35%, transparent 65%)',
          pointerEvents: 'none',
          zIndex: 3,
          borderRadius: innerRadius,
        }} />

        {image ? (
          <img
            src={image}
            alt={alt}
            style={{
              display: 'block',
              width: '100%',
              aspectRatio: '3/4',
              objectFit: 'contain',
            }}
          />
        ) : (
          <div style={{ width: '100%', aspectRatio: '3/4', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg viewBox="0 0 60 84" fill="none" xmlns="http://www.w3.org/2000/svg"
              style={{ width: isLg ? 80 : 40, height: isLg ? 112 : 56, opacity: 0.3 }}>
              <rect width="60" height="84" rx="4" fill="#2a2a38"/>
              <rect x="6" y="6" width="48" height="48" rx="2" fill="#333344"/>
              <rect x="6" y="62" width="32" height="5" rx="2" fill="#3a3a4e"/>
              <rect x="6" y="71" width="20" height="4" rx="2" fill="#333344"/>
            </svg>
          </div>
        )}
      </div>
    </div>
  )
}
