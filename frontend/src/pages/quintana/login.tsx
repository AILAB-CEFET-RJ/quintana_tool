import { useState } from 'react';
import { Button, Input, Layout, Typography } from 'antd';
import Link from 'next/link';
import axios from 'axios';
import { useAuth } from '../../context';
import router from 'next/router';
import ErrorAlert from '../../components/errorAlert';
import { API_URL } from "@/config/config";

const { Content } = Layout;

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const { setAuthData } = useAuth();

    const handleLogin = async () => {
        try {
            const response = await axios.post(`${API_URL}/userLogin`, {
                email,
                password,
            });

            const data = response.data;

            const auth = {
                isLoggedIn: true,
                tipoUsuario: data.tipoUsuario,
                nomeUsuario: data.nomeUsuario,
            };

            // Salvar no localStorage
            localStorage.setItem('authData', JSON.stringify(auth));

            // Salvar no context também
            setAuthData(auth);

            router.push('/quintana/home');
        } catch (error) {
            console.error('Erro ao fazer login:', error);
            setErrorMessage('E-mail ou senha inválidos.');
        }
    };


    return (
        <Layout style={{ minHeight: '50vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <title>Login</title>
            <Content style={{ padding: '20px', borderRadius: '8px', boxShadow: '0 4px 8px rgba(0,0,0,0.1)', width: '300px' }}>
                <div style={{ marginBottom: '20px', textAlign: 'center' }}>
                    <h2>Login</h2>
                </div>
                <div style={{ marginBottom: '20px' }}>
                    <Input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
                </div>
                <div style={{ marginBottom: '20px' }}>
                    <Input.Password placeholder="Senha" value={password} onChange={e => setPassword(e.target.value)} />
                </div>
                {errorMessage &&
                    <div style={{ marginBottom: '10px' }}>
                        <ErrorAlert message={errorMessage} />
                    </div>
                }
                <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                    <Button type="primary" onClick={handleLogin}>Entrar</Button>
                </div>
                <div style={{ textAlign: 'center' }}>
                    <Typography.Text>Não possui uma conta? Cadastre-se <Link href="/quintana/cadastro">aqui</Link>.</Typography.Text>
                </div>
            </Content>
        </Layout>
    );
};


export default Login;