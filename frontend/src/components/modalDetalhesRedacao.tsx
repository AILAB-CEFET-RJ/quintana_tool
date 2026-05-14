import { Modal, Input, Button, message, Collapse, Row, Col, Card, Statistic, Tabs } from 'antd';
import { EditOutlined } from '@ant-design/icons';
import { useState, useEffect } from 'react';
import { Redacao, Tema } from '@/pages/quintana/home';
import { useAuth } from '@/context';
import TextArea from "antd/lib/input/TextArea";
import { API_URL } from "@/config/config";
import ReactMarkdown from 'react-markdown';
import CompetencyRadar from './studentInsights/CompetencyRadar';
import StudyPriorityCard from './studentInsights/StudyPriorityCard';
import CompetencyFeedbackMap from './studentInsights/CompetencyFeedbackMap';
import RewriteChecklist from './studentInsights/RewriteChecklist';
import VersionComparison from './studentInsights/VersionComparison';
import router from 'next/router';
import { authFetch, authHeaders } from '@/lib/authFetch';


interface RedacaoDetalhes {
    open: boolean;
    onCancel: () => void;
    redacao: Redacao | null;
    onRedacaoEditado: (redacaoEditado: Redacao) => void;
}

const ModalDetalhesRedacao: React.FC<RedacaoDetalhes> = ({ open, onCancel, redacao, onRedacaoEditado }) => {

    const [notaComp1Editada, setnotaComp1Editada] = useState<string>('');
    const [notaComp2Editada, setnotaComp2Editada] = useState<string>('');
    const [notaComp3Editada, setnotaComp3Editada] = useState<string>('');
    const [notaComp4Editada, setnotaComp4Editada] = useState<string>('');
    const [notaComp5Editada, setnotaComp5Editada] = useState<string>('');
    const [feedbackProfessorEditada, setFeedbackProfessorEditada] = useState<string>('');
    const [versions, setVersions] = useState<Redacao[]>([]);
    const { tipoUsuario } = useAuth();


    useEffect(() => {
        setnotaComp1Editada(`${redacao?.nota_competencia_1_professor ?? ''}`)
        setnotaComp2Editada(`${redacao?.nota_competencia_2_professor ?? ''}`)
        setnotaComp3Editada(`${redacao?.nota_competencia_3_professor ?? ''}`)
        setnotaComp4Editada(`${redacao?.nota_competencia_4_professor ?? ''}`)
        setnotaComp5Editada(`${redacao?.nota_competencia_5_professor ?? ''}`)
        setFeedbackProfessorEditada(redacao?.feedback_professor ?? '')
    }, [redacao])

    useEffect(() => {
        const fetchVersions = async () => {
            if (!redacao?._id || !open || tipoUsuario !== 'aluno') {
                setVersions([]);
                return;
            }

            try {
                const response = await authFetch(`${API_URL}/redacoes/${redacao._id}/versions`);
                if (response.ok) {
                    const data = await response.json();
                    setVersions(data);
                }
            } catch (error) {
                console.error('Erro ao buscar versões da redação:', error);
            }
        };

        fetchVersions();
    }, [redacao, open, tipoUsuario])


    const { Panel } = Collapse;

    const handleEditarRedacao = async () => {
        try {
            const gradesEdited = notaComp1Editada !== '' ||
                notaComp2Editada !== '' ||
                notaComp3Editada !== '' ||
                notaComp4Editada !== '' ||
                notaComp5Editada !== '' ||
                feedbackProfessorEditada !== ''


            if (redacao && redacao.nota_professor && gradesEdited) {
                message.error('Redação já foi corrigida!');
                return
            }
            if (redacao && gradesEdited) {
                const response = await authFetch(`${API_URL}/redacoes/${redacao._id}`, {
                    method: 'PUT',
                    headers: authHeaders({
                        'Content-Type': 'application/json'
                    }),
                    body: JSON.stringify({
                        nota_competencia_1_professor: notaComp1Editada !== '' ? notaComp1Editada : 0,
                        nota_competencia_2_professor: notaComp2Editada !== '' ? notaComp2Editada : 0,
                        nota_competencia_3_professor: notaComp3Editada !== '' ? notaComp3Editada : 0,
                        nota_competencia_4_professor: notaComp4Editada !== '' ? notaComp4Editada : 0,
                        nota_competencia_5_professor: notaComp5Editada !== '' ? notaComp5Editada : 0,
                        feedback_professor: feedbackProfessorEditada !== '' ? feedbackProfessorEditada : "",
                        //nome_professor: redacao.tema.nome_professor todo: add nome professor
                    })
                });
                if (response.ok) {
                    message.success('Redacao atualizado com sucesso!');
                    onCancel();
                    onRedacaoEditado({
                        ...redacao,
                    });
                }
            }
        } catch (error) {
            console.error('Erro ao atualizar a redacao:', error);
            message.error('Erro ao atualizar a redacao. Por favor, tente novamente.');
        }
    };

    const inputStyle = {
        marginBottom: '10px',
        color: '#4a4a4a'
    };

    const labelStyle = {
        marginBottom: '10px',
    }

    const renderFeedback = () => (
        <div style={{ ...inputStyle, overflowY: 'auto', maxHeight: '420px' }}>
            <ReactMarkdown>
                {(redacao?.feedback_llm || '')
                    .split('\n')
                    .map((linha) => linha.replace(/^\s{8}/, '').replace(/^\s{4}/, ''))
                    .join('\n')
                    .replace(/\\n/g, '\n')
                    .trim()
                }
            </ReactMarkdown>
        </div>
    )

    const handleRewrite = () => {
        if (!redacao) return;
        onCancel();
        router.push(`/quintana/redacao?id=${redacao.id_tema}&rewriteOf=${redacao._id}`);
    }

    return (
        <Modal
            title={tipoUsuario === 'aluno' ? 'Detalhes da redação' : 'Editar redação'}
            open={open}
            onCancel={onCancel}
            footer={null}
            width="80vw"
            style={{ height: '80vh', top: '10px' }}
        >

            {redacao && tipoUsuario === 'aluno' ? (
                <div>
                    <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
                        <Col xs={24} md={12}>
                            <Card size="small" title="Redação" style={{ height: '100%' }}>
                                <strong>{redacao.titulo?.trim() || 'Sem título'}</strong>
                                <p style={{ margin: '6px 0 0', color: '#6b7280' }}>
                                    {redacao.student_name || 'Aluno'} · Versão {redacao.version_number || 1}
                                </p>
                            </Card>
                        </Col>
                        <Col xs={24} sm={12} md={6}>
                            <Card size="small">
                                <Statistic title="Nota IA" value={Math.round(Number(redacao.nota_total) || 0)} suffix="/1000" />
                            </Card>
                        </Col>
                        <Col xs={24} sm={12} md={6}>
                            <Card size="small">
                                <Statistic title="Nota professor" value={redacao.nota_professor ? Math.round(Number(redacao.nota_professor)) : '-'} />
                            </Card>
                        </Col>
                    </Row>

                    <Tabs
                        defaultActiveKey="resumo"
                        items={[
                            {
                                key: 'resumo',
                                label: 'Resumo',
                                children: (
                                    <>
                                        <CompetencyRadar redacao={redacao} />
                                        <StudyPriorityCard redacao={redacao} />
                                    </>
                                )
                            },
                            {
                                key: 'texto',
                                label: 'Texto',
                                children: <TextArea rows={20} style={inputStyle} value={redacao.texto} disabled />
                            },
                            {
                                key: 'notas',
                                label: 'Notas',
                                children: (
                                    <Collapse style={labelStyle} defaultActiveKey={['modelo']}>
                                        <Panel header="Notas IA por competência" key="modelo">
                                            <label style={labelStyle}><b>Nota IA C1 - Domínio da modalidade escrita formal </b></label>
                                            <Input style={inputStyle} value={redacao.nota_competencia_1_model} disabled />
                                            <label style={labelStyle}><b>Nota IA C2 - Compreender a proposta e aplicar conceitos das várias áreas de conhecimento para desenvolver o texto dissertativo-argumentativo em prosa</b></label>
                                            <Input style={inputStyle} value={redacao.nota_competencia_2_model} disabled />
                                            <label style={labelStyle}><b>Nota IA C3 - Selecionar, relacionar, organizar e interpretar informações em defesa de um ponto de vista</b></label>
                                            <Input style={inputStyle} value={redacao.nota_competencia_3_model} disabled />
                                            <label style={labelStyle}><b>Nota IA C4 - Conhecimento dos mecanismos linguísticos necessários para a construção da argumentação</b></label>
                                            <Input style={inputStyle} value={redacao.nota_competencia_4_model} disabled />
                                            <label style={labelStyle}><b>Nota IA C5 - Proposta de intervenção com respeito aos direitos humanos</b></label>
                                            <Input style={inputStyle} value={redacao.nota_competencia_5_model} disabled />
                                        </Panel>
                                        <Panel header="Notas professor por competência" key="professor">
                                            <label style={labelStyle}><b>Nota professor C1 - Domínio da modalidade escrita formal</b></label>
                                            <Input style={inputStyle} value={notaComp1Editada} disabled />
                                            <label style={labelStyle}><b>Nota professor C2 - Compreender a proposta e aplicar conceitos das várias áreas de conhecimento para desenvolver o texto dissertativo-argumentativo em prosa</b></label>
                                            <Input style={inputStyle} value={notaComp2Editada} disabled />
                                            <label style={labelStyle}><b>Nota professor C3 - Selecionar, relacionar, organizar e interpretar informações em defesa de um ponto de vista</b></label>
                                            <Input style={inputStyle} value={notaComp3Editada} disabled />
                                            <label style={labelStyle}><b>Nota professor C4 - Conhecimento dos mecanismos linguísticos necessários para a construção da argumentação</b></label>
                                            <Input style={inputStyle} value={notaComp4Editada} disabled />
                                            <label style={labelStyle}><b>Nota professor C5 - Proposta de intervenção com respeito aos direitos humanos</b></label>
                                            <Input style={inputStyle} value={notaComp5Editada} disabled />
                                        </Panel>
                                    </Collapse>
                                )
                            },
                            {
                                key: 'plano',
                                label: 'Plano de ação',
                                children: (
                                    <div style={{ display: 'grid', gap: 16 }}>
                                        <CompetencyFeedbackMap redacao={redacao} />
                                        <RewriteChecklist redacao={redacao} />
                                    </div>
                                )
                            },
                            {
                                key: 'versoes',
                                label: 'Versões',
                                children: <VersionComparison versions={versions} />
                            },
                            {
                                key: 'feedback',
                                label: 'Feedback',
                                children: (
                                    <Collapse defaultActiveKey={['llm']}>
                                        <Panel header="Feedback IA" key="llm">{renderFeedback()}</Panel>
                                        <Panel header="Feedback professor" key="professor">
                                            <TextArea rows={14} style={inputStyle} value={feedbackProfessorEditada} disabled />
                                        </Panel>
                                    </Collapse>
                                )
                            }
                        ]}
                    />

                    <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 16 }}>
                        <Button onClick={onCancel}>OK</Button>
                        <Button type="primary" icon={<EditOutlined />} onClick={handleRewrite}>Reescrever</Button>
                    </div>
                </div>
            ) : redacao && ( //tipo professor
                <div>
                    <label style={labelStyle}><b>Título</b>:</label>
                    <Input style={inputStyle} value={redacao.titulo} disabled />
                    <label style={labelStyle}><b>Texto</b>:</label>
                    <TextArea rows={20} style={inputStyle} value={redacao.texto}
                        disabled />
                    <Collapse style={labelStyle}>
                        <Panel header="Notas professor por competência" key="1">
                            <label style={labelStyle}><b>Nota professor C1 - Domínio da modalidade escrita formal</b></label>
                            <Input style={inputStyle} value={notaComp1Editada}
                                onChange={(e) => setnotaComp1Editada(e.target.value)} />
                            <label style={labelStyle}><b>Nota professor C2 - Compreender a proposta e aplicar conceitos das várias áreas de conhecimento para desenvolver o texto dissertativo-argumentativo em prosa</b></label>
                            <Input style={inputStyle} value={notaComp2Editada}
                                onChange={(e) => setnotaComp2Editada(e.target.value)} />
                            <label style={labelStyle}><b>Nota professor C3 - Selecionar, relacionar, organizar e interpretar informações em defesa de um ponto de vista</b></label>
                            <Input style={inputStyle} value={notaComp3Editada}
                                onChange={(e) => setnotaComp3Editada(e.target.value)} />
                            <label style={labelStyle}><b>Nota professor C4 - Conhecimento dos mecanismos linguísticos necessários para a construção da argumentação</b></label>
                            <Input style={inputStyle} value={notaComp4Editada}
                                onChange={(e) => setnotaComp4Editada(e.target.value)} />
                            <label style={labelStyle}><b>Nota professor C5 - Proposta de intervenção com respeito aos direitos humanos</b></label>
                            <Input style={inputStyle} value={notaComp5Editada}
                                onChange={(e) => setnotaComp5Editada(e.target.value)} />
                        </Panel>
                        <Panel header="Feedback professor" key="2">
                            <TextArea rows={20} style={inputStyle} value={feedbackProfessorEditada} onChange={(e) => setFeedbackProfessorEditada(e.target.value)} />
                        </Panel>
                        <Panel header="Notas IA por competência" key="3">
                            <label style={labelStyle}><b>Nota IA C1 - Domínio da modalidade escrita formal </b></label>
                            <Input style={inputStyle} value={redacao.nota_competencia_1_model}
                                disabled />
                            <label style={labelStyle}><b>Nota IA C2 - Compreender a proposta e aplicar conceitos das várias áreas de conhecimento para desenvolver o texto dissertativo-argumentativo em prosa</b></label>
                            <Input style={inputStyle} value={redacao.nota_competencia_2_model}
                                disabled />
                            <label style={labelStyle}><b>Nota IA C3 - Selecionar, relacionar, organizar e interpretar informações em defesa de um ponto de vista</b></label>
                            <Input style={inputStyle} value={redacao.nota_competencia_3_model}
                                disabled />
                            <label style={labelStyle}><b>Nota IA C4 - Conhecimento dos mecanismos linguísticos necessários para a construção da argumentação</b></label>
                            <Input style={inputStyle} value={redacao.nota_competencia_4_model}
                                disabled />
                            <label style={labelStyle}><b>Nota IA C5 - Proposta de intervenção com respeito aos direitos humanos</b></label>
                            <Input style={inputStyle} value={redacao.nota_competencia_5_model}
                                disabled />
                        </Panel>
                        <Panel header="Feedback IA" key="4">
                            <div style={{ ...inputStyle, overflowY: 'auto', maxHeight: '400px' }}>
                                <ReactMarkdown>
                                    {(redacao?.feedback_llm || '')
                                        .split('\n')
                                        .map((linha) => linha.replace(/^\s{8}/, '').replace(/^\s{4}/, ''))
                                        .join('\n')
                                        .replace(/\\n/g, '\n')
                                        .trim()
                                    }
                                </ReactMarkdown>

                            </div>
                        </Panel>
                    </Collapse>

                    <Button style={{ marginTop: '1vw' }} onClick={handleEditarRedacao}>Editar</Button>
                </div>
            )}
        </Modal>
    );
};

export default ModalDetalhesRedacao;
