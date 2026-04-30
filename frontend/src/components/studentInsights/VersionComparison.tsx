import { Card, Col, Empty, Row, Tag } from 'antd'
import { getCompetencyScores } from '@/lib/competencias'
import type React from 'react'
import type { CSSProperties } from 'react'

interface VersionComparisonProps {
  versions: any[]
}

const VersionComparison: React.FC<VersionComparisonProps> = ({ versions }) => {
  const ordered = [...versions].sort((a, b) => Number(a.version_number || 1) - Number(b.version_number || 1))

  if (ordered.length < 2) {
    return <Empty description="Ainda não há reescritas para comparar" />
  }

  const first = ordered[0]
  const latest = ordered[ordered.length - 1]
  const previous = ordered[ordered.length - 2]
  const totalDelta = (Number(latest.nota_total) || 0) - (Number(first.nota_total) || 0)
  const competencyDeltas = getCompetencyScores(latest)
    .map((item) => {
      const previousScore = getCompetencyScores(previous).find((competency) => competency.code === item.code)?.score || 0
      return { ...item, delta: item.score - previousScore }
    })
    .filter((item) => item.delta !== 0)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))

  return (
    <div style={styles.wrapper}>
      <Row gutter={[12, 12]}>
        {ordered.map((version) => (
          <Col xs={24} md={12} key={version._id}>
            <Card size="small" title={`Versão ${version.version_number || 1}`} style={{ height: '100%' }}>
              <strong style={styles.score}>{Math.round(Number(version.nota_total) || 0)} pontos</strong>
              <p style={styles.meta}>{version.titulo?.trim() || 'Sem título'}</p>
            </Card>
          </Col>
        ))}
      </Row>
      <Card size="small" title="Melhorias mais recentes" style={{ marginTop: 12 }}>
        <p style={styles.summary}>
          Evolução desde a primeira versão: <strong>{totalDelta >= 0 ? '+' : ''}{Math.round(totalDelta)} pontos</strong>
        </p>
        <div style={styles.tags}>
          {competencyDeltas.length ? competencyDeltas.map((item) => (
            <Tag key={item.code} color={item.delta > 0 ? 'green' : 'red'}>
              {item.delta > 0 ? '+' : ''}{Math.round(item.delta)} em {item.code}
            </Tag>
          )) : <span style={styles.meta}>Sem alteração entre as duas últimas versões.</span>}
        </div>
      </Card>
    </div>
  )
}

const styles: Record<string, CSSProperties> = {
  wrapper: {
    display: 'grid',
    gap: 12
  },
  score: {
    display: 'block',
    fontSize: 24,
    color: '#111827'
  },
  meta: {
    margin: '6px 0 0',
    color: '#6b7280'
  },
  summary: {
    margin: '0 0 10px',
    color: '#374151'
  },
  tags: {
    display: 'flex',
    gap: 8,
    flexWrap: 'wrap'
  }
}

export default VersionComparison
