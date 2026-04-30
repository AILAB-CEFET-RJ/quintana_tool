import { Checkbox, Empty, message } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import type React from 'react'
import type { CSSProperties } from 'react'
import { API_URL } from '@/config/config'

interface RewriteChecklistProps {
  redacao: any
}

const defaultItems = [
  { id: 'tese', label: 'Minha tese aparece claramente na introdução?' },
  { id: 'argumentos', label: 'Cada parágrafo desenvolve um argumento completo?' },
  { id: 'conectivos', label: 'Usei conectivos adequados entre ideias e parágrafos?' },
  { id: 'intervencao', label: 'Minha proposta tem agente, ação, meio, finalidade e detalhamento?' }
]

const RewriteChecklist: React.FC<RewriteChecklistProps> = ({ redacao }) => {
  const items = useMemo(() => redacao?.feedback_structured?.rewrite_checklist || defaultItems, [redacao])
  const [checked, setChecked] = useState<Record<string, boolean>>(redacao?.rewrite_checklist_state || {})
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    setChecked(redacao?.rewrite_checklist_state || {})
  }, [redacao])

  if (!items.length) {
    return <Empty description="Checklist indisponível" />
  }

  const updateItem = async (id: string, value: boolean) => {
    const nextState = { ...checked, [id]: value }
    setChecked(nextState)

    if (!redacao?._id) {
      return
    }

    try {
      setIsSaving(true)
      const response = await fetch(`${API_URL}/redacoes/${redacao._id}/rewrite-checklist`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rewrite_checklist_state: nextState })
      })

      if (!response.ok) {
        throw new Error('Erro ao salvar checklist')
      }
    } catch (error) {
      console.error('Erro ao salvar checklist:', error)
      message.error('Não foi possível salvar o checklist.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div style={styles.wrapper}>
      <h3 style={styles.title}>Checklist da próxima reescrita</h3>
      {isSaving && <p style={styles.saving}>Salvando...</p>}
      <div style={styles.list}>
        {items.map((item: any) => (
          <Checkbox
            key={item.id}
            checked={!!checked[item.id]}
            onChange={(event) => updateItem(item.id, event.target.checked)}
          >
            {item.label}
          </Checkbox>
        ))}
      </div>
    </div>
  )
}

const styles: Record<string, CSSProperties> = {
  wrapper: {
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: 16,
    background: '#ffffff'
  },
  title: {
    margin: '0 0 12px',
    fontSize: 18
  },
  saving: {
    margin: '-8px 0 10px',
    color: '#6b7280',
    fontSize: 13
  },
  list: {
    display: 'grid',
    gap: 10
  }
}

export default RewriteChecklist
