import { useState } from 'react';
import { Button, Checkbox, Input, Layout } from 'antd';
import axios from 'axios';
import router from 'next/router';
import { API_URL } from "@/config/config";

const { Content } = Layout;

const Cadastro = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [nomeUsuario, setNomeUsuario] = useState('');
    const [isProfessor, setIsProfessor] = useState(false);
    const [isAluno, setIsAluno] = useState(false);
    const [tipoUsuario, setTipoUsuario] = useState('');


    const handleCheckboxChange = (type: string) => {
        console.log('type', type)
        if (type === 'professor') {
            setIsProfessor(!isProfessor);
            setIsAluno(false);
            setTipoUsuario(type);
        } else if (type === 'aluno') {
            setIsAluno(!isAluno);
            setIsProfessor(false);
            setTipoUsuario(type);
        }
    };

    const handleCadastro = async () => {
        try {
            await axios.post(`${API_URL}/userRegister`, {
                email,
                password,
                nomeUsuario,
                tipoUsuario
            });
            console.log('Usuário cadastrado com sucesso!');
            setEmail('');
            setPassword('');
            setTipoUsuario('');
            setNomeUsuario('');
            router.push('/quintana/login');
        } catch (error) {
            console.error('Erro ao cadastrar usuário:', error);
        }
    }

    const isDisabled = !isProfessor && !isAluno;

    return (
        <Layout style={{ minHeight: '50vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <Content style={{ padding: '20px', borderRadius: '8px', boxShadow: '0 4px 8px rgba(0,0,0,0.1)', width: '300px' }}>
                <div style={{ marginBottom: '20px', textAlign: 'center' }}>
                    <h2>Cadastro</h2>
                </div>
                <div style={{ marginBottom: '20px' }}>
                    <Checkbox
                        style={{ marginLeft: '50px' }}
                        checked={isProfessor}
                        onChange={() => handleCheckboxChange('professor')}
                    >
                        Professor
                    </Checkbox>
                    <Checkbox
                        checked={isAluno}
                        onChange={() => handleCheckboxChange('aluno')}
                    >
                        Aluno
                    </Checkbox>
                </div>
                <div style={{ marginBottom: '20px' }}>
                    <Input
                        placeholder="Email"
                        value={email}
                        onChange={e => setEmail(e.target.value)}
                        disabled={isDisabled}
                    />
                </div>
                <div style={{ marginBottom: '20px' }}>
                    <Input
                        placeholder="Nome de usuário"
                        value={nomeUsuario}
                        onChange={e => setNomeUsuario(e.target.value)}
                        disabled={isDisabled}
                    />
                </div>
                <div style={{ marginBottom: '20px' }}>
                    <Input.Password
                        placeholder="Senha"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        disabled={isDisabled}
                    />
                </div>
                <div style={{ textAlign: 'center' }}>
                    <Button onClick={handleCadastro} type="primary">Entrar</Button>
                </div>
            </Content>
        </Layout>
    );
};

export default Cadastro;