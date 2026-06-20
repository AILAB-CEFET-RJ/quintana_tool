import type { CSSProperties, ReactNode } from 'react'
import { theme } from '@/styles/theme'

interface AuthShellProps {
  title: string
  subtitle: string
  children: ReactNode
}

const AuthShell: React.FC<AuthShellProps> = ({ title, subtitle, children }) => (
  <main style={styles.wrapper}>
    <section style={styles.brandPanel}>
      <div style={styles.brandOverlay}>
        <span style={styles.badge}>Quintana</span>
        <h1 style={styles.brandTitle}>Avaliação formativa para redações do ENEM</h1>
        <p style={styles.brandText}>
          Acompanhe competências, progresso e próximos passos de estudo em uma experiência clara para estudantes e professores.
        </p>
      </div>
    </section>
    <section style={styles.formPanel}>
      <div style={styles.formCard}>
        <div style={styles.formHeader}>
          <h2 style={styles.title}>{title}</h2>
          <p style={styles.subtitle}>{subtitle}</p>
        </div>
        {children}
      </div>
    </section>
  </main>
)

const styles: Record<string, CSSProperties> = {
  wrapper: {
    minHeight: 'calc(100vh - 64px)',
    display: 'grid',
    gridTemplateColumns: 'minmax(320px, 1fr) minmax(360px, 520px)',
    background: theme.colors.bg
  },
  brandPanel: {
    minHeight: 520,
    backgroundImage: 'linear-gradient(90deg, rgba(244, 241, 236, 0.92), rgba(244, 241, 236, 0.72)), url("/bookPages.jpg")',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    display: 'flex',
    alignItems: 'flex-end',
    borderRight: `1px solid ${theme.colors.rule}`
  },
  brandOverlay: {
    padding: '56px',
    maxWidth: 680,
    color: theme.colors.ink
  },
  badge: {
    display: 'inline-flex',
    border: `1px solid ${theme.colors.rule}`,
    borderRadius: theme.radius.sm,
    padding: '6px 12px',
    marginBottom: 18,
    background: theme.colors.surface,
    color: theme.colors.inkPale,
    fontSize: 12,
    letterSpacing: '0.16em',
    textTransform: 'uppercase'
  },
  brandTitle: {
    margin: 0,
    fontFamily: theme.fonts.serif,
    fontSize: 42,
    lineHeight: 1.1,
    letterSpacing: 0,
    fontWeight: 500
  },
  brandText: {
    margin: '18px 0 0',
    fontSize: 17,
    lineHeight: 1.65,
    color: theme.colors.inkLight
  },
  formPanel: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px 28px'
  },
  formCard: {
    width: '100%',
    maxWidth: 420,
    border: `1px solid ${theme.colors.rule}`,
    borderRadius: theme.radius.md,
    background: theme.colors.surface,
    padding: 28,
    boxShadow: `0 18px 45px ${theme.colors.shadow}`
  },
  formHeader: {
    marginBottom: 22
  },
  title: {
    margin: 0,
    color: theme.colors.ink,
    fontFamily: theme.fonts.serif,
    fontSize: 30,
    lineHeight: 1.2,
    fontWeight: 500
  },
  subtitle: {
    margin: '8px 0 0',
    color: theme.colors.inkLight,
    lineHeight: 1.5
  }
}

export default AuthShell
