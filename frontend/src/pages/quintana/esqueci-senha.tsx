import { useState } from 'react'
import { Alert, Button, Input, Typography } from 'antd'
import { MailOutlined } from '@ant-design/icons'
import Link from 'next/link'
import { useRouter } from 'next/router'
import axios from 'axios'
import { API_URL } from '@/config/config'
import AuthShell from '@/components/ui/AuthShell'
import ErrorAlert from '@/components/errorAlert'
import { useAuth } from '@/context'
import { authHeaders } from '@/lib/authFetch'

const EsqueciSenha = () => {
    const router = useRouter()
    const { isLoggedIn } = useAuth()
    const [email, setEmail] = useState('')
    const [errorMessage, setErrorMessage] = useState('')
    const [successMessage, setSuccessMessage] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)

    const handleSubmit = async () => {
        setErrorMessage('')
        setSuccessMessage('')

        if (!email) {
            setErrorMessage('Informe o e-mail cadastrado.')
            return
        }

        try {
            setIsSubmitting(true)
            const response = await axios.post(`${API_URL}/password-reset/request`, { email }, {
                headers: authHeaders(),
            })
            setSuccessMessage(response.data?.message || 'Se o e-mail estiver cadastrado, enviaremos instruções para redefinir a senha.')
        } catch (error) {
            console.error('Erro ao solicitar redefinição de senha:', error)
            if (axios.isAxiosError(error) && !error.response) {
                setErrorMessage('Não foi possível conectar ao backend.')
            } else if (axios.isAxiosError(error) && error.response?.data?.error) {
                setErrorMessage(error.response.data.error)
            } else {
                setErrorMessage('Não foi possível processar a solicitação. Tente novamente.')
            }
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <AuthShell
            title="Esqueci minha senha"
            subtitle="Informe seu e-mail para receber as instruções de redefinição."
        >
            <div style={{ display: 'grid', gap: 14 }}>
                {isLoggedIn && (
                    <Alert
                        type="warning"
                        showIcon
                        message="Você já está logado"
                        description="Para redefinir a senha de outra conta, saia da sessão atual primeiro."
                        action={
                            <Button size="small" onClick={() => router.push('/quintana/home')}>
                                Voltar ao painel
                            </Button>
                        }
                    />
                )}
                <Input
                    size="large"
                    prefix={<MailOutlined />}
                    placeholder="Email"
                    value={email}
                    onChange={event => setEmail(event.target.value)}
                    onPressEnter={handleSubmit}
                    disabled={isLoggedIn}
                />
                {errorMessage && <ErrorAlert message={errorMessage} />}
                {successMessage && <Alert type="success" showIcon message={successMessage} />}
                <Button type="primary" size="large" block onClick={handleSubmit} loading={isSubmitting} disabled={isLoggedIn}>
                    Enviar instruções
                </Button>
                <Typography.Text style={{ textAlign: 'center', color: '#6b7280' }}>
                    Lembrou a senha? <Link href="/quintana/login">Entrar</Link>.
                </Typography.Text>
            </div>
        </AuthShell>
    )
}

export default EsqueciSenha
