import axios from 'axios'
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react'
import { Modal, Collapse, Button, Space, Alert, Card, Statistic, message, Result, Input } from 'antd'
import { ClearOutlined, CheckOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import TextArea from 'antd/lib/input/TextArea'
import { useAuth } from '../../context';
import { API_URL } from "@/config/config";
import { authFetch, authHeaders } from '@/lib/authFetch'
import PageShell from '@/components/ui/PageShell'
import PageHeader from '@/components/ui/PageHeader'
import SectionPanel from '@/components/ui/SectionPanel'
import type { CSSProperties } from 'react'
import { COMPETENCIES } from '@/lib/competencias'

const BACKEND_GRADE_KEYS = [
  'Domínio da modalidade escrita formal',
  'Compreender a proposta e aplicar conceitos das várias áreas de conhecimento para desenvolver o texto dissertativo-argumentativo em prosa',
  'Selecionar, relacionar, organizar e interpretar informações em defesa de um ponto de vista',
  'Conhecimento dos mecanismos linguísticos necessários para a construção da argumentação',
  'Proposta de intervenção com respeito aos direitos humanos'
]

const MIN_WRITTEN_LINES = 7
const MIN_WORDS = 30
const MIN_ALPHA_CHARS = 100
const MIN_UNIQUE_WORDS = 12
const MAX_REPEATED_WORD_RATIO = 0.55
const APPROX_CHARS_PER_LINE = 55

const getEssayMetrics = (text: string) => {
  const trimmed = text.trim()
  const nonEmptyLines = trimmed ? trimmed.split(/\r?\n/).filter((line) => line.trim()).length : 0
  const words = trimmed.match(/\b[\wÀ-ÿ]+\b/gu)?.map((word) => word.toLocaleLowerCase('pt-BR')) || []
  const alphaChars = trimmed.match(/[A-Za-zÀ-ÿ]/gu)?.length || 0
  const estimatedWrittenLines = Math.max(nonEmptyLines, Math.floor(alphaChars / APPROX_CHARS_PER_LINE))
  const uniqueWords = new Set(words).size
  const wordFrequency = words.reduce<Record<string, number>>((acc, word) => {
    acc[word] = (acc[word] || 0) + 1
    return acc
  }, {})
  const mostCommonWordCount = Object.values(wordFrequency).reduce((max, value) => Math.max(max, value), 0)
  const repeatedWordRatio = words.length ? mostCommonWordCount / words.length : 0

  return {
    nonEmptyLines,
    estimatedWrittenLines,
    words: words.length,
    alphaChars,
    uniqueWords,
    repeatedWordRatio
  }
}

const getEssayReadiness = (text: string) => {
  const metrics = getEssayMetrics(text)
  const criteria = [
    {
      key: 'lines',
      label: 'Mínimo de 7 linhas escritas',
      value: `${Math.min(metrics.estimatedWrittenLines, MIN_WRITTEN_LINES)}/${MIN_WRITTEN_LINES}`,
      passed: metrics.estimatedWrittenLines >= MIN_WRITTEN_LINES
    },
    {
      key: 'words',
      label: 'Texto com pelo menos 30 palavras',
      value: `${Math.min(metrics.words, MIN_WORDS)}/${MIN_WORDS}`,
      passed: metrics.words >= MIN_WORDS
    },
    {
      key: 'alpha',
      label: 'Conteúdo textual suficiente',
      value: `${Math.min(metrics.alphaChars, MIN_ALPHA_CHARS)}/${MIN_ALPHA_CHARS}`,
      passed: metrics.alphaChars >= MIN_ALPHA_CHARS
    },
    {
      key: 'diversity',
      label: 'Diversidade mínima de palavras',
      value: `${Math.min(metrics.uniqueWords, MIN_UNIQUE_WORDS)}/${MIN_UNIQUE_WORDS}`,
      passed: metrics.uniqueWords >= MIN_UNIQUE_WORDS && metrics.repeatedWordRatio <= MAX_REPEATED_WORD_RATIO
    }
  ]

  return {
    metrics,
    criteria,
    isReady: criteria.every((criterion) => criterion.passed)
  }
}

const extractSubmittedGrades = (result: any) => {
  if (!result) return []

  if (Array.isArray(result.competency_scores)) {
    return COMPETENCIES.map((competency) => {
      const item = result.competency_scores.find((score: any) => score?.code === competency.code)
      return Number(item?.score) || 0
    })
  }

  if (result.grades_by_code) {
    return COMPETENCIES.map((competency) => Number(result.grades_by_code[competency.code]) || 0)
  }

  if (result.grades) {
    return BACKEND_GRADE_KEYS.map((key) => Number(result.grades[key]) || 0)
  }

  return []
}


const Redacao = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [essayTitle, setEssayTitle] = useState('')
  const [essay, setEssay] = useState('')
  const [submissionResult, setSubmissionResult] = useState<any | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [hasSubmitted, setHasSubmitted] = useState(false)
  const router = useRouter();
  const { id, rewriteOf, classId, activityId } = router.query;
  const { nomeUsuario } = useAuth();
  const { Panel } = Collapse;

  const showModalText = async () => {
    if (hasSubmitted) {
      setIsModalOpen(true)
      return
    }

    if (!essay.trim()) {
      message.warning('Escreva a redação antes de enviar.')
      return
    }

    const readiness = getEssayReadiness(essay)
    if (!readiness.isReady) {
      message.warning('A redação ainda não atende aos critérios mínimos para avaliação.')
      return
    }

    try {
      setIsSubmitting(true)
      const result = await submitEssay()
      setSubmissionResult(result)
      setHasSubmitted(true)
      message.success('Redação enviada com sucesso.')
      setIsModalOpen(true)
    } catch (error) {
      console.error('Erro ao enviar redação:', error)
      message.error('Não foi possível enviar a redação.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleOk = () => {
    setIsModalOpen(false)
  }

  const handleCancel = () => {
    setIsModalOpen(false)
  }

  const handleChange = (event: any) => {
    setEssay(event.target.value)
  }


  const submitEssay = async () => {
    const response = await axios.post(`${API_URL}/model`, {
      essay: essay,
      title: essayTitle.trim(),
      id: id,
      rewrite_of: rewriteOf || null,
      class_id: classId || null,
      activity_id: activityId || null
    }, {
      headers: authHeaders()
    })

    const data = response.data
    return data
  }

  const clearEssay = () => {
    if (hasSubmitted) {
      return
    }
    setEssay('')
  }

  const startNewEssay = () => {
    setEssay('')
    setEssayTitle('')
    setSubmissionResult(null)
    setHasSubmitted(false)
    setIsModalOpen(false)
  }

  const [tema, setTema] = useState<string>('')
  const [descricaoTema, setDescricaoTema] = useState<string>('')

  useEffect(() => {
    // Garantir que está no client antes de acessar o localStorage
    if (typeof window !== 'undefined') {
      const temaSalvo = localStorage.getItem('temaRedacao')
      if (temaSalvo) {
        setTema(temaSalvo)
      }
      const descricaoSalvo = localStorage.getItem('descricaoRedacao')
      if (descricaoSalvo) {
        setDescricaoTema(descricaoSalvo)
      }
    }
  }, [])

  useEffect(() => {
    const fetchTema = async () => {
      if (!id || tema) {
        return
      }

      try {
        const response = await authFetch(`${API_URL}/temas`)
        if (response.ok) {
          const temas = await response.json()
          const temaAtual = temas.find((item: any) => item._id === id)
          if (temaAtual) {
            setTema(temaAtual.tema)
            setDescricaoTema(temaAtual.descricao)
          }
        }
      } catch (error) {
        console.error('Erro ao buscar tema:', error)
      }
    }

    fetchTema()
  }, [id, tema])

  const wordCount = essay.trim() ? essay.trim().split(/\s+/).length : 0
  const charCount = essay.length
  const readiness = getEssayReadiness(essay)
  const submittedGrades = extractSubmittedGrades(submissionResult)
  const submittedTotal = submittedGrades.reduce((sum: number, value: any) => sum + (Number(value) || 0), 0)
  const isInvalidSubmission = submissionResult?.ai_quality?.status === 'invalid_submission'

  return (
    <PageShell maxWidth={1040}>
      <PageHeader
        title={rewriteOf ? 'Reescrever redação' : 'Enviar redação'}
        description="Produza seu texto dissertativo-argumentativo e envie para receber a avaliação por competência."
      />

      {rewriteOf && (
        <Alert
          type="info"
          showIcon
          message="Reescrita de redação anterior"
          description="Esta submissão será vinculada à versão anterior para comparação de progresso."
          style={{ marginBottom: 16 }}
        />
      )}

      {hasSubmitted && (
        <Alert
          type="success"
          showIcon
          message="Redação já enviada"
          description="Esta submissão foi registrada. Para evitar duplicidade, o envio desta página foi bloqueado."
          style={{ marginBottom: 16 }}
        />
      )}

      <SectionPanel>
        <Collapse bordered={false} defaultActiveKey={['tema']} style={{ marginBottom: 16, background: '#ffffff' }}>
          <Panel header="Tema da redação" key="tema">
            <h2 style={{ margin: '0 0 8px', fontSize: 18 }}>{tema || 'Carregando tema...'}</h2>
            <p style={{ margin: 0, whiteSpace: 'pre-line', color: '#4b5563' }}>
              {descricaoTema || 'A descrição do tema será exibida aqui.'}
            </p>
          </Panel>
        </Collapse>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 16 }}>
          <Card size="small">
            <Statistic title="Palavras" value={wordCount} />
          </Card>
          <Card size="small">
            <Statistic title="Caracteres" value={charCount} />
          </Card>
          <Card size="small">
            <Statistic title="Linhas estimadas" value={readiness.metrics.estimatedWrittenLines} suffix="/7" />
          </Card>
          <Card size="small">
            <Statistic title="Palavras distintas" value={readiness.metrics.uniqueWords} />
          </Card>
        </div>

        <div style={styles.readinessPanel}>
          <div style={styles.readinessHeader}>
            <div>
              <strong style={styles.readinessTitle}>Pronto para avaliação IA</strong>
              <span style={styles.readinessSubtitle}>
                O envio é liberado quando a redação atende aos critérios mínimos.
              </span>
            </div>
            <span style={{ ...styles.readinessBadge, ...(readiness.isReady ? styles.readinessBadgeReady : styles.readinessBadgeBlocked) }}>
              {readiness.isReady ? 'Liberado' : 'Bloqueado'}
            </span>
          </div>
          <div style={styles.criteriaGrid}>
            {readiness.criteria.map((criterion) => (
              <div key={criterion.key} style={styles.criterionItem}>
                {criterion.passed ? (
                  <CheckCircleOutlined style={{ color: '#1f8f5f', fontSize: 17 }} />
                ) : (
                  <CloseCircleOutlined style={{ color: '#b45309', fontSize: 17 }} />
                )}
                <span style={styles.criterionLabel}>{criterion.label}</span>
                <span style={styles.criterionValue}>{criterion.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ maxWidth: 860, margin: '0 auto 14px' }}>
          <label style={styles.inputLabel}>Título da redação</label>
          <Input
            size="large"
            value={essayTitle}
            onChange={(event) => setEssayTitle(event.target.value)}
            disabled={hasSubmitted}
            placeholder="Título da redação (opcional)"
          />
        </div>

        <div style={styles.paperShell}>
          <div style={styles.paperHeader}>
            <div>
              <span style={styles.paperLabel}>Tema</span>
              <strong style={styles.paperTitle}>{tema || 'Redação'}</strong>
              <span style={styles.paperSubtitle}>
                Título: {essayTitle.trim() || 'Sem título'}
              </span>
            </div>
            <div style={styles.paperMeta}>
              <span>{nomeUsuario || 'Aluno'}</span>
              <span>{new Intl.DateTimeFormat('pt-BR').format(new Date())}</span>
            </div>
          </div>

          <TextArea
            value={essay}
            onChange={handleChange}
            style={styles.paperTextArea}
            placeholder='Escreva sua redação aqui'
            autoComplete='off'
            autoCorrect='off'
            autoCapitalize='off'
            spellCheck={false}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginTop: 16, flexWrap: 'wrap' }}>
          <Button onClick={() => router.push('/quintana/home')}>
            Voltar
          </Button>
          <Space wrap>
            <Button onClick={clearEssay} disabled={hasSubmitted} danger icon={<ClearOutlined />}>
              Apagar texto
            </Button>
            <Button
              type="primary"
              onClick={showModalText}
              loading={isSubmitting}
              disabled={hasSubmitted || !readiness.isReady}
              icon={<CheckOutlined />}
            >
              {hasSubmitted ? 'Redação enviada' : 'Enviar redação'}
            </Button>
          </Space>
        </div>
      </SectionPanel>

      <Modal
        title={null}
        open={isModalOpen}
        onOk={handleOk}
        onCancel={handleCancel}
        footer={null}
        width={640}
      >
        <Result
          status={isInvalidSubmission ? 'warning' : 'success'}
          title={isInvalidSubmission ? 'Redação submetida com nota zero' : 'Redação submetida com sucesso'}
          subTitle={
            isInvalidSubmission
              ? 'O texto não atende aos critérios mínimos para avaliação por competências. O modelo IA não foi acionado.'
              : 'A avaliação automática da IA foi registrada. O feedback IA pode levar alguns instantes para aparecer nos detalhes da redação.'
          }
          extra={[
            <Button key="home" type="primary" onClick={() => router.push('/quintana/home')}>
              Ver minhas redações
            </Button>,
            <Button key="new" onClick={startNewEssay}>
              Escrever nova redação
            </Button>,
            <Button key="continue" onClick={handleCancel}>
              Continuar nesta página
            </Button>
          ]}
        />

        {submissionResult?.grades && (
          <div style={styles.resultPanel}>
            {submissionResult.ai_quality?.status && submissionResult.ai_quality.status !== 'ok' && (
              <Alert
                style={{ marginBottom: 16 }}
                type={isInvalidSubmission || submissionResult.ai_quality.requires_review ? 'warning' : 'info'}
                showIcon
                message={
                  isInvalidSubmission
                    ? 'Redação não avaliável'
                    : submissionResult.ai_quality.requires_review
                      ? 'Avaliação IA requer revisão'
                      : 'Revisão humana recomendada'
                }
                description={
                  <div>
                    {(submissionResult.ai_quality.flags || []).map((flag: any, index: number) => (
                      <p key={`${flag.code || 'flag'}-${index}`} style={{ margin: index === 0 ? 0 : '6px 0 0' }}>
                        {flag.message}
                      </p>
                    ))}
                  </div>
                }
              />
            )}
            <p style={styles.submittedTitle}>
              <strong>Título:</strong> {essayTitle.trim() || 'Sem título'}
            </p>
            <Statistic
              title="Nota IA total"
              value={submittedTotal}
              suffix="/1000"
            />
            <div style={styles.gradeGrid}>
              {COMPETENCIES.map((competency, index) => {
                const value = submittedGrades[index]
                return (
                  <Card key={competency.code} size="small" style={styles.gradeItem}>
                    <Statistic
                      title={`Nota IA ${competency.code} - ${competency.title}`}
                      value={Math.round(Number(value) || 0)}
                      suffix="/200"
                    />
                  </Card>
                )
              })}
            </div>
          </div>
        )}
      </Modal>
    </PageShell>
  )
}

const styles: Record<string, CSSProperties> = {
  paperShell: {
    maxWidth: 860,
    margin: '0 auto',
    background: '#fffdf8',
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    boxShadow: '0 18px 34px rgba(15, 23, 42, 0.10)',
    overflow: 'hidden'
  },
  paperHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: 16,
    alignItems: 'flex-start',
    flexWrap: 'wrap',
    padding: '16px 22px 14px 72px',
    borderBottom: '1px solid #e5e7eb',
    background: '#fffaf0'
  },
  paperLabel: {
    display: 'block',
    color: '#6b7280',
    fontSize: 12,
    marginBottom: 3
  },
  paperTitle: {
    display: 'block',
    color: '#111827',
    fontSize: 15
  },
  paperSubtitle: {
    display: 'block',
    color: '#4b5563',
    fontSize: 13,
    marginTop: 5
  },
  inputLabel: {
    display: 'block',
    marginBottom: 6,
    color: '#374151',
    fontWeight: 600
  },
  paperMeta: {
    display: 'flex',
    gap: 12,
    color: '#6b7280',
    fontSize: 13,
    flexWrap: 'wrap'
  },
  paperTextArea: {
    width: '100%',
    minHeight: 560,
    border: 0,
    borderRadius: 0,
    padding: '22px 28px 28px 72px',
    backgroundColor: '#fffdf8',
    backgroundImage: [
      'linear-gradient(to right, transparent 55px, rgba(220, 38, 38, 0.34) 56px, transparent 57px)',
      'repeating-linear-gradient(to bottom, transparent 0, transparent 31px, rgba(59, 130, 246, 0.28) 32px)'
    ].join(', '),
    backgroundAttachment: 'local',
    color: '#1f2937',
    fontFamily: '"Segoe Print", "Bradley Hand", "Comic Sans MS", cursive',
    fontSize: 19,
    lineHeight: '32px',
    resize: 'vertical',
    boxShadow: 'none'
  },
  resultPanel: {
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: 16,
    background: '#fafafa'
  },
  submittedTitle: {
    margin: '0 0 14px',
    color: '#374151'
  },
  gradeGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr',
    gap: 10,
    marginTop: 14
  },
  gradeItem: {
    borderRadius: 8
  },
  readinessPanel: {
    border: '1px solid #d9eadf',
    borderRadius: 8,
    padding: 14,
    marginBottom: 16,
    background: '#f7fbf8'
  },
  readinessHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
    flexWrap: 'wrap',
    marginBottom: 12
  },
  readinessTitle: {
    display: 'block',
    color: '#1f2937',
    fontSize: 15
  },
  readinessSubtitle: {
    display: 'block',
    color: '#6b7280',
    fontSize: 13,
    marginTop: 3
  },
  readinessBadge: {
    borderRadius: 999,
    padding: '4px 10px',
    fontSize: 12,
    fontWeight: 700
  },
  readinessBadgeReady: {
    color: '#146c43',
    background: '#dff5e8'
  },
  readinessBadgeBlocked: {
    color: '#92400e',
    background: '#fef3c7'
  },
  criteriaGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: 10
  },
  criterionItem: {
    display: 'grid',
    gridTemplateColumns: '18px 1fr auto',
    alignItems: 'center',
    gap: 8,
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: '9px 10px',
    background: '#ffffff'
  },
  criterionLabel: {
    color: '#374151',
    fontSize: 13
  },
  criterionValue: {
    color: '#111827',
    fontSize: 13,
    fontWeight: 700
  }
}

export default Redacao
