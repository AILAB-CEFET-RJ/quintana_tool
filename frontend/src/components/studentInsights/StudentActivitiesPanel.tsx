import { Button, Card, Empty, List, Tag } from 'antd'
import { CheckCircleOutlined, ClockCircleOutlined, SendOutlined } from '@ant-design/icons'
import Link from 'next/link'
import type React from 'react'

interface StudentActivitiesPanelProps {
  activities: any[]
}

const StudentActivitiesPanel: React.FC<StudentActivitiesPanelProps> = ({ activities }) => {
  if (!activities.length) {
    return (
      <Card>
        <Empty description="Nenhuma atividade atribuída às suas turmas." />
      </Card>
    )
  }

  return (
    <Card title="Atividades atribuídas" style={{ borderRadius: 8 }}>
      <List
        dataSource={activities}
        renderItem={(activity) => {
          const submitted = activity.status === 'submitted'
          const late = activity.status === 'late'
          return (
            <List.Item
              actions={[
                <Link
                  key="submit"
                  href={`/quintana/redacao?id=${activity.theme_id}&classId=${activity.class_id}&activityId=${activity._id}`}
                  onClick={() => {
                    localStorage.setItem('temaRedacao', activity.theme)
                    localStorage.setItem('descricaoRedacao', activity.description || '')
                  }}
                >
                  <Button type={submitted ? 'default' : 'primary'} icon={<SendOutlined />}>
                    {submitted ? 'Reenviar' : 'Enviar'}
                  </Button>
                </Link>
              ]}
            >
              <List.Item.Meta
                title={
                  <span>
                    {activity.title}{' '}
                    <Tag color={submitted ? 'green' : late ? 'red' : 'gold'} icon={submitted ? <CheckCircleOutlined /> : <ClockCircleOutlined />}>
                      {submitted ? 'Enviada' : late ? 'Atrasada' : 'Pendente'}
                    </Tag>
                  </span>
                }
                description={`${activity.class_name} · ${activity.theme}${activity.due_date ? ` · prazo: ${activity.due_date}` : ''}`}
              />
            </List.Item>
          )
        }}
      />
    </Card>
  )
}

export default StudentActivitiesPanel
