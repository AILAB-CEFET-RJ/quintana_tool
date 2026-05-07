import { useState } from 'react'
import { Alert, Button, Input, Typography } from 'antd'
import { LockOutlined } from '@ant-design/icons'
import Link from 'next/link'
import { useRouter } from 'next/router'
import axios from 'axios'
import { API_URL } from '@/config/config'
import AuthShell from '@/components/ui/AuthShell'
import ErrorAlert from '@/components/errorAlert'
import { useAuth } from '@/context'

const RedefinirSenha = () => {
    const router = useRouter()
    const { isLoggedIn } = useAuth()
    const [password, setPassword] = useState('')
    const [passwordConfirmation, setPasswordConfirmation] = useState('')
    const [errorMessage, setErrorMessage] = useState('')
    const [successMessage, setSuccessMessage] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)

    const token = typeof router.query.token === 'string' ? router.query.token : ''

    const handleSubmit = async () => {
        setErrorMessage('')
        setSuccessMessage('')

        if (isLoggedIn) {
            setErrorMessage('Saia da conta atual antes de usar um link de redefinição de senha.')
            return
        }

        if (!token) {
            setErrorMessage('Link de redefinição inválido ou incompleto.')
            return
        }

        if (!password || !passwordConfirmation) {
            setErrorMessage('Preencha e confirme a nova senha.')
            return
        }

        if (password.length < 8) {
            setErrorMessage('A nova senha deve ter pelo menos 8 caracteres.')
            return
        }

        if (password !== passwordConfirmation) {
            setErrorMessage('A confirmação da senha não confere.')
            return
        }

        try {
            setIsSubmitting(true)
            const response = await axios.post(`${API_URL}/password-reset/confirm`, {
                token,
                new_password: password,
            })
            setSuccessMessage(response.data?.message || 'Senha redefinida com sucesso.')
            setPassword('')
            setPasswordConfirmation('')

            setTimeout(() => {
                router.push('/quintana/login')
            }, 1400)
        } catch (error) {
            console.error('Erro ao redefinir senha:', error)
            if (axios.isAxiosError(error) && !error.response) {
                setErrorMessage('Não foi possível conectar ao backend.')
            } else if (axios.isAxiosError(error) && error.response?.data?.error) {
                setErrorMessage(error.response.data.error)
            } else {
                setErrorMessage('Não foi possível redefinir a senha. Solicite um novo link.')
            }
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <AuthShell
            title="Redefinir senha"
            subtitle="Escolha uma nova senha para voltar a acessar sua conta."
        >
            <div style={{ display: 'grid', gap: 14 }}>
                {!token && (
                    <Alert
                        type="warning"
                        showIcon
                        message="Link inválido"
                        description="Solicite um novo link de redefinição de senha."
                    />
                )}
                {isLoggedIn && (
                    <Alert
                        type="warning"
                        showIcon
                        message="Você já está logado"
                        description="Saia da sessão atual antes de usar um link de redefinição."
                        action={
                            <Button size="small" onClick={() => router.push('/quintana/home')}>
                                Voltar ao painel
                            </Button>
                        }
                    />
                )}
                <Input.Password
                    size="large"
                    prefix={<LockOutlined />}
                    placeholder="Nova senha"
                    value={password}
                    onChange={event => setPassword(event.target.value)}
                    disabled={!token || isLoggedIn}
                />
                <Input.Password
                    size="large"
                    prefix={<LockOutlined />}
                    placeholder="Confirmar nova senha"
                    value={passwordConfirmation}
                    onChange={event => setPasswordConfirmation(event.target.value)}
                    onPressEnter={handleSubmit}
                    disabled={!token || isLoggedIn}
                />
                {errorMessage && <ErrorAlert message={errorMessage} />}
                {successMessage && <Alert type="success" showIcon message={successMessage} />}
                <Button
                    type="primary"
                    size="large"
                    block
                    onClick={handleSubmit}
                    loading={isSubmitting}
                    disabled={!token || isLoggedIn}
                >
                    Redefinir senha
                </Button>
                <Typography.Text style={{ textAlign: 'center', color: '#6b7280' }}>
                    <Link href="/quintana/esqueci-senha">Solicitar novo link</Link>
                </Typography.Text>
            </div>
        </AuthShell>
    )
}

export default RedefinirSenha
