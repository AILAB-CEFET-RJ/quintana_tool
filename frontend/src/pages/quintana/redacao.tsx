import axios from 'axios'
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react'
import { Modal, Skeleton, Collapse, Button, Space, Alert, Card, Statistic, message } from 'antd'
import { ClearOutlined, CheckOutlined, UploadOutlined } from '@ant-design/icons'
import TextArea from 'antd/lib/input/TextArea'
import { useAuth } from '../../context';
import { API_URL } from "@/config/config";
import { authFetch, authHeaders } from '@/lib/authFetch'
import PageShell from '@/components/ui/PageShell'
import PageHeader from '@/components/ui/PageHeader'
import SectionPanel from '@/components/ui/SectionPanel'


const Redacao = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [essay, setEssay] = useState('')
  const [essayGrade, setEssayGrade] = useState<object>({ key: 'value' })
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const router = useRouter();
  const { id, rewriteOf, classId, activityId } = router.query;
  const { nomeUsuario } = useAuth();
  const { Panel } = Collapse;

  const showModalText = async () => {
    if (!essay.trim()) {
      message.warning('Escreva a redação antes de enviar.')
      return
    }

    try {
      setIsSubmitting(true)
      await getEssayGrade()
      setIsModalOpen(true)
    } catch (error) {
      console.error('Erro ao enviar redação:', error)
      message.error('Não foi possível enviar a redação.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const showModalImage = async () => {
    await uploadImage()
    setIsModalOpen(true)
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


  const getEssayGrade = async () => {
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
    setEssayGrade(data.grades)
  }

  const clearEssay = () => {
    setEssay('')
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0])
    }
  }

  const uploadImage = async () => {
    if (!selectedFile) {
      console.error('No file selected')
      return
    }

    const formData = new FormData()
    formData.append('image', selectedFile)
    formData.append('id', id ? id.toString() : '')
    formData.append('aluno', nomeUsuario)
    formData.append('rewrite_of', rewriteOf ? rewriteOf.toString() : '')
    formData.append('class_id', classId ? classId.toString() : '')
    formData.append('activity_id', activityId ? activityId.toString() : '')

    try {
      const response = await axios.post(`${API_URL}/model_ocr`, formData, {
        headers: {
          ...authHeaders(),
          'Content-Type': 'multipart/form-data'
        }
      })


      const data = response.data
      setEssayGrade(data.grades)

    } catch (error) {
      console.error(error)
    }
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

        <TextArea
          value={essay}
          onChange={handleChange}
          style={{ padding: 20, minHeight: 430, background: 'white', fontSize: 16, lineHeight: 1.65, resize: 'vertical' }}
          placeholder='Escreva sua redação aqui'
          autoComplete='off'
          autoCorrect='off'
          autoCapitalize='off'
          spellCheck={false}
        />

        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginTop: 16, flexWrap: 'wrap' }}>
          <Button onClick={() => router.push('/quintana/home')}>
            Voltar
          </Button>
          <Space wrap>
            <Button onClick={clearEssay} danger icon={<ClearOutlined />}>
              Apagar texto
            </Button>
            <Button type="primary" onClick={showModalText} loading={isSubmitting} icon={<CheckOutlined />}>
              Enviar redação
            </Button>
          </Space>
        </div>
      </SectionPanel>

      <Modal title='Nota da redação' open={isModalOpen} onOk={handleOk} onCancel={handleCancel} footer={null}>
        {essayGrade ? (
          Object.entries(essayGrade).map(([key, value], index) => (
            <p key={index}>{key}: <strong>{value}</strong></p>
          ))
        ) : (
          <Skeleton paragraph={{ rows: 0 }} />
        )}
      </Modal>
    </PageShell>
  )
}

export default Redacao
