import { useState } from 'react'
import { Button, Input, Typography } from 'antd'
import { LockOutlined, MailOutlined } from '@ant-design/icons'
import Link from 'next/link'
import axios from 'axios'
import { useAuth } from '../../context'
import router from 'next/router'
import ErrorAlert from '../../components/errorAlert'
import { API_URL } from "@/config/config"
import AuthShell from '@/components/ui/AuthShell'

const Login = () => {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [errorMessage, setErrorMessage] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)
    const { setAuthData } = useAuth()

    const handleLogin = async () => {
        setErrorMessage('')

        if (!email || !password) {
            setErrorMessage('Preencha email e senha.')
            return
        }

        try {
            setIsSubmitting(true)
            const response = await axios.post(`${API_URL}/userLogin`, {
                email,
                password,
            })

            const data = response.data

            const auth = {
                isLoggedIn: true,
                userId: data.userId,
                tipoUsuario: data.tipoUsuario,
                nomeUsuario: data.nomeUsuario,
                token: data.token,
            }

            localStorage.setItem('authData', JSON.stringify(auth))
            setAuthData(auth)

            router.push('/quintana/home')
        } catch (error) {
            console.error('Erro ao fazer login:', error)
            if (axios.isAxiosError(error) && !error.response) {
                setErrorMessage('Não foi possível conectar ao backend')
            } else {
                setErrorMessage('E-mail ou senha inválidos.')
            }
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <AuthShell
            title="Entrar"
            subtitle="Acesse seu painel para acompanhar redações, competências e progresso."
        >
            <div style={{ display: 'grid', gap: 14 }}>
                <Input
                    size="large"
                    prefix={<MailOutlined />}
                    placeholder="Email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                />
                <Input.Password
                    size="large"
                    prefix={<LockOutlined />}
                    placeholder="Senha"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    onPressEnter={handleLogin}
                />
                {errorMessage && <ErrorAlert message={errorMessage} />}
                <Button type="primary" size="large" block onClick={handleLogin} loading={isSubmitting}>
                    Entrar
                </Button>
                <Typography.Text style={{ textAlign: 'center', color: '#6b7280' }}>
                    <Link href="/quintana/esqueci-senha">Esqueci minha senha</Link>
                </Typography.Text>
                <Typography.Text style={{ textAlign: 'center', color: '#6b7280' }}>
                    Não possui uma conta? <Link href="/quintana/cadastro">Cadastre-se</Link>.
                </Typography.Text>
            </div>
        </AuthShell>
    )
}

export default Login
