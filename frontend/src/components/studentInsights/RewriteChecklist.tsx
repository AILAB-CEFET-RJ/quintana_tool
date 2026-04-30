import { Checkbox, Empty } from 'antd'
import { useMemo, useState } from 'react'
import type React from 'react'
import type { CSSProperties } from 'react'

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
  const [checked, setChecked] = useState<Record<string, boolean>>({})

  if (!items.length) {
    return <Empty description="Checklist indisponível" />
  }

  return (
    <div style={styles.wrapper}>
      <h3 style={styles.title}>Checklist da próxima reescrita</h3>
      <div style={styles.list}>
        {items.map((item: any) => (
          <Checkbox
            key={item.id}
            checked={!!checked[item.id]}
            onChange={(event) => setChecked((current) => ({ ...current, [item.id]: event.target.checked }))}
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
  list: {
    display: 'grid',
    gap: 10
  }
}

export default RewriteChecklist
