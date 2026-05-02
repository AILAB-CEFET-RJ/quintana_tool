import { useState } from 'react'
import { Button, Input, Radio, Typography } from 'antd'
import { LockOutlined, MailOutlined, TeamOutlined, UserOutlined } from '@ant-design/icons'
import axios from 'axios'
import router from 'next/router'
import { API_URL } from "@/config/config"
import ErrorAlert from '../../components/errorAlert'
import AuthShell from '@/components/ui/AuthShell'

const Cadastro = () => {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [nomeUsuario, setNomeUsuario] = useState('')
    const [tipoUsuario, setTipoUsuario] = useState('')
    const [errorMessage, setErrorMessage] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)

    const handleCadastro = async () => {
        setErrorMessage('')

        if (!tipoUsuario) {
            setErrorMessage('Selecione se o usuário é professor ou aluno.')
            return
        }

        if (!email || !password || !nomeUsuario) {
            setErrorMessage('Preencha email, nome de usuário e senha.')
            return
        }

        try {
            setIsSubmitting(true)
            await axios.post(`${API_URL}/userRegister`, {
                email,
                password,
                nomeUsuario,
                tipoUsuario
            })
            setEmail('')
            setPassword('')
            setTipoUsuario('')
            setNomeUsuario('')
            router.push('/quintana/login')
        } catch (error) {
            console.error('Erro ao cadastrar usuário:', error)
            if (axios.isAxiosError(error) && !error.response) {
                setErrorMessage('Não foi possível conectar ao backend')
            } else {
                setErrorMessage('Erro ao cadastrar usuário. Verifique os dados e tente novamente.')
            }
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <AuthShell
            title="Criar conta"
            subtitle="Escolha seu perfil para acessar a experiência adequada."
        >
            <div style={{ display: 'grid', gap: 14 }}>
                <Radio.Group
                    value={tipoUsuario}
                    onChange={(event) => setTipoUsuario(event.target.value)}
                    optionType="button"
                    buttonStyle="solid"
                    size="large"
                    style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}
                >
                    <Radio.Button value="aluno" style={{ textAlign: 'center' }}>
                        <UserOutlined /> Aluno
                    </Radio.Button>
                    <Radio.Button value="professor" style={{ textAlign: 'center' }}>
                        <TeamOutlined /> Professor
                    </Radio.Button>
                </Radio.Group>
                <Input
                    size="large"
                    prefix={<MailOutlined />}
                    placeholder="Email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                />
                <Input
                    size="large"
                    prefix={<UserOutlined />}
                    placeholder="Nome de usuário"
                    value={nomeUsuario}
                    onChange={e => setNomeUsuario(e.target.value)}
                />
                <Input.Password
                    size="large"
                    prefix={<LockOutlined />}
                    placeholder="Senha"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    onPressEnter={handleCadastro}
                />
                {errorMessage && <ErrorAlert message={errorMessage} />}
                <Button type="primary" size="large" block onClick={handleCadastro} loading={isSubmitting}>
                    Criar conta
                </Button>
                <Typography.Text style={{ textAlign: 'center', color: '#6b7280' }}>
                    Já possui conta? <a onClick={() => router.push('/quintana/login')}>Entrar</a>.
                </Typography.Text>
            </div>
        </AuthShell>
    )
}

export default Cadastro
