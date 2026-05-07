import { Button, Card, Form, Input, Modal, Popconfirm, Select, Space, Statistic, Table, Tag, message, Row, Col } from 'antd'
import { BarChartOutlined, DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type React from 'react'
import { useEffect, useState } from 'react'
import { API_URL } from '@/config/config'
import type { Tema } from '@/pages/quintana/home'
import { authFetch, authHeaders } from '@/lib/authFetch'

interface TeacherClassActivityManagerProps {
  teacher: string
  alunos: any[]
  temas: Tema[]
  onChanged?: () => void
}

const TeacherClassActivityManager: React.FC<TeacherClassActivityManagerProps> = ({ teacher, alunos, temas, onChanged }) => {
  const [classes, setClasses] = useState<any[]>([])
  const [activities, setActivities] = useState<any[]>([])
  const [editingClass, setEditingClass] = useState<any | null>(null)
  const [editingActivity, setEditingActivity] = useState<any | null>(null)
  const [submissionStatus, setSubmissionStatus] = useState<any | null>(null)
  const [submissionModalOpen, setSubmissionModalOpen] = useState(false)
  const [classForm] = Form.useForm()
  const [activityForm] = Form.useForm()
  const [editClassForm] = Form.useForm()
  const [editActivityForm] = Form.useForm()
  const teacherThemes = temas.filter((tema) => tema.teacher_id === teacher)

  const fetchData = async () => {
    if (!teacher) return

    const [classesResponse, activitiesResponse] = await Promise.all([
      authFetch(`${API_URL}/classes`),
      authFetch(`${API_URL}/activities`)
    ])

    if (classesResponse.ok) {
      setClasses(await classesResponse.json())
    }

    if (activitiesResponse.ok) {
      setActivities(await activitiesResponse.json())
    }
  }

  useEffect(() => {
    fetchData()
  }, [teacher])

  const notifyChanged = async () => {
    await fetchData()
    onChanged?.()
  }

  const createClass = async (values: any) => {
    const response = await authFetch(`${API_URL}/classes`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        name: values.name,
        student_ids: values.student_ids || []
      })
    })

    if (response.ok) {
      message.success('Turma criada com sucesso!')
      classForm.resetFields()
      notifyChanged()
    } else {
      message.error('Erro ao criar turma.')
    }
  }

  const createActivity = async (values: any) => {
    const response = await authFetch(`${API_URL}/activities`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        title: values.title,
        class_id: values.class_id,
        theme_id: values.theme_id,
        due_date: values.due_date || ''
      })
    })

    if (response.ok) {
      message.success('Atividade criada com sucesso!')
      activityForm.resetFields()
      notifyChanged()
    } else {
      message.error('Erro ao criar atividade.')
    }
  }

  const deleteClass = async (id: string) => {
    const response = await authFetch(`${API_URL}/classes/${id}`, { method: 'DELETE' })
    if (response.ok) {
      message.success('Turma removida.')
      notifyChanged()
    } else {
      message.error('Erro ao remover turma.')
    }
  }

  const deleteActivity = async (id: string) => {
    const response = await authFetch(`${API_URL}/activities/${id}`, { method: 'DELETE' })
    if (response.ok) {
      message.success('Atividade removida.')
      notifyChanged()
    } else {
      message.error('Erro ao remover atividade.')
    }
  }

  const openEditClass = (record: any) => {
    setEditingClass(record)
    editClassForm.setFieldsValue({
      name: record.name,
      student_ids: record.student_ids || []
    })
  }

  const openEditActivity = (record: any) => {
    setEditingActivity(record)
    editActivityForm.setFieldsValue({
      title: record.title,
      class_id: record.class_id,
      theme_id: record.theme_id,
      due_date: record.due_date || ''
    })
  }

  const updateClass = async (values: any) => {
    if (!editingClass) return

    const response = await authFetch(`${API_URL}/classes/${editingClass._id}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        name: values.name,
        student_ids: values.student_ids || []
      })
    })

    if (response.ok) {
      message.success('Turma atualizada.')
      setEditingClass(null)
      notifyChanged()
    } else {
      message.error('Erro ao atualizar turma.')
    }
  }

  const updateActivity = async (values: any) => {
    if (!editingActivity) return

    const response = await authFetch(`${API_URL}/activities/${editingActivity._id}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        title: values.title,
        class_id: values.class_id,
        theme_id: values.theme_id,
        due_date: values.due_date || ''
      })
    })

    if (response.ok) {
      message.success('Atividade atualizada.')
      setEditingActivity(null)
      notifyChanged()
    } else {
      message.error('Erro ao atualizar atividade.')
    }
  }

  const openSubmissionStatus = async (record: any) => {
    const response = await authFetch(`${API_URL}/activities/${record._id}/submissions`)

    if (response.ok) {
      setSubmissionStatus(await response.json())
      setSubmissionModalOpen(true)
    } else {
      message.error('Erro ao carregar submissões da atividade.')
    }
  }

  const getClassName = (id: string) => classes.find((item) => item._id === id)?.name || 'Turma não encontrada'
  const getThemeName = (id: string) => teacherThemes.find((item) => item._id === id)?.tema || 'Tema não encontrado'

  const classColumns: ColumnsType<any> = [
    { title: 'Turma', dataIndex: 'name', key: 'name' },
    {
      title: 'Alunos',
      dataIndex: 'student_ids',
      key: 'student_ids',
      render: (studentIds: string[]) => (
        <Space wrap>
          {(studentIds || []).map((studentId) => {
            const aluno = alunos.find((item) => item._id === studentId)
            return <Tag key={studentId}>{aluno?.display_name || aluno?.email || studentId}</Tag>
          })}
        </Space>
      )
    },
    {
      title: 'Ações',
      key: 'actions',
      align: 'center' as const,
      render: (_, record) => (
        <Space>
          <Button icon={<EditOutlined />} onClick={() => openEditClass(record)} />
          <Popconfirm title="Remover turma?" onConfirm={() => deleteClass(record._id)}>
            <Button danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  const activityColumns: ColumnsType<any> = [
    { title: 'Atividade', dataIndex: 'title', key: 'title' },
    { title: 'Turma', dataIndex: 'class_id', key: 'class_id', render: getClassName },
    { title: 'Tema', dataIndex: 'theme_id', key: 'theme_id', render: getThemeName },
    { title: 'Prazo', dataIndex: 'due_date', key: 'due_date', render: (value: string) => value || '-' },
    {
      title: 'Link de envio',
      key: 'link',
      render: (_, record) => (
        <a
          href={`/quintana/redacao?id=${record.theme_id}&classId=${record.class_id}&activityId=${record._id}`}
          target="_blank"
          rel="noreferrer"
        >
          Abrir
        </a>
      )
    },
    {
      title: 'Submissões',
      key: 'submissions',
      align: 'center' as const,
      render: (_, record) => (
        <Button icon={<BarChartOutlined />} onClick={() => openSubmissionStatus(record)}>
          Status
        </Button>
      )
    },
    {
      title: 'Ações',
      key: 'actions',
      align: 'center' as const,
      render: (_, record) => (
        <Space>
          <Button icon={<EditOutlined />} onClick={() => openEditActivity(record)} />
          <Popconfirm title="Remover atividade?" onConfirm={() => deleteActivity(record._id)}>
            <Button danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <Card title="Cadastrar turma" style={{ borderRadius: 8 }}>
        <Form form={classForm} layout="vertical" onFinish={createClass}>
          <Form.Item name="name" label="Nome da turma" rules={[{ required: true, message: 'Informe o nome da turma.' }]}>
            <Input placeholder="Ex.: 3001 - Manhã" />
          </Form.Item>
          <Form.Item name="student_ids" label="Alunos">
            <Select
              mode="multiple"
              placeholder="Selecione os alunos"
              options={alunos.map((aluno) => ({ label: aluno.display_name || aluno.email, value: aluno._id }))}
            />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>Criar turma</Button>
        </Form>
      </Card>

      <Card title="Turmas cadastradas" style={{ borderRadius: 8 }}>
        <Table rowKey="_id" dataSource={classes} columns={classColumns} pagination={{ pageSize: 5 }} />
      </Card>

      <Card title="Cadastrar atividade" style={{ borderRadius: 8 }}>
        <Form form={activityForm} layout="vertical" onFinish={createActivity}>
          <Form.Item name="title" label="Título da atividade" rules={[{ required: true, message: 'Informe o título da atividade.' }]}>
            <Input placeholder="Ex.: Redação 3 - proposta de intervenção" />
          </Form.Item>
          <Form.Item name="class_id" label="Turma" rules={[{ required: true, message: 'Selecione uma turma.' }]}>
            <Select options={classes.map((item) => ({ label: item.name, value: item._id }))} />
          </Form.Item>
          <Form.Item name="theme_id" label="Tema" rules={[{ required: true, message: 'Selecione um tema.' }]}>
            <Select options={teacherThemes.map((item) => ({ label: item.tema, value: item._id }))} />
          </Form.Item>
          <Form.Item name="due_date" label="Prazo">
            <Input type="date" />
          </Form.Item>
          <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>Criar atividade</Button>
        </Form>
      </Card>

      <Card title="Atividades cadastradas" style={{ borderRadius: 8 }}>
        <Table rowKey="_id" dataSource={activities} columns={activityColumns} pagination={{ pageSize: 5 }} />
      </Card>

      <Modal
        title="Editar turma"
        open={!!editingClass}
        onCancel={() => setEditingClass(null)}
        onOk={() => editClassForm.submit()}
        okText="Salvar"
      >
        <Form form={editClassForm} layout="vertical" onFinish={updateClass}>
          <Form.Item name="name" label="Nome da turma" rules={[{ required: true, message: 'Informe o nome da turma.' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="student_ids" label="Alunos">
            <Select
              mode="multiple"
              options={alunos.map((aluno) => ({ label: aluno.display_name || aluno.email, value: aluno._id }))}
            />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Editar atividade"
        open={!!editingActivity}
        onCancel={() => setEditingActivity(null)}
        onOk={() => editActivityForm.submit()}
        okText="Salvar"
      >
        <Form form={editActivityForm} layout="vertical" onFinish={updateActivity}>
          <Form.Item name="title" label="Título da atividade" rules={[{ required: true, message: 'Informe o título da atividade.' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="class_id" label="Turma" rules={[{ required: true, message: 'Selecione uma turma.' }]}>
            <Select options={classes.map((item) => ({ label: item.name, value: item._id }))} />
          </Form.Item>
          <Form.Item name="theme_id" label="Tema" rules={[{ required: true, message: 'Selecione um tema.' }]}>
            <Select options={teacherThemes.map((item) => ({ label: item.tema, value: item._id }))} />
          </Form.Item>
          <Form.Item name="due_date" label="Prazo">
            <Input type="date" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Status de submissões"
        open={submissionModalOpen}
        onCancel={() => setSubmissionModalOpen(false)}
        footer={null}
        width={760}
      >
        {submissionStatus && (
          <div style={{ display: 'grid', gap: 16 }}>
            <Card size="small">
              <strong>{submissionStatus.activity?.title}</strong>
              <p style={{ margin: '4px 0 0', color: '#6b7280' }}>
                {submissionStatus.activity?.class_name} · {submissionStatus.activity?.theme}
              </p>
            </Card>
            <Row gutter={[12, 12]}>
              <Col xs={24} sm={8}>
                <Card size="small"><Statistic title="Esperados" value={submissionStatus.expected_count} /></Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card size="small"><Statistic title="Enviados" value={submissionStatus.submission_count} /></Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card size="small"><Statistic title="Pendentes" value={submissionStatus.missing_students?.length || 0} /></Card>
              </Col>
            </Row>
            <Card size="small" title="Enviados">
              <Space wrap>
                {(submissionStatus.submitted_students || []).map((student: string) => <Tag color="green" key={student}>{student}</Tag>)}
              </Space>
            </Card>
            <Card size="small" title="Pendentes">
              <Space wrap>
                {(submissionStatus.missing_students || []).map((student: string) => <Tag color="gold" key={student}>{student}</Tag>)}
              </Space>
            </Card>
            {!!submissionStatus.late_students?.length && (
              <Card size="small" title="Atrasados">
                <Space wrap>
                  {submissionStatus.late_students.map((student: string) => <Tag color="red" key={student}>{student}</Tag>)}
                </Space>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}

export default TeacherClassActivityManager
