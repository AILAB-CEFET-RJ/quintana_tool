import { ReactNode, useState } from 'react';
import { Layout, Menu, Dropdown, Space, Tooltip } from 'antd';
import { CaretUpOutlined, CaretDownOutlined } from '@ant-design/icons';
import Link from 'next/link';
import { useAuth } from '../context';

const { Header, Content, Footer } = Layout;

interface MainLayoutProps {
    children: ReactNode;
}

const MainLayout = ({ children }: MainLayoutProps) => {
    const { isLoggedIn, tipoUsuario, nomeUsuario } = useAuth();
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const handleLogout = () => {
        setAuthData({
            isLoggedIn: false,
            tipoUsuario: '',
            nomeUsuario: '',
        });

        window.location.href = '/quintana/login';
    }

    const items = isLoggedIn
        ? [
            {
                key: '1',
                label: <span>Seja bem-vindo, {nomeUsuario}</span>,
            },
            {
                key: '2',
                label: (
                    <span onClick={handleLogout} style={{ cursor: 'pointer', color: '#1677ff' }}>
                        Sair
                    </span>
                ),
            },
        ]
        : [
            {
                key: '1',
                label: <Link href="/quintana/login">Entrar</Link>,
            },
        ];


    const handleMenuClick = () => {
        setIsMenuOpen(!isMenuOpen);
    };

    const { setAuthData } = useAuth();



    return (
        <Layout style={{ minHeight: "100vh" }}>
            <Header style={{ position: 'sticky', top: 0, zIndex: 1, width: '100%' }}>
                <Menu
                    theme="dark"
                    mode="horizontal"
                    defaultSelectedKeys={['2']}
                >
                    <Menu.Item>
                        <Link href="/quintana">
                            Quintana
                        </Link>
                    </Menu.Item>
                    {isLoggedIn === false ? (
                        <Tooltip title="Você precisa fazer login para acessar essa página">
                            <div onClick={(e) => e.preventDefault()}>
                                <Menu.Item disabled>
                                    Home
                                </Menu.Item>
                            </div>
                        </Tooltip>
                    ) : (
                        <Menu.Item>
                            <Link href="/quintana/home">
                                Home
                            </Link>
                        </Menu.Item>
                    )}
                    <Menu.Item>
                        <Link href="/quintana/competencias">
                            Competências
                        </Link>
                    </Menu.Item>
                    <Menu.Item>
                        <Link href="/quintana/sobre">
                            Sobre
                        </Link>
                    </Menu.Item>
                    <Menu.Item style={{ marginLeft: isLoggedIn ? '720px' : '830px' }}>
                        <Dropdown
                            menu={{ items }}
                            onOpenChange={handleMenuClick}
                            overlayStyle={{ marginTop: '8px' }}
                        >
                            <Space onClick={handleMenuClick}>
                                {isLoggedIn === true ? `${nomeUsuario}` : 'Login'}
                                {isMenuOpen ? <CaretDownOutlined /> : <CaretUpOutlined />}
                            </Space>
                        </Dropdown>
                    </Menu.Item>
                </Menu>
            </Header>
            <Content>{children}</Content>
        </Layout>
    );
};

export default MainLayout;