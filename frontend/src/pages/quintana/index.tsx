import { useEffect } from 'react'
import type { CSSProperties } from 'react'
import { Button } from 'antd'
import { LoginOutlined, UserAddOutlined } from '@ant-design/icons'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { useAuth } from '@/context'
import { IS_WORKSHOP_MODE } from '@/config/config'
import { theme } from '@/styles/theme'

const Index = () => {
  const { isLoggedIn } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (isLoggedIn) {
      router.replace('/quintana/home')
    }
  }, [isLoggedIn, router])

  if (isLoggedIn) {
    return null
  }

  return (
    <main style={styles.hero}>
      <section style={styles.content}>
        <span style={styles.badge}>Quintana</span>
        <h1 style={styles.title}>Avaliação de redações com devolutiva clara para o próximo texto</h1>
        <p style={styles.description}>
          Visualize competências, acompanhe evolução e transforme a correção em um plano de estudo.
        </p>
        <div style={styles.actions}>
          <Link href="/quintana/login">
            <Button type="primary" size="large" icon={<LoginOutlined />}>Entrar</Button>
          </Link>
          <Link href="/quintana/cadastro">
            <Button size="large" icon={<UserAddOutlined />}>Criar conta</Button>
          </Link>
        </div>
        {IS_WORKSHOP_MODE && (
          <div style={styles.workshopBox}>
            <strong>Modo oficina ativo</strong>
            <span>Use os acessos rápidos na tela de login para demonstrar os perfis de aluno e professor.</span>
          </div>
        )}
      </section>
    </main>
  )
}

const styles: Record<string, CSSProperties> = {
  hero: {
    minHeight: 'calc(100vh - 64px)',
    backgroundImage: 'linear-gradient(90deg, rgba(244, 241, 236, 0.96), rgba(234, 231, 226, 0.78)), url("/bookPages.jpg")',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    display: 'flex',
    alignItems: 'center',
    padding: '64px 8vw',
    borderBottom: `1px solid ${theme.colors.rule}`
  },
  content: {
    maxWidth: 720,
    color: theme.colors.ink
  },
  badge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    color: theme.colors.accent,
    padding: 0,
    marginBottom: 20,
    background: 'transparent',
    fontSize: 13,
    letterSpacing: '0.14em',
    textTransform: 'uppercase'
  },
  title: {
    margin: 0,
    fontFamily: theme.fonts.serif,
    fontSize: 50,
    lineHeight: 1.08,
    letterSpacing: 0,
    fontWeight: 500
  },
  description: {
    margin: '18px 0 0',
    color: theme.colors.inkMid,
    fontSize: 18,
    lineHeight: 1.65,
    maxWidth: 620
  },
  actions: {
    display: 'flex',
    gap: 12,
    flexWrap: 'wrap',
    marginTop: 28
  },
  workshopBox: {
    display: 'grid',
    gap: 4,
    maxWidth: 520,
    marginTop: 20,
    padding: 14,
    border: `1px solid ${theme.colors.successBorder}`,
    borderRadius: theme.radius.md,
    background: theme.colors.successBg,
    color: theme.colors.inkMid
  }
}

export default Index
