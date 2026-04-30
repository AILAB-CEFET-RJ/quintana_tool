import type { CSSProperties, ReactNode } from 'react'

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
    background: '#f5f7fb'
  },
  brandPanel: {
    minHeight: 520,
    backgroundImage: 'linear-gradient(90deg, rgba(9, 30, 66, 0.82), rgba(9, 30, 66, 0.48)), url("/bookPages.jpg")',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    display: 'flex',
    alignItems: 'flex-end'
  },
  brandOverlay: {
    padding: '56px',
    maxWidth: 680,
    color: '#ffffff'
  },
  badge: {
    display: 'inline-flex',
    border: '1px solid rgba(255, 255, 255, 0.36)',
    borderRadius: 999,
    padding: '6px 12px',
    marginBottom: 18,
    background: 'rgba(255, 255, 255, 0.12)',
    fontWeight: 700
  },
  brandTitle: {
    margin: 0,
    fontSize: 40,
    lineHeight: 1.1,
    letterSpacing: 0
  },
  brandText: {
    margin: '18px 0 0',
    fontSize: 17,
    lineHeight: 1.65,
    color: '#e5e7eb'
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
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    background: '#ffffff',
    padding: 28,
    boxShadow: '0 18px 45px rgba(15, 23, 42, 0.08)'
  },
  formHeader: {
    marginBottom: 22
  },
  title: {
    margin: 0,
    color: '#111827',
    fontSize: 26,
    lineHeight: 1.2
  },
  subtitle: {
    margin: '8px 0 0',
    color: '#6b7280',
    lineHeight: 1.5
  }
}

export default AuthShell
