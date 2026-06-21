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
import { IS_WORKSHOP_MODE } from '@/config/config'
import { theme } from '@/styles/theme'

const { Header, Content } = Layout

interface MainLayoutProps {
    children: ReactNode
}

const MainLayout = ({ children }: MainLayoutProps) => {
    const { isLoggedIn, tipoUsuario, nomeUsuario, setAuthData } = useAuth()
    const [isMenuOpen, setIsMenuOpen] = useState(false)
    const router = useRouter()

    const handleLogout = async () => {
        localStorage.removeItem('authData')
        setAuthData({
            isLoggedIn: false,
            userId: '',
            tipoUsuario: '',
            nomeUsuario: '',
            token: '',
        })

        await router.push('/quintana/login')
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
                label: 'Sair',
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
        <Layout style={{ minHeight: '100vh', background: theme.colors.bg, fontFamily: theme.fonts.sans }}>
            <Header style={styles.header}>
                <div style={styles.headerInner}>
                    <Link href={brandHref} style={styles.brand}>
                        <img src="/q3.png" alt="" style={styles.brandImage} />
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
                        menu={{
                            items: userItems,
                            onClick: ({ key }) => {
                                if (key === 'logout') {
                                    handleLogout()
                                }
                            }
                        }}
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
            {IS_WORKSHOP_MODE && (
                <div style={styles.workshopBanner}>
                    <strong>Modo oficina ativo</strong>
                    <span>Dados e fluxos preparados para demonstração pedagógica. Remoções destrutivas ficam bloqueadas.</span>
                </div>
            )}
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
        height: 60,
        padding: '0 24px',
        background: 'rgba(234, 231, 226, 0.94)',
        borderBottom: `1px solid ${theme.colors.rule}`,
        backdropFilter: 'blur(12px)'
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
        gap: 0,
        color: theme.colors.ink,
        textDecoration: 'none',
        flex: '0 0 auto'
    },
    brandImage: {
        width: 76,
        height: 38,
        display: 'block',
        objectFit: 'contain'
    },
    brandText: {
        fontFamily: theme.fonts.serif,
        fontSize: 21,
        fontWeight: 500,
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
        color: theme.colors.inkLight,
        textDecoration: 'none',
        padding: '8px 10px',
        borderRadius: theme.radius.sm,
        lineHeight: 1,
        whiteSpace: 'nowrap',
        fontSize: 14,
        letterSpacing: '0.03em'
    },
    navLinkActive: {
        color: theme.colors.ink,
        background: theme.colors.surface2
    },
    userButton: {
        flex: '0 0 auto',
        borderColor: theme.colors.rule,
        borderRadius: theme.radius.sm,
        color: theme.colors.inkMid,
        background: theme.colors.surface
    },
    workshopBanner: {
        display: 'flex',
        gap: 10,
        alignItems: 'center',
        justifyContent: 'center',
        flexWrap: 'wrap',
        padding: '8px 16px',
        background: theme.colors.successBg,
        borderBottom: `1px solid ${theme.colors.successBorder}`,
        color: theme.colors.inkMid,
        fontSize: 13
    }
}

export default MainLayout
