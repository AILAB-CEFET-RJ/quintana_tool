import { Modal, Input, Button, message, Collapse, Row, Col, Card, Statistic, Tabs, Alert, Space, Tag } from 'antd';
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
    const [reviewComment, setReviewComment] = useState<string>('');
    const [versions, setVersions] = useState<Redacao[]>([]);
    const { tipoUsuario } = useAuth();


    useEffect(() => {
        setnotaComp1Editada(`${redacao?.nota_competencia_1_professor ?? ''}`)
        setnotaComp2Editada(`${redacao?.nota_competencia_2_professor ?? ''}`)
        setnotaComp3Editada(`${redacao?.nota_competencia_3_professor ?? ''}`)
        setnotaComp4Editada(`${redacao?.nota_competencia_4_professor ?? ''}`)
        setnotaComp5Editada(`${redacao?.nota_competencia_5_professor ?? ''}`)
        setFeedbackProfessorEditada(redacao?.feedback_professor ?? '')
        setReviewComment(redacao?.teacher_review?.comment ?? '')
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

    const reviewStatusLabel: Record<string, string> = {
        pending: 'Pendente',
        accepted: 'Nota IA aceita',
        adjusted: 'Ajustada pelo professor',
    }

    const formatDateTime = (value?: string | null) => {
        if (!value) return '-'
        const date = new Date(value)
        if (Number.isNaN(date.getTime())) return value
        return date.toLocaleString('pt-BR')
    }

    const renderAiQualityAlert = () => {
        const quality = redacao?.ai_quality
        if (!quality || quality.status === 'ok') return null

        const flags = quality.flags || []
        const isRequired = quality.status === 'requires_review' || quality.requires_review
        return (
            <Alert
                style={{ marginBottom: 16 }}
                type={isRequired ? 'warning' : 'info'}
                showIcon
                message={isRequired ? 'Avaliação IA requer revisão' : 'Revisão humana recomendada'}
                description={
                    <div>
                        <p style={{ margin: '0 0 8px' }}>
                            O sistema encontrou sinais de possível inconsistência na avaliação automática.
                        </p>
                        {flags.length > 0 && (
                            <ul style={{ margin: 0, paddingLeft: 18 }}>
                                {flags.map((flag, index) => (
                                    <li key={`${flag.code || 'flag'}-${index}`}>{flag.message}</li>
                                ))}
                            </ul>
                        )}
                    </div>
                }
            />
        )
    }

    const handleEditarRedacao = async (reviewAction: 'accept_ai' | 'adjust' = 'adjust') => {
        try {
            if (redacao) {
                const response = await authFetch(`${API_URL}/redacoes/${redacao._id}`, {
                    method: 'PUT',
                    headers: authHeaders({
                        'Content-Type': 'application/json'
                    }),
                    body: JSON.stringify({
                        review_action: reviewAction,
                        nota_competencia_1_professor: notaComp1Editada !== '' ? notaComp1Editada : 0,
                        nota_competencia_2_professor: notaComp2Editada !== '' ? notaComp2Editada : 0,
                        nota_competencia_3_professor: notaComp3Editada !== '' ? notaComp3Editada : 0,
                        nota_competencia_4_professor: notaComp4Editada !== '' ? notaComp4Editada : 0,
                        nota_competencia_5_professor: notaComp5Editada !== '' ? notaComp5Editada : 0,
                        feedback_professor: feedbackProfessorEditada !== '' ? feedbackProfessorEditada : "",
                        review_comment: reviewComment,
                    })
                });
                if (response.ok) {
                    const data = await response.json()
                    message.success(reviewAction === 'accept_ai' ? 'Notas IA aceitas pelo professor.' : 'Revisão do professor salva.');
                    onCancel();
                    onRedacaoEditado(data.redacao || redacao);
                } else {
                    message.error('Erro ao salvar a revisão da redação.')
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
                                <p style={{ margin: '6px 0 0', color: '#6b7280' }}>
                                    Avaliação IA: {redacao.ai_evaluation?.model_version || redacao.ai_evaluation?.model_name || 'modelo registrado'} · {formatDateTime(redacao.ai_evaluation?.created_at)}
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
                    {renderAiQualityAlert()}

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
                    <Alert
                        style={{ marginBottom: 12 }}
                        type="info"
                        showIcon
                        message={
                            <Space wrap>
                                <span>Avaliação IA:</span>
                                <Tag color="blue">{redacao.ai_evaluation?.model_version || redacao.ai_evaluation?.model_name || 'modelo registrado'}</Tag>
                                <span>{formatDateTime(redacao.ai_evaluation?.created_at)}</span>
                                <span>Revisão:</span>
                                <Tag color={redacao.teacher_review?.status === 'pending' ? 'gold' : 'green'}>
                                    {reviewStatusLabel[redacao.teacher_review?.status || 'pending'] || redacao.teacher_review?.status}
                                </Tag>
                            </Space>
                        }
                        description={redacao.teacher_review?.reviewed_at
                            ? `Revisado por ${redacao.teacher_review.reviewed_by_name || 'professor'} em ${formatDateTime(redacao.teacher_review.reviewed_at)}.`
                            : 'O professor pode aceitar a avaliação automática da IA ou registrar uma revisão própria.'}
                    />
                    {renderAiQualityAlert()}
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
                        <Panel header="Comentário da revisão" key="review">
                            <TextArea
                                rows={5}
                                style={inputStyle}
                                value={reviewComment}
                                placeholder="Registre uma justificativa curta para aceitar ou ajustar a avaliação da IA."
                                onChange={(e) => setReviewComment(e.target.value)}
                            />
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

                    <Space style={{ marginTop: '1vw' }}>
                        <Button onClick={() => handleEditarRedacao('accept_ai')}>Aceitar notas IA</Button>
                        <Button type="primary" onClick={() => handleEditarRedacao('adjust')}>Salvar revisão</Button>
                    </Space>
                </div>
            )}
        </Modal>
    );
};

export default ModalDetalhesRedacao;
