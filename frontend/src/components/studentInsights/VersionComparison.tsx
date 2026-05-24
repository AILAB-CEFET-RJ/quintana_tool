import { Card, Col, Empty, Row, Select, Tag } from 'antd'
import { getCompetencyScores } from '@/lib/competencias'
import React, { useState } from 'react'
import type { CSSProperties } from 'react'

interface VersionComparisonProps {
  versions: any[]
}

interface DiffToken {
  value: string
  type: 'same' | 'added' | 'removed'
}

const tokenize = (text: string) => {
  const normalized = String(text || '').replace(/\s+/g, ' ').trim()
  return normalized.match(/[\p{L}\p{N}]+|[^\s\p{L}\p{N}]/gu) || []
}

const buildTextDiff = (beforeText: string, afterText: string): DiffToken[] => {
  const before = tokenize(beforeText)
  const after = tokenize(afterText)
  const rows = before.length + 1
  const cols = after.length + 1
  const dp = Array.from({ length: rows }, () => Array(cols).fill(0))

  for (let i = before.length - 1; i >= 0; i -= 1) {
    for (let j = after.length - 1; j >= 0; j -= 1) {
      if (before[i].toLowerCase() === after[j].toLowerCase()) {
        dp[i][j] = dp[i + 1][j + 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1])
      }
    }
  }

  const result: DiffToken[] = []
  let i = 0
  let j = 0

  while (i < before.length && j < after.length) {
    if (before[i].toLowerCase() === after[j].toLowerCase()) {
      result.push({ value: after[j], type: 'same' })
      i += 1
      j += 1
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      result.push({ value: before[i], type: 'removed' })
      i += 1
    } else {
      result.push({ value: after[j], type: 'added' })
      j += 1
    }
  }

  while (i < before.length) {
    result.push({ value: before[i], type: 'removed' })
    i += 1
  }
  while (j < after.length) {
    result.push({ value: after[j], type: 'added' })
    j += 1
  }

  return result
}

const diffStats = (tokens: DiffToken[]) => ({
  added: tokens.filter((item) => item.type === 'added').length,
  removed: tokens.filter((item) => item.type === 'removed').length,
})

const VersionComparison: React.FC<VersionComparisonProps> = ({ versions }) => {
  const ordered = [...versions].sort((a, b) => Number(a.version_number || 1) - Number(b.version_number || 1))
  const [pairIndex, setPairIndex] = useState(Math.max(0, ordered.length - 2))

  const selectedPairIndex = Math.min(pairIndex, Math.max(0, ordered.length - 2))

  if (ordered.length < 2) {
    return <Empty description="Ainda não há reescritas para comparar" />
  }

  const first = ordered[0]
  const previous = ordered[selectedPairIndex]
  const next = ordered[selectedPairIndex + 1]
  const latest = ordered[ordered.length - 1]
  const totalDeltaFromFirst = (Number(latest.nota_total) || 0) - (Number(first.nota_total) || 0)
  const pairTotalDelta = (Number(next.nota_total) || 0) - (Number(previous.nota_total) || 0)
  const textDiff = buildTextDiff(previous.texto || '', next.texto || '')
  const stats = diffStats(textDiff)
  const competencyDeltas = getCompetencyScores(next)
    .map((item) => {
      const previousScore = getCompetencyScores(previous).find((competency) => competency.code === item.code)?.score || 0
      return { ...item, delta: item.score - previousScore }
    })
    .filter((item) => item.delta !== 0)
    .sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta))

  return (
    <div style={styles.wrapper}>
      <Card size="small">
        <div style={styles.toolbar}>
          <div>
            <strong>Comparar versões</strong>
            <p style={styles.meta}>Veja o que mudou no texto e como isso se refletiu nas competências.</p>
          </div>
          <Select
            value={selectedPairIndex}
            style={{ minWidth: 220 }}
            onChange={setPairIndex}
            options={ordered.slice(0, -1).map((version, index) => ({
              value: index,
              label: `Versão ${version.version_number || index + 1} → Versão ${ordered[index + 1].version_number || index + 2}`
            }))}
          />
        </div>
      </Card>

      <Row gutter={[12, 12]}>
        {[previous, next].map((version) => (
          <Col xs={24} md={12} key={version._id}>
            <Card size="small" title={`Versão ${version.version_number || 1}`} style={{ height: '100%' }}>
              <strong style={styles.score}>{Math.round(Number(version.nota_total) || 0)} pontos</strong>
              <p style={styles.meta}>{version.titulo?.trim() || 'Sem título'}</p>
            </Card>
          </Col>
        ))}
      </Row>

      <Card size="small" title="Resumo da evolução">
        <p style={styles.summary}>
          Evolução entre as versões selecionadas: <strong>{pairTotalDelta >= 0 ? '+' : ''}{Math.round(pairTotalDelta)} pontos</strong>
        </p>
        <p style={styles.summary}>
          Evolução desde a primeira versão até a mais recente: <strong>{totalDeltaFromFirst >= 0 ? '+' : ''}{Math.round(totalDeltaFromFirst)} pontos</strong>
        </p>
        <p style={styles.meta}>
          Texto: {stats.added} termos adicionados e {stats.removed} termos removidos.
        </p>
        <div style={styles.tags}>
          {competencyDeltas.length ? competencyDeltas.map((item) => (
            <Tag key={item.code} color={item.delta > 0 ? 'green' : 'red'}>
              {item.delta > 0 ? '+' : ''}{Math.round(item.delta)} em {item.code}
            </Tag>
          )) : <span style={styles.meta}>Sem alteração entre as duas últimas versões.</span>}
        </div>
      </Card>

      <Card size="small" title="Comparação textual">
        <div style={styles.legend}>
          <Tag color="green">Adicionado</Tag>
          <Tag color="red">Removido</Tag>
          <span style={styles.meta}>Trechos sem destaque foram preservados ou mantêm o mesmo sentido lexical.</span>
        </div>
        <div style={styles.diffBox}>
          {textDiff.map((token, index) => {
            const style = token.type === 'added'
              ? styles.added
              : token.type === 'removed'
                ? styles.removed
                : styles.same

            return (
              <React.Fragment key={`${token.value}-${index}`}>
                <span style={style}>{token.value}</span>{' '}
              </React.Fragment>
            )
          })}
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
  toolbar: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
    flexWrap: 'wrap'
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
  },
  legend: {
    display: 'flex',
    gap: 8,
    alignItems: 'center',
    flexWrap: 'wrap',
    marginBottom: 12
  },
  diffBox: {
    maxHeight: 420,
    overflowY: 'auto',
    padding: 16,
    border: '1px solid #eef2f7',
    borderRadius: 8,
    background: '#ffffff',
    color: '#374151',
    lineHeight: 1.9,
    fontSize: 15
  },
  same: {
    color: '#374151'
  },
  added: {
    color: '#237804',
    background: '#f6ffed',
    borderBottom: '1px solid #b7eb8f',
    padding: '1px 2px',
    borderRadius: 3
  },
  removed: {
    color: '#a8071a',
    background: '#fff1f0',
    textDecoration: 'line-through',
    padding: '1px 2px',
    borderRadius: 3
  }
}

export default VersionComparison
