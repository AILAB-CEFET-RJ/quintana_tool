import type { CSSProperties } from 'react';
import { useState } from 'react';
import { Alert, Button, Form, Input, Space, Typography, message } from 'antd';
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons';
import { useAuth } from '@/context';
import router from 'next/router';
import { API_URL } from '@/config/config';
import PageShell from '@/components/ui/PageShell';
import PageHeader from '@/components/ui/PageHeader';
import SectionPanel from '@/components/ui/SectionPanel';
import { authFetch, authHeaders } from '@/lib/authFetch';

const Tema = () => {
    const [salvarDesabilitado, setSalvarDesabilitado] = useState(true);
    const [salvando, setSalvando] = useState(false);
    const [preview, setPreview] = useState({ nomeTema: '', descricaoTema: '' });
    const [form] = Form.useForm();
    const { nomeUsuario } = useAuth();

    const handleCadastroTema = async (values: any) => {
        try {
            setSalvando(true);

            const response = await authFetch(`${API_URL}/temas`, {
                method: 'POST',
                headers: authHeaders({
                    'Content-Type': 'application/json',
                }),
                body: JSON.stringify({
                    nome_professor: nomeUsuario,
                    tema: values.nomeTema,
                    descricao: values.descricaoTema,
                }),
            });

            if (response.ok) {
                message.success('Tema cadastrado com sucesso!');
                form.resetFields();
                router.push('/quintana/home');
            } else {
                message.error('Erro ao cadastrar o tema.');
            }
        } catch (error) {
            console.error('Erro ao cadastrar o tema:', error);
            message.error('Erro ao cadastrar o tema. Por favor, tente novamente.');
        } finally {
            setSalvando(false);
        }
    };

    const handleFormChange = () => {
        const { nomeTema, descricaoTema } = form.getFieldsValue();

        setPreview({
            nomeTema: nomeTema || '',
            descricaoTema: descricaoTema || '',
        });
        setSalvarDesabilitado(!nomeTema || !descricaoTema);
    };

    return (
        <PageShell maxWidth={980}>
            <PageHeader
                title="Criar novo tema"
                description="Cadastre a proposta que ficará disponível para os estudantes enviarem redações."
                actions={
                    <Button icon={<ArrowLeftOutlined />} onClick={() => router.push('/quintana/home')}>
                        Voltar
                    </Button>
                }
            />

            <div style={styles.grid}>
                <SectionPanel
                    title="Dados da proposta"
                    description="Use um título claro e uma descrição suficiente para orientar a produção textual."
                >
                    <Form
                        form={form}
                        layout="vertical"
                        onFinish={handleCadastroTema}
                        onValuesChange={handleFormChange}
                        requiredMark={false}
                    >
                        <Form.Item
                            name="nomeTema"
                            label="Tema"
                            rules={[{ required: true, message: 'Informe o tema da redação.' }]}
                        >
                            <Input
                                size="large"
                                placeholder="Ex.: Desafios para combater a desinformação no Brasil"
                                maxLength={140}
                                showCount
                            />
                        </Form.Item>

                        <Form.Item
                            name="descricaoTema"
                            label="Texto de apoio e orientações"
                            rules={[{ required: true, message: 'Informe a descrição do tema.' }]}
                        >
                            <Input.TextArea
                                rows={14}
                                placeholder="Descreva a proposta, o recorte temático e, se necessário, instruções para a produção da redação."
                                showCount
                            />
                        </Form.Item>

                        <Alert
                            type="info"
                            showIcon
                            style={{ marginBottom: 16 }}
                            message="Após salvar, o tema aparece na aba Temas e pode ser usado pelos estudantes."
                        />

                        <Form.Item style={{ marginBottom: 0 }}>
                            <Space style={styles.actions} wrap>
                                <Button onClick={() => router.push('/quintana/home')}>
                                    Cancelar
                                </Button>
                                <Button
                                    type="primary"
                                    htmlType="submit"
                                    icon={<SaveOutlined />}
                                    disabled={salvarDesabilitado}
                                    loading={salvando}
                                >
                                    Salvar tema
                                </Button>
                            </Space>
                        </Form.Item>
                    </Form>
                </SectionPanel>

                <SectionPanel
                    title="Prévia para o estudante"
                    description="Esta é a forma como o tema será apresentado antes da escrita."
                >
                    <div style={styles.preview}>
                        <Typography.Text style={styles.previewLabel}>
                            Tema da redação
                        </Typography.Text>
                        <Typography.Title level={3} style={styles.previewTitle}>
                            {preview.nomeTema.trim() || 'Título do tema'}
                        </Typography.Title>
                        <Typography.Paragraph style={styles.previewText}>
                            {preview.descricaoTema.trim() || 'A descrição cadastrada aparecerá aqui para orientar a produção da redação.'}
                        </Typography.Paragraph>
                    </div>
                </SectionPanel>
            </div>
        </PageShell>
    );
};

const styles: Record<string, CSSProperties> = {
    grid: {
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: 16,
        alignItems: 'start',
    },
    actions: {
        display: 'flex',
        justifyContent: 'flex-end',
        width: '100%',
    },
    preview: {
        border: '1px solid #e5e7eb',
        borderRadius: 8,
        background: '#f9fafb',
        padding: 18,
        minHeight: 260,
    },
    previewLabel: {
        display: 'block',
        color: '#6b7280',
        fontSize: 12,
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: 0,
        marginBottom: 8,
    },
    previewTitle: {
        marginTop: 0,
        marginBottom: 12,
        color: '#111827',
    },
    previewText: {
        color: '#4b5563',
        whiteSpace: 'pre-line',
        marginBottom: 0,
    },
};

export default Tema;
