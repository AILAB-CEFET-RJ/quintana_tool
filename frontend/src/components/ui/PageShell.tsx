import type { CSSProperties, ReactNode } from 'react'
import { theme } from '@/styles/theme'

interface PageShellProps {
  children: ReactNode
  maxWidth?: number
}

const PageShell: React.FC<PageShellProps> = ({ children, maxWidth = 1180 }) => (
  <main style={styles.page}>
    <div style={{ ...styles.inner, maxWidth }}>
      {children}
    </div>
  </main>
)

const styles: Record<string, CSSProperties> = {
  page: {
    minHeight: 'calc(100vh - 64px)',
    background: theme.colors.bg,
    padding: '28px 24px 48px'
  },
  inner: {
    width: '100%',
    margin: '0 auto'
  }
}

export default PageShell
