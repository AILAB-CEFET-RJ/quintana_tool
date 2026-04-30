import type { CSSProperties, ReactNode } from 'react'

interface SectionPanelProps {
  children: ReactNode
  title?: string
  description?: string
  actions?: ReactNode
}

const SectionPanel: React.FC<SectionPanelProps> = ({ children, title, description, actions }) => (
  <section style={styles.panel}>
    {(title || description || actions) && (
      <div style={styles.header}>
        <div>
          {title && <h2 style={styles.title}>{title}</h2>}
          {description && <p style={styles.description}>{description}</p>}
        </div>
        {actions}
      </div>
    )}
    {children}
  </section>
)

const styles: Record<string, CSSProperties> = {
  panel: {
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    background: '#ffffff',
    padding: 18,
    marginBottom: 16
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 14,
    flexWrap: 'wrap'
  },
  title: {
    margin: 0,
    fontSize: 18,
    lineHeight: 1.25,
    color: '#111827'
  },
  description: {
    margin: '4px 0 0',
    color: '#6b7280'
  }
}

export default SectionPanel
