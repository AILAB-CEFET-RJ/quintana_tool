import { useEffect } from 'react'
import type { CSSProperties } from 'react'
import { Button } from 'antd'
import { LoginOutlined, UserAddOutlined } from '@ant-design/icons'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { useAuth } from '@/context'

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
      </section>
    </main>
  )
}

const styles: Record<string, CSSProperties> = {
  hero: {
    minHeight: 'calc(100vh - 64px)',
    backgroundImage: 'linear-gradient(90deg, rgba(15, 23, 42, 0.84), rgba(15, 23, 42, 0.45)), url("/bookPages.jpg")',
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    display: 'flex',
    alignItems: 'center',
    padding: '48px 8vw'
  },
  content: {
    maxWidth: 720,
    color: '#ffffff'
  },
  badge: {
    display: 'inline-flex',
    border: '1px solid rgba(255, 255, 255, 0.34)',
    borderRadius: 999,
    padding: '7px 13px',
    marginBottom: 20,
    background: 'rgba(255, 255, 255, 0.12)',
    fontWeight: 700
  },
  title: {
    margin: 0,
    fontSize: 48,
    lineHeight: 1.08,
    letterSpacing: 0
  },
  description: {
    margin: '18px 0 0',
    color: '#e5e7eb',
    fontSize: 18,
    lineHeight: 1.65,
    maxWidth: 620
  },
  actions: {
    display: 'flex',
    gap: 12,
    flexWrap: 'wrap',
    marginTop: 28
  }
}

export default Index
