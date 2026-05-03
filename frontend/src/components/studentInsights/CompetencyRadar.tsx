import { getCompetencyScores } from '@/lib/competencias'
import type React from 'react'
import type { CSSProperties } from 'react'

interface CompetencyRadarProps {
  redacao: any
  title?: string
  subtitle?: string
}

const size = 280
const center = size / 2
const maxRadius = 92

const pointFor = (index: number, value: number) => {
  const angle = -Math.PI / 2 + (index * 2 * Math.PI) / 5
  const radius = (Math.max(0, Math.min(value, 200)) / 200) * maxRadius
  return {
    x: center + radius * Math.cos(angle),
    y: center + radius * Math.sin(angle)
  }
}

const guidePointFor = (index: number, radius: number) => {
  const angle = -Math.PI / 2 + (index * 2 * Math.PI) / 5
  return {
    x: center + radius * Math.cos(angle),
    y: center + radius * Math.sin(angle)
  }
}

const CompetencyRadar: React.FC<CompetencyRadarProps> = ({
  redacao,
  title = 'Radar das competências',
  subtitle = 'Comparação rápida das cinco habilidades avaliadas.'
}) => {
  const scores = getCompetencyScores(redacao)
  const polygon = scores.map((item, index) => pointFor(index, item.score)).map((point) => `${point.x},${point.y}`).join(' ')

  return (
    <section style={styles.card}>
      <div>
        <h3 style={styles.title}>{title}</h3>
        <p style={styles.subtitle}>{subtitle}</p>
      </div>
      <div style={styles.content}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Radar das cinco competências">
          {[40, 80, 120, 160, 200].map((value) => {
            const radius = (value / 200) * maxRadius
            const points = scores.map((_, index) => guidePointFor(index, radius)).map((point) => `${point.x},${point.y}`).join(' ')
            return <polygon key={value} points={points} fill="none" stroke="#e5e7eb" strokeWidth="1" />
          })}
          {scores.map((_, index) => {
            const end = guidePointFor(index, maxRadius)
            return <line key={index} x1={center} y1={center} x2={end.x} y2={end.y} stroke="#e5e7eb" />
          })}
          <polygon points={polygon} fill="rgba(22, 119, 255, 0.18)" stroke="#1677ff" strokeWidth="2" />
          {scores.map((item, index) => {
            const point = pointFor(index, item.score)
            const label = guidePointFor(index, maxRadius + 26)
            return (
              <g key={item.code}>
                <circle cx={point.x} cy={point.y} r="4" fill="#1677ff" />
                <text x={label.x} y={label.y} textAnchor="middle" dominantBaseline="middle" fontSize="12" fill="#374151">
                  {item.code}
                </text>
              </g>
            )
          })}
        </svg>
        <div style={styles.legend}>
          {scores.map((item) => (
            <div key={item.code} style={styles.legendItem}>
              <span style={styles.code}>{item.code}</span>
              <span style={styles.label}>{item.shortTitle}</span>
              <strong style={styles.score}>{Math.round(item.score)}</strong>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

const styles: Record<string, CSSProperties> = {
  card: {
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    background: '#ffffff'
  },
  title: {
    margin: 0,
    fontSize: 18
  },
  subtitle: {
    margin: '4px 0 0',
    color: '#6b7280'
  },
  content: {
    display: 'flex',
    alignItems: 'center',
    gap: 24,
    flexWrap: 'wrap'
  },
  legend: {
    flex: 1,
    minWidth: 240
  },
  legendItem: {
    display: 'grid',
    gridTemplateColumns: '44px 1fr 52px',
    gap: 8,
    alignItems: 'center',
    padding: '8px 0',
    borderBottom: '1px solid #f3f4f6'
  },
  code: {
    fontWeight: 700,
    color: '#1677ff'
  },
  label: {
    color: '#374151'
  },
  score: {
    textAlign: 'right'
  }
}

export default CompetencyRadar
