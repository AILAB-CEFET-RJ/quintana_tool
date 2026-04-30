import { Card, Col, Empty, Row, Tag } from 'antd'
import { getCompetencyScores } from '@/lib/competencias'
import type React from 'react'
import type { CSSProperties } from 'react'

interface CompetencyFeedbackMapProps {
  redacao: any
}

const fallbackFeedback = (redacao: any) =>
  getCompetencyScores(redacao).map((item) => ({
    code: item.code,
    title: item.shortTitle,
    score: item.score,
    diagnosis: item.score < 120 ? 'Esta competência deve ser priorizada na próxima reescrita.' : 'Esta competência tem desempenho intermediário ou bom.',
    suggestion: item.defaultAction,
    practice_action: item.defaultAction
  }))

const CompetencyFeedbackMap: React.FC<CompetencyFeedbackMapProps> = ({ redacao }) => {
  const competencies = redacao?.feedback_structured?.competencies || fallbackFeedback(redacao)

  if (!competencies.length) {
    return <Empty description="Feedback por competência indisponível" />
  }

  return (
    <Row gutter={[12, 12]}>
      {competencies.map((item: any) => (
        <Col xs={24} md={12} key={item.code}>
          <Card
            size="small"
            title={`${item.code} - ${item.title}`}
            extra={<Tag color={item.score < 120 ? 'red' : item.score < 160 ? 'gold' : 'green'}>{Math.round(Number(item.score) || 0)}/200</Tag>}
            style={{ height: '100%' }}
          >
            <p style={styles.label}>Diagnóstico</p>
            <p style={styles.text}>{item.diagnosis}</p>
            <p style={styles.label}>Próxima ação</p>
            <p style={styles.text}>{item.suggestion}</p>
            <p style={styles.label}>Ação prática</p>
            <p style={styles.text}>{item.practice_action}</p>
          </Card>
        </Col>
      ))}
    </Row>
  )
}

const styles: Record<string, CSSProperties> = {
  label: {
    margin: '0 0 3px',
    color: '#6b7280',
    fontSize: 12,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: 0
  },
  text: {
    margin: '0 0 12px',
    color: '#374151'
  }
}

export default CompetencyFeedbackMap
