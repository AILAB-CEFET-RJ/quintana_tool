import axios from 'axios'
import { useRouter } from 'next/router';
import { useState, useEffect } from 'react'
import { Modal, Skeleton, Collapse } from 'antd'
import { ClearOutlined, CheckOutlined, UploadOutlined } from '@ant-design/icons'
import TextArea from 'antd/lib/input/TextArea'
import { S } from '@/styles/Redacao.styles'
import { useAuth } from '../../context';
import { API_URL } from "@/config/config";
import { CSSProperties } from 'react'


const Redacao = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [essay, setEssay] = useState('')
  const [essayGrade, setEssayGrade] = useState<object>({ key: 'value' })
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const router = useRouter();
  const { id, rewriteOf, classId, activityId } = router.query;
  const { nomeUsuario } = useAuth();
  const { Panel } = Collapse;

  const showModalText = async () => {
    await getEssayGrade()
    setIsModalOpen(true)
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
    })

    const data = response.data
    console.log(data.grades)

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
      const response = await axios.post(`${API_URL}/model2`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })


      const data = response.data
      setEssayGrade(data.grades)

    } catch (error) {
      console.error(error)
    }
  }


  const labelStyle = {
    marginTop: '20px',
    marginBottom: '25px',
    whiteSpace: 'pre-line' as const,
    width: '50%',
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

  return (
    <S.Wrapper>
      <S.Title>🧾 Redação 🧾</S.Title>
      {rewriteOf && (
        <p style={{ color: '#6b7280', marginTop: -8 }}>
          Reescrita de uma redação anterior
        </p>
      )}

      <Collapse style={labelStyle}>
        <Panel header="Tema" key="1">
          <h3>{tema}</h3>
          <span>{descricaoTema}</span>
        </Panel>
      </Collapse>

      <TextArea
        value={essay}
        onChange={handleChange}
        style={{ padding: 24, minHeight: 380, background: 'white', width: '50%' }}
        placeholder='Escreva sua redação aqui'
        autoComplete='off'
        autoCorrect='off'
        autoCapitalize='off'
        spellCheck={false}
      />

      <S.ButtonWrapper>
        <S.MyButton onClick={clearEssay} size='small' type='primary' danger icon={<ClearOutlined />}>
          Apagar texto
        </S.MyButton>

        <S.MyButton onClick={showModalText} size='small' type='primary' icon={<CheckOutlined />}>
          Enviar redação
        </S.MyButton>
      </S.ButtonWrapper>

      <Modal title='Nota da redação' open={isModalOpen} onOk={handleOk} onCancel={handleCancel} footer={null}>
        {essayGrade ? (
          Object.entries(essayGrade).map(([key, value], index) => (
            <p key={index}>{key}: <strong>{value}</strong></p>
          ))
        ) : (
          <Skeleton paragraph={{ rows: 0 }} />
        )}
      </Modal>
    </S.Wrapper>
  )
}

export default Redacao
