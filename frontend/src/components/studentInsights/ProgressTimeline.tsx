import { getCompetencyScores } from '@/lib/competencias'
import type React from 'react'
import type { CSSProperties } from 'react'

interface ProgressTimelineProps {
  redacoes: any[]
}

const chartWidth = 760
const chartHeight = 260
const padding = { top: 20, right: 28, bottom: 48, left: 54 }
const plotWidth = chartWidth - padding.left - padding.right
const plotHeight = chartHeight - padding.top - padding.bottom

const getDateValue = (redacao: any) => {
  if (redacao.created_at) {
    const value = new Date(redacao.created_at).getTime()
    if (Number.isFinite(value)) return value
  }

  const objectId = `${redacao._id || ''}`
  if (/^[a-fA-F0-9]{24}$/.test(objectId)) {
    return parseInt(objectId.slice(0, 8), 16) * 1000
  }

  return 0
}

const formatDate = (value: number) => {
  if (!value) return 'Sem data'
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: '2-digit' }).format(new Date(value))
}

const xFor = (index: number, total: number) => {
  if (total <= 1) return padding.left + plotWidth / 2
  return padding.left + (index / (total - 1)) * plotWidth
}

const yFor = (score: number) => padding.top + plotHeight - (Math.max(0, Math.min(score, 1000)) / 1000) * plotHeight
const ProgressTimeline: React.FC<ProgressTimelineProps> = ({ redacoes }) => {
  const ordered = [...redacoes].sort((a, b) => getDateValue(a) - getDateValue(b))

  if (ordered.length < 2) {
    return (
      <section style={styles.card}>
        <h3 style={styles.title}>Linha do tempo de progresso</h3>
        <p style={styles.empty}>Envie ao menos duas redações para visualizar evolução.</p>
      </section>
    )
  }

  const totalPoints = ordered.map((redacao, index) => ({
    x: xFor(index, ordered.length),
    y: yFor(Number(redacao.nota_total) || 0)
  }))
  const totalPolyline = totalPoints.map((point) => `${point.x},${point.y}`).join(' ')
  const latest = ordered[ordered.length - 1]
  const previous = ordered[ordered.length - 2]
  const totalDelta = (Number(latest.nota_total) || 0) - (Number(previous.nota_total) || 0)

  return (
    <section style={styles.card}>
      <div style={styles.header}>
        <div>
          <h3 style={styles.title}>Linha do tempo de progresso</h3>
          <p style={styles.subtitle}>Evolução da nota total e leitura das competências da redação mais recente.</p>
        </div>
        <strong style={{ ...styles.delta, color: totalDelta >= 0 ? '#237804' : '#a8071a' }}>
          {totalDelta >= 0 ? '+' : ''}{Math.round(totalDelta)} desde a última
        </strong>
      </div>
      <div style={styles.scroll}>
        <svg width={chartWidth} height={chartHeight} viewBox={`0 0 ${chartWidth} ${chartHeight}`} role="img" aria-label="Linha do tempo de progresso">
          {[0, 250, 500, 750, 1000].map((tick) => {
            const y = yFor(tick)
            return (
              <g key={tick}>
                <line x1={padding.left} y1={y} x2={chartWidth - padding.right} y2={y} stroke="#eef2f7" />
                <text x={padding.left - 12} y={y} textAnchor="end" dominantBaseline="middle" fontSize="12" fill="#6b7280">{tick}</text>
              </g>
            )
          })}
          <polyline points={totalPolyline} fill="none" stroke="#1677ff" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
          {ordered.map((redacao, index) => {
            const x = xFor(index, ordered.length)
            const y = yFor(Number(redacao.nota_total) || 0)
            const date = getDateValue(redacao)
            return (
              <g key={redacao._id || index}>
                <circle cx={x} cy={y} r="4" fill="#1677ff" />
                <text x={x} y={chartHeight - 18} textAnchor="middle" fontSize="12" fill="#6b7280">{formatDate(date)}</text>
              </g>
            )
          })}
        </svg>
      </div>
      <div style={styles.competencyBars}>
        {getCompetencyScores(latest).map((item) => {
          const previousScore = getCompetencyScores(previous).find((competency) => competency.code === item.code)?.score || 0
          const delta = item.score - previousScore
          return (
            <div key={item.code} style={styles.barRow}>
              <span style={styles.barLabel}>{item.code}</span>
              <div style={styles.barTrack}>
                <div style={{ ...styles.barFill, width: `${Math.max(0, Math.min(item.score, 200)) / 2}%` }} />
              </div>
              <span style={styles.barScore}>{Math.round(item.score)}</span>
              <span style={{ ...styles.barDelta, color: delta >= 0 ? '#237804' : '#a8071a' }}>
                {delta >= 0 ? '+' : ''}{Math.round(delta)}
              </span>
            </div>
          )
        })}
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
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: 16,
    alignItems: 'flex-start',
    flexWrap: 'wrap'
  },
  title: {
    margin: 0,
    fontSize: 18
  },
  subtitle: {
    margin: '4px 0 0',
    color: '#6b7280'
  },
  empty: {
    margin: '8px 0 0',
    color: '#6b7280'
  },
  delta: {
    background: '#f6ffed',
    border: '1px solid #b7eb8f',
    borderRadius: 6,
    padding: '6px 10px'
  },
  scroll: {
    overflowX: 'auto'
  },
  competencyBars: {
    display: 'grid',
    gap: 8,
    marginTop: 8
  },
  barRow: {
    display: 'grid',
    gridTemplateColumns: '34px 1fr 42px 44px',
    gap: 8,
    alignItems: 'center'
  },
  barLabel: {
    fontWeight: 700,
    color: '#1677ff'
  },
  barTrack: {
    height: 8,
    background: '#eef2f7',
    borderRadius: 999
  },
  barFill: {
    height: '100%',
    background: '#69b1ff',
    borderRadius: 999
  },
  barScore: {
    textAlign: 'right',
    color: '#374151'
  },
  barDelta: {
    textAlign: 'right',
    fontWeight: 700
  }
}

export default ProgressTimeline
