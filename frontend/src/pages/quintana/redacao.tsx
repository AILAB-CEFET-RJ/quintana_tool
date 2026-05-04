import axios from 'axios'
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react'
import { Modal, Collapse, Button, Space, Alert, Card, Statistic, message, Result } from 'antd'
import { ClearOutlined, CheckOutlined } from '@ant-design/icons'
import TextArea from 'antd/lib/input/TextArea'
import { useAuth } from '../../context';
import { API_URL } from "@/config/config";
import { authFetch, authHeaders } from '@/lib/authFetch'
import PageShell from '@/components/ui/PageShell'
import PageHeader from '@/components/ui/PageHeader'
import SectionPanel from '@/components/ui/SectionPanel'
import type { CSSProperties } from 'react'


const Redacao = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
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
      id: id,
      aluno: nomeUsuario,
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
        </div>

        <div style={styles.paperShell}>
          <div style={styles.paperHeader}>
            <div>
              <span style={styles.paperLabel}>Tema</span>
              <strong style={styles.paperTitle}>{tema || 'Redação'}</strong>
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
              disabled={hasSubmitted}
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
          status="success"
          title="Redação submetida com sucesso"
          subTitle="A correção foi registrada. O feedback textual pode levar alguns instantes para aparecer nos detalhes da redação."
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
            <Statistic
              title="Nota total estimada"
              value={Object.values(submissionResult.grades).reduce((sum: number, value: any) => sum + (Number(value) || 0), 0)}
              suffix="/1000"
            />
            <div style={styles.gradeGrid}>
              {Object.entries(submissionResult.grades).map(([key, value]) => (
                <div key={key} style={styles.gradeItem}>
                  <span style={styles.gradeLabel}>{key}</span>
                  <strong>{Math.round(Number(value) || 0)}</strong>
                </div>
              ))}
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
    color: '#111827',
    fontSize: 15
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
  gradeGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
    gap: 10,
    marginTop: 14
  },
  gradeItem: {
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: 10,
    background: '#ffffff',
    display: 'flex',
    justifyContent: 'space-between',
    gap: 8
  },
  gradeLabel: {
    color: '#6b7280'
  }
}

export default Redacao
