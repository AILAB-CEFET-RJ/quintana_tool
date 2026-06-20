import type { CSSProperties, ReactNode } from 'react'
import { theme } from '@/styles/theme'

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
    color: theme.colors.ink,
    fontFamily: theme.fonts.serif,
    fontSize: 34,
    lineHeight: 1.2,
    fontWeight: 500,
    letterSpacing: 0
  },
  description: {
    margin: '8px 0 0',
    color: theme.colors.inkLight,
    fontSize: 16,
    lineHeight: 1.65,
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
