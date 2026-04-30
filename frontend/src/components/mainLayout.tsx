import type { CSSProperties, ReactNode } from 'react'
import { useMemo, useState } from 'react'
import { Layout, Dropdown, Space, Button } from 'antd'
import {
    BookOutlined,
    HomeOutlined,
    InfoCircleOutlined,
    LoginOutlined,
    LogoutOutlined,
    ReadOutlined,
    UserOutlined,
    DownOutlined
} from '@ant-design/icons'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { useAuth } from '../context'

const { Header, Content } = Layout

interface MainLayoutProps {
    children: ReactNode
}

const MainLayout = ({ children }: MainLayoutProps) => {
    const { isLoggedIn, tipoUsuario, nomeUsuario, setAuthData } = useAuth()
    const [isMenuOpen, setIsMenuOpen] = useState(false)
    const router = useRouter()

    const handleLogout = () => {
        setAuthData({
            isLoggedIn: false,
            tipoUsuario: '',
            nomeUsuario: '',
        })

        router.push('/quintana/login')
    }

    const userItems = isLoggedIn
        ? [
            {
                key: 'profile',
                label: <span>{nomeUsuario}</span>,
                icon: <UserOutlined />,
            },
            {
                key: 'logout',
                label: <span onClick={handleLogout}>Sair</span>,
                icon: <LogoutOutlined />,
            },
        ]
        : [
            {
                key: 'login',
                label: <Link href="/quintana/login">Entrar</Link>,
                icon: <LoginOutlined />,
            },
        ]

    const navItems = useMemo(() => {
        const dashboardLabel = tipoUsuario === 'professor' ? 'Painel' : 'Minhas redações'

        return [
            ...(isLoggedIn
                ? [{ href: '/quintana/home', label: dashboardLabel, icon: <HomeOutlined /> }]
                : []),
            { href: '/quintana/competencias', label: 'Competências', icon: <ReadOutlined /> },
            { href: '/quintana/sobre', label: 'Sobre', icon: <InfoCircleOutlined /> },
        ]
    }, [isLoggedIn, tipoUsuario])

    const brandHref = isLoggedIn ? '/quintana/home' : '/quintana'

    return (
        <Layout style={{ minHeight: '100vh', background: '#f5f7fb' }}>
            <Header style={styles.header}>
                <div style={styles.headerInner}>
                    <Link href={brandHref} style={styles.brand}>
                        <span style={styles.brandMark}>Q</span>
                        <span style={styles.brandText}>Quintana</span>
                    </Link>

                    <nav style={styles.nav}>
                        {navItems.map((item) => {
                            const active = router.pathname === item.href
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    style={{
                                        ...styles.navLink,
                                        ...(active ? styles.navLinkActive : {})
                                    }}
                                >
                                    {item.icon}
                                    <span>{item.label}</span>
                                </Link>
                            )
                        })}
                    </nav>

                    <Dropdown
                        menu={{ items: userItems }}
                        onOpenChange={setIsMenuOpen}
                        overlayStyle={{ marginTop: 8 }}
                    >
                        <Button style={styles.userButton} icon={isLoggedIn ? <UserOutlined /> : <BookOutlined />}>
                            <Space>
                                {isLoggedIn ? nomeUsuario : 'Acessar'}
                                <DownOutlined style={{ transform: isMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform .18s ease' }} />
                            </Space>
                        </Button>
                    </Dropdown>
                </div>
            </Header>
            <Content>{children}</Content>
        </Layout>
    )
}

const styles: Record<string, CSSProperties> = {
    header: {
        position: 'sticky',
        top: 0,
        zIndex: 10,
        width: '100%',
        height: 64,
        padding: '0 24px',
        background: '#0f172a',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
    },
    headerInner: {
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 20,
        maxWidth: 1240,
        margin: '0 auto'
    },
    brand: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: 10,
        color: '#ffffff',
        textDecoration: 'none',
        flex: '0 0 auto'
    },
    brandMark: {
        width: 34,
        height: 34,
        borderRadius: 8,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#1677ff',
        color: '#ffffff',
        fontWeight: 800
    },
    brandText: {
        fontSize: 18,
        fontWeight: 700,
        letterSpacing: 0
    },
    nav: {
        display: 'flex',
        alignItems: 'center',
        gap: 4,
        minWidth: 0,
        flex: 1
    },
    navLink: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: 7,
        color: '#cbd5e1',
        textDecoration: 'none',
        padding: '8px 11px',
        borderRadius: 8,
        lineHeight: 1,
        whiteSpace: 'nowrap'
    },
    navLinkActive: {
        color: '#ffffff',
        background: 'rgba(255, 255, 255, 0.1)'
    },
    userButton: {
        flex: '0 0 auto',
        borderColor: 'rgba(255, 255, 255, 0.18)',
        color: '#ffffff',
        background: 'rgba(255, 255, 255, 0.08)'
    }
}

export default MainLayout
