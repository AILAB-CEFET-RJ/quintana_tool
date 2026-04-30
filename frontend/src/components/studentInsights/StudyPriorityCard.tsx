import { getCompetencyScores } from '@/lib/competencias'
import type React from 'react'
import type { CSSProperties } from 'react'

interface StudyPriorityCardProps {
  redacao: any
}

const StudyPriorityCard: React.FC<StudyPriorityCardProps> = ({ redacao }) => {
  const priorities = getCompetencyScores(redacao)
    .sort((a, b) => a.score - b.score)
    .slice(0, 3)

  return (
    <section style={styles.card}>
      <h3 style={styles.title}>Prioridade de estudo</h3>
      <div style={styles.list}>
        {priorities.map((item, index) => (
          <div key={item.code} style={styles.item}>
            <div style={styles.rank}>P{index + 1}</div>
            <div style={styles.body}>
              <strong>{item.code} - {item.shortTitle}</strong>
              <span style={styles.meta}>Nota atual: {Math.round(item.score)}/200</span>
              <p style={styles.action}>{item.defaultAction}</p>
            </div>
          </div>
        ))}
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
    margin: '0 0 12px',
    fontSize: 18
  },
  list: {
    display: 'grid',
    gap: 10
  },
  item: {
    display: 'flex',
    gap: 12,
    padding: 12,
    border: '1px solid #eef2f7',
    borderRadius: 8,
    background: '#f9fafb'
  },
  rank: {
    width: 38,
    height: 32,
    borderRadius: 6,
    background: '#e6f4ff',
    color: '#0958d9',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 700,
    flex: '0 0 auto'
  },
  body: {
    display: 'grid',
    gap: 3
  },
  meta: {
    color: '#6b7280',
    fontSize: 13
  },
  action: {
    margin: 0,
    color: '#374151'
  }
}

export default StudyPriorityCard
