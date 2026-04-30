import { useState } from 'react';
import { Form, Input, Button, message } from 'antd';
import { useAuth } from '@/context';
import router from 'next/router';
import {API_URL} from "@/config/config";
import PageShell from '@/components/ui/PageShell';
import PageHeader from '@/components/ui/PageHeader';
import SectionPanel from '@/components/ui/SectionPanel';

const Tema = () => {
    const [salvarDesabilitado, setSalvarDesabilitado] = useState(true);
    const [form] = Form.useForm(); 
    const { nomeUsuario } = useAuth();

    const handleCadastroTema = async (values: any) => {
        try {
            const response = await fetch(`${API_URL}/temas`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    nome_professor: nomeUsuario,
                    tema: values.nomeTema,
                    descricao: values.descricaoTema,
                }),
            });

            if (response.ok) {
                message.success('Tema cadastrado com sucesso!');
                form.resetFields(); 
                router.push('/quintana/home')
            } else {
                message.error('Erro ao cadastrar o tema.');
            }
        } catch (error) {
            console.error('Erro ao cadastrar o tema:', error);
            message.error('Erro ao cadastrar o tema. Por favor, tente novamente.');
        }
    };

    const handleFormChange = () => {
        const { nomeTema, descricaoTema } = form.getFieldsValue();
        setSalvarDesabilitado(!nomeTema || !descricaoTema);
    };

    return (
        <PageShell maxWidth={720}>
            <PageHeader
                title="Criar novo tema"
                description="Cadastre a proposta que ficará disponível para os estudantes enviarem redações."
            />
            <SectionPanel>
                <Form form={form} onFinish={handleCadastroTema} onValuesChange={handleFormChange}>
                    <Form.Item name="nomeTema" label="Nome do Tema" rules={[{ required: true, message: 'Por favor, insira o nome do tema!' }]}>
                        <Input size="large" />
                    </Form.Item>
                    <Form.Item name="descricaoTema" label="Descrição do Tema" rules={[{ required: true, message: 'Por favor, insira a descrição do tema!' }]}>
                        <Input.TextArea rows={12}/>
                    </Form.Item>
                    <Form.Item>
                        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                            <Button type="primary" htmlType="submit" disabled={salvarDesabilitado}>
                                Salvar
                            </Button>
                        </div>
                    </Form.Item>
                </Form>
            </SectionPanel>
        </PageShell>
    );
};

export default Tema;
