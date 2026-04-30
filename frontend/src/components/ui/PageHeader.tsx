import type { CSSProperties, ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  description?: string
  actions?: ReactNode
}

const PageHeader: React.FC<PageHeaderProps> = ({ title, description, actions }) => (
  <header style={styles.header}>
    <div>
      <h1 style={styles.title}>{title}</h1>
      {description && <p style={styles.description}>{description}</p>}
    </div>
    {actions && <div style={styles.actions}>{actions}</div>}
  </header>
)

const styles: Record<string, CSSProperties> = {
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 16,
    marginBottom: 20,
    flexWrap: 'wrap'
  },
  title: {
    margin: 0,
    color: '#111827',
    fontSize: 28,
    lineHeight: 1.2,
    fontWeight: 700
  },
  description: {
    margin: '8px 0 0',
    color: '#6b7280',
    fontSize: 15,
    maxWidth: 720
  },
  actions: {
    display: 'flex',
    gap: 8,
    alignItems: 'center',
    flexWrap: 'wrap'
  }
}

export default PageHeader
