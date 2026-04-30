import { Alert, Card, Col, Empty, Row, Table, Tag } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import type React from 'react'
import type { CSSProperties } from 'react'

interface TeacherAnalyticsPanelProps {
  data: any
}

const competencyColor = (score: number) => {
  if (score < 80) return '#fff1f0'
  if (score < 120) return '#fff7e6'
  if (score < 160) return '#f6ffed'
  return '#e6f4ff'
}

const competencyTextColor = (score: number) => {
  if (score < 80) return '#a8071a'
  if (score < 120) return '#ad6800'
  if (score < 160) return '#237804'
  return '#0958d9'
}

const TeacherAnalyticsPanel: React.FC<TeacherAnalyticsPanelProps> = ({ data }) => {
  if (!data || !data.scope || data.scope.essay_count === 0) {
    return (
      <Card>
        <Empty description="Ainda não há redações suficientes nos temas deste professor para gerar análise da turma." />
      </Card>
    )
  }

  return (
    <div style={styles.wrapper}>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <TeacherAlerts alerts={data.alerts || []} />
        </Col>
        <Col xs={24} lg={14}>
          <ProblemRanking ranking={data.ranking || []} />
        </Col>
      </Row>

      <CompetencyDistribution distribution={data.distribution || []} />
      <StudentHeatmap rows={data.heatmap || []} />

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <PedagogicalGroups groups={data.groups || []} />
        </Col>
        <Col xs={24} lg={14}>
          <ClassEvolution evolution={data.evolution || []} />
        </Col>
      </Row>

      <ThemePerformanceTable rows={data.theme_performance || []} />
    </div>
  )
}

const TeacherAlerts: React.FC<{ alerts: any[] }> = ({ alerts }) => (
  <Card title="Alertas pedagógicos" style={styles.card}>
    {alerts.length ? (
      <div style={styles.list}>
        {alerts.map((alert, index) => (
          <Alert
            key={`${alert.type}-${index}`}
            type={alert.severity === 'high' ? 'warning' : 'info'}
            showIcon
            message={alert.message}
            description={alert.action}
          />
        ))}
      </div>
    ) : (
      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Nenhum alerta no recorte atual" />
    )}
  </Card>
)

const ProblemRanking: React.FC<{ ranking: any[] }> = ({ ranking }) => (
  <Card title="Competências que mais precisam de intervenção" style={styles.card}>
    <div style={styles.ranking}>
      {ranking.slice(0, 3).map((item) => (
        <div key={item.competency} style={styles.rankingItem}>
          <div style={styles.rank}>{item.rank}</div>
          <div>
            <strong>{item.competency} - {item.title}</strong>
            <p style={styles.muted}>
              Média da turma: {Math.round(item.average)}/200 · {item.below_120_percent}% abaixo de 120
            </p>
          </div>
        </div>
      ))}
    </div>
  </Card>
)

const CompetencyDistribution: React.FC<{ distribution: any[] }> = ({ distribution }) => {
  return (
    <Card title="Distribuição da turma por competência" style={styles.card}>
      <div style={styles.boxplotList}>
        {distribution.map((item) => (
          <div key={item.competency} style={styles.boxplotRow}>
            <div style={styles.boxplotLabel}>
              <strong>{item.competency}</strong>
              <span>{item.title}</span>
            </div>
            <Boxplot item={item} />
            <div style={styles.boxplotStats}>
              <strong>média {Math.round(item.average)}</strong>
              <span>mediana {Math.round(item.median)}</span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  )
}

const Boxplot: React.FC<{ item: any }> = ({ item }) => {
  const width = 360
  const height = 42
  const x = (value: number) => Math.max(8, Math.min(width - 8, (Number(value || 0) / 200) * (width - 16) + 8))
  const y = height / 2
  const q1 = x(item.q1)
  const q3 = x(item.q3)
  const medianX = x(item.median)
  const lower = x(item.lower_whisker)
  const upper = x(item.upper_whisker)

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`Boxplot ${item.competency}`}>
      <line x1="8" y1={y} x2={width - 8} y2={y} stroke="#eef2f7" strokeWidth="6" strokeLinecap="round" />
      <line x1={lower} y1={y} x2={upper} y2={y} stroke="#1677ff" strokeWidth="2" />
      <line x1={lower} y1={y - 8} x2={lower} y2={y + 8} stroke="#1677ff" strokeWidth="2" />
      <line x1={upper} y1={y - 8} x2={upper} y2={y + 8} stroke="#1677ff" strokeWidth="2" />
      <rect x={q1} y={y - 12} width={Math.max(q3 - q1, 2)} height="24" rx="4" fill="#e6f4ff" stroke="#1677ff" />
      <line x1={medianX} y1={y - 14} x2={medianX} y2={y + 14} stroke="#0958d9" strokeWidth="3" />
      {(item.outliers || []).map((value: number, index: number) => (
        <circle key={`${value}-${index}`} cx={x(value)} cy={y} r="3" fill="#cf1322" />
      ))}
      <text x="8" y={height - 2} fontSize="10" fill="#6b7280">0</text>
      <text x={width - 8} y={height - 2} fontSize="10" textAnchor="end" fill="#6b7280">200</text>
    </svg>
  )
}

const StudentHeatmap: React.FC<{ rows: any[] }> = ({ rows }) => {
  const columns: ColumnsType<any> = [
    { title: 'Aluno', dataIndex: 'student', key: 'student', fixed: 'left' },
    ...['C1', 'C2', 'C3', 'C4', 'C5'].map((code) => ({
      title: code,
      dataIndex: ['scores', code],
      key: code,
      align: 'center' as const,
      render: (value: number) => (
        <span style={{
          ...styles.heatCell,
          background: competencyColor(value),
          color: competencyTextColor(value)
        }}>
          {Math.round(value)}
        </span>
      )
    })),
    {
      title: 'Total',
      dataIndex: 'total',
      key: 'total',
      align: 'center' as const,
      render: (value: number) => Math.round(value)
    },
    { title: 'Redações', dataIndex: 'essay_count', key: 'essay_count', align: 'center' as const }
  ]

  return (
    <Card title="Heatmap aluno x competência" style={styles.card}>
      <Table
        rowKey="student"
        dataSource={rows}
        columns={columns}
        pagination={{ pageSize: 8 }}
        scroll={{ x: true }}
      />
    </Card>
  )
}

const PedagogicalGroups: React.FC<{ groups: any[] }> = ({ groups }) => (
  <Card title="Grupos por necessidade pedagógica" style={styles.card}>
    {groups.length ? (
      <div style={styles.list}>
        {groups.map((group) => (
          <div key={group.competency} style={styles.group}>
            <strong>{group.competency} - {group.title}</strong>
            <p style={styles.muted}>{group.recommended_activity}</p>
            {group.profile && <p style={styles.profile}>{group.profile}</p>}
            <div style={styles.tags}>
              {group.students.map((student: string) => <Tag key={student}>{student}</Tag>)}
            </div>
          </div>
        ))}
      </div>
    ) : (
      <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sem grupos no recorte atual" />
    )}
  </Card>
)

const ClassEvolution: React.FC<{ evolution: any[] }> = ({ evolution }) => {
  if (!evolution.length) {
    return (
      <Card title="Evolução da turma ao longo das atividades" style={styles.card}>
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sem dados para evolução" />
      </Card>
    )
  }

  const width = 620
  const height = 220
  const left = 46
  const right = 20
  const top = 18
  const bottom = 42
  const plotWidth = width - left - right
  const plotHeight = height - top - bottom
  const xFor = (index: number) => evolution.length === 1 ? left + plotWidth / 2 : left + (index / (evolution.length - 1)) * plotWidth
  const yFor = (value: number) => top + plotHeight - (Math.max(0, Math.min(value, 1000)) / 1000) * plotHeight
  const points = evolution.map((item, index) => `${xFor(index)},${yFor(item.total_average)}`).join(' ')

  return (
    <Card title="Evolução da turma ao longo das atividades" style={styles.card}>
      <div style={{ overflowX: 'auto' }}>
        <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Evolução da turma">
          {[0, 250, 500, 750, 1000].map((tick) => {
            const y = yFor(tick)
            return (
              <g key={tick}>
                <line x1={left} y1={y} x2={width - right} y2={y} stroke="#eef2f7" />
                <text x={left - 10} y={y} textAnchor="end" dominantBaseline="middle" fontSize="11" fill="#6b7280">{tick}</text>
              </g>
            )
          })}
          <polyline points={points} fill="none" stroke="#1677ff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          {evolution.map((item, index) => (
            <g key={item.theme_id || index}>
              <circle cx={xFor(index)} cy={yFor(item.total_average)} r="4" fill="#1677ff" />
              <text x={xFor(index)} y={height - 18} textAnchor="middle" fontSize="11" fill="#6b7280">
                {item.group_by === 'week' ? item.label.slice(5) : `${index + 1}`}
              </text>
            </g>
          ))}
        </svg>
      </div>
    </Card>
  )
}

const ThemePerformanceTable: React.FC<{ rows: any[] }> = ({ rows }) => {
  const columns: ColumnsType<any> = [
    { title: 'Tema', dataIndex: 'theme', key: 'theme', ellipsis: true },
    { title: 'Média geral', dataIndex: 'total_average', key: 'total_average', align: 'center' as const, render: (value) => Math.round(value) },
    ...['C1', 'C2', 'C3', 'C4', 'C5'].map((code) => ({
      title: `${code} média`,
      dataIndex: code,
      key: code,
      align: 'center' as const,
      render: (value: number) => Math.round(value)
    })),
    { title: 'Envios', dataIndex: 'submission_count', key: 'submission_count', align: 'center' as const }
  ]

  return (
    <Card title="Comparação entre tema e desempenho" style={styles.card}>
      <Table
        rowKey="theme_id"
        dataSource={rows}
        columns={columns}
        pagination={{ pageSize: 6 }}
        scroll={{ x: true }}
      />
    </Card>
  )
}

const styles: Record<string, CSSProperties> = {
  wrapper: {
    display: 'grid',
    gap: 16
  },
  card: {
    borderRadius: 8,
    height: '100%'
  },
  list: {
    display: 'grid',
    gap: 10
  },
  ranking: {
    display: 'grid',
    gap: 12
  },
  rankingItem: {
    display: 'flex',
    gap: 12,
    alignItems: 'flex-start'
  },
  rank: {
    width: 32,
    height: 32,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: '#e6f4ff',
    color: '#0958d9',
    fontWeight: 800,
    flex: '0 0 auto'
  },
  muted: {
    margin: '4px 0 0',
    color: '#6b7280'
  },
  boxplotList: {
    display: 'grid',
    gap: 16
  },
  boxplotRow: {
    display: 'grid',
    gridTemplateColumns: '180px minmax(220px, 1fr) 130px',
    gap: 12,
    alignItems: 'center'
  },
  boxplotLabel: {
    display: 'grid',
    gap: 2,
    color: '#374151'
  },
  boxplotStats: {
    display: 'grid',
    textAlign: 'right',
    color: '#374151'
  },
  heatCell: {
    display: 'inline-flex',
    minWidth: 44,
    justifyContent: 'center',
    padding: '4px 8px',
    borderRadius: 6,
    fontWeight: 700
  },
  group: {
    border: '1px solid #eef2f7',
    borderRadius: 8,
    padding: 12,
    background: '#f9fafb'
  },
  profile: {
    margin: '4px 0 10px',
    color: '#4b5563',
    fontSize: 13
  },
  tags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 6
  }
}

export default TeacherAnalyticsPanel
