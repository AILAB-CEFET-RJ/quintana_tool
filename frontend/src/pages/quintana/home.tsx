import { Tabs, Button, Tooltip, message, Select, Space, Card, Row, Col, Statistic, Spin, Alert } from 'antd';
import { useState, useEffect } from 'react';
import { PlusOutlined, DeleteOutlined, FileTextOutlined, ReadOutlined, TrophyOutlined, UserOutlined } from '@ant-design/icons';
import Link from 'next/link';
import { useAuth } from '../../context';
import CustomTable from '../../components/customTable';
import ModalDetalhesTema from '@/components/modalDetalhesTema';
import ModalDetalhesRedacao from "@/components/modalDetalhesRedacao";
import { API_URL } from "@/config/config";
import ProgressTimeline from '@/components/studentInsights/ProgressTimeline';
import CompetencyRadar from '@/components/studentInsights/CompetencyRadar';
import PageShell from '@/components/ui/PageShell';
import PageHeader from '@/components/ui/PageHeader';
import SectionPanel from '@/components/ui/SectionPanel';
import { getCompetencyScores } from '@/lib/competencias';
import TeacherAnalyticsPanel from '@/components/teacherAnalytics/TeacherAnalyticsPanel';
import TeacherClassActivityManager from '@/components/teacherAnalytics/TeacherClassActivityManager';
import StudentActivitiesPanel from '@/components/studentInsights/StudentActivitiesPanel';

const { TabPane } = Tabs;
const { Option } = Select;

const buildAverageCompetencyRedacao = (redacoes: Redacao[]) => {
    const latestVersions = redacoes.filter((redacao) => redacao.is_latest_version !== false);

    if (!latestVersions.length) {
        return null;
    }

    const average = (field: keyof Redacao) => {
        const total = latestVersions.reduce((sum, redacao) => sum + (Number(redacao[field]) || 0), 0);
        return Math.round(total / latestVersions.length);
    };

    return {
        nota_competencia_1_model: average('nota_competencia_1_model'),
        nota_competencia_2_model: average('nota_competencia_2_model'),
        nota_competencia_3_model: average('nota_competencia_3_model'),
        nota_competencia_4_model: average('nota_competencia_4_model'),
        nota_competencia_5_model: average('nota_competencia_5_model'),
    };
};

export interface Tema {
    _id: string;
    nome_professor: string;
    tema: string;
    descricao: string;
}

export interface Redacao {
    titulo: string;
    texto: string;
    nota_total: number;
    nota_competencia_1_model: number;
    nota_competencia_2_model: number;
    nota_competencia_3_model: number;
    nota_competencia_4_model: number;
    nota_competencia_5_model: number;
    nota_professor: number;
    nota_competencia_1_professor: number;
    nota_competencia_2_professor: number;
    nota_competencia_3_professor: number;
    nota_competencia_4_professor: number;
    nota_competencia_5_professor: number;
    id_tema: string;
    _id: string;
    aluno: string;
    comentarios: string;
    feedback_llm: string;
    feedback_professor: string;
    created_at?: string;
    updated_at?: string;
    version_group_id?: string | null;
    parent_redacao_id?: string | null;
    version_number?: number;
    feedback_structured?: any;
    rewrite_checklist_state?: Record<string, boolean>;
    class_id?: string | null;
    activity_id?: string | null;
    submitted_at?: string;
    correction_source?: string;
    is_latest_version?: boolean;
}

const Home = () => {
    const [activeKey, setActiveKey] = useState<string>('1');
    const [temasData, setTemasData] = useState<Tema[]>([]);
    const [redacoesData, setRedacoesData] = useState<Redacao[]>([]);
    const [alunos, setAlunos] = useState<any[]>([]);
    const [modalVisible, setModalVisible] = useState(false);
    const [redacaoModalVisible, setRedacaoModalVisible] = useState(false);
    const [selectedTema, setSelectedTema] = useState<Tema | null>(null);
    const [selectedRedacao, setSelectedRedacao] = useState<Redacao | null>(null);
    const [filter, setFilter] = useState<string>('todos');
    const [filterAluno, setFilterAluno] = useState<string>('todos');
    const [teacherAnalytics, setTeacherAnalytics] = useState<any>(null);
    const [analyticsLoading, setAnalyticsLoading] = useState(false);
    const [analyticsError, setAnalyticsError] = useState('');
    const [classesData, setClassesData] = useState<any[]>([]);
    const [activitiesData, setActivitiesData] = useState<any[]>([]);
    const [studentActivities, setStudentActivities] = useState<any[]>([]);
    const [selectedClassId, setSelectedClassId] = useState<string>('todos');
    const [selectedActivityId, setSelectedActivityId] = useState<string>('todos');
    const [analyticsGroupBy, setAnalyticsGroupBy] = useState<string>('activity');
    const { isLoggedIn, tipoUsuario, nomeUsuario } = useAuth();

    const handleTabChange = (key: string) => {
        setActiveKey(key);
    };

    const openModal = (tema: any) => {
        setSelectedTema(tema);
        setModalVisible(true);
    };

    const openRedacaoModal = (redacao: any) => {
        setSelectedRedacao(redacao);
        setRedacaoModalVisible(true);
    };

    useEffect(() => {
        const fetchTemas = async () => {
            try {
                const response = await fetch(`${API_URL}/temas`);
                const data = await response.json();
                setTemasData(data);
            } catch (error) {
                console.error('Erro ao buscar os temas:', error);
            }
        };

        fetchTemas();
    }, []);

    useEffect(() => {
        const fetchRedacoes = async () => {
            if (!isLoggedIn) {
                return;
            }

            try {
                let url = `${API_URL}/redacoes`
                if (tipoUsuario === 'aluno') {
                    if (!nomeUsuario) {
                        return;
                    }
                    url += `?user=${nomeUsuario}`
                }
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error('Erro ao buscar redações');
                }
                const data = await response.json();
                setRedacoesData(data);
            } catch (error) {
                console.error('Erro ao buscar as redações:', error);
            }
        };

        fetchRedacoes();
    }, [isLoggedIn, tipoUsuario, nomeUsuario]);

    useEffect(() => {
        const fetchAlunos = async () => {
            try {
                const response = await fetch(`${API_URL}/users/alunos`);
                const data = await response.json();
                setAlunos(data);
            } catch (error) {
                console.error('Erro ao buscar alunos:', error);
            }
        };

        fetchAlunos();
    }, []);

    useEffect(() => {
        const fetchTeacherAnalytics = async () => {
            if (tipoUsuario !== 'professor' || !nomeUsuario) {
                return;
            }

            try {
                setAnalyticsLoading(true);
                setAnalyticsError('');
                const params = new URLSearchParams();
                if (selectedClassId !== 'todos') {
                    params.append('class_id', selectedClassId);
                }
                if (selectedActivityId !== 'todos') {
                    params.append('activity_id', selectedActivityId);
                }
                params.append('group_by', analyticsGroupBy);
                const query = params.toString();
                const response = await fetch(`${API_URL}/professores/${encodeURIComponent(nomeUsuario)}/analytics${query ? `?${query}` : ''}`);
                if (!response.ok) {
                    throw new Error('Erro ao buscar análise da turma');
                }
                const data = await response.json();
                setTeacherAnalytics(data);
            } catch (error) {
                console.error('Erro ao buscar análise da turma:', error);
                setAnalyticsError('Não foi possível carregar a análise da turma.');
            } finally {
                setAnalyticsLoading(false);
            }
        };

        fetchTeacherAnalytics();
    }, [tipoUsuario, nomeUsuario, redacoesData.length, temasData.length, selectedClassId, selectedActivityId, analyticsGroupBy]);

    useEffect(() => {
        const fetchStudentActivities = async () => {
            if (tipoUsuario !== 'aluno' || !nomeUsuario) {
                return;
            }

            try {
                const response = await fetch(`${API_URL}/students/${encodeURIComponent(nomeUsuario)}/activities`);
                if (response.ok) {
                    setStudentActivities(await response.json());
                }
            } catch (error) {
                console.error('Erro ao buscar atividades do aluno:', error);
            }
        };

        fetchStudentActivities();
    }, [tipoUsuario, nomeUsuario, redacoesData.length]);

    const fetchTeacherStructure = async () => {
        if (tipoUsuario !== 'professor' || !nomeUsuario) {
            return;
        }

        try {
            const [classesResponse, activitiesResponse] = await Promise.all([
                fetch(`${API_URL}/classes?teacher=${encodeURIComponent(nomeUsuario)}`),
                fetch(`${API_URL}/activities?teacher=${encodeURIComponent(nomeUsuario)}`)
            ]);

            if (classesResponse.ok) {
                setClassesData(await classesResponse.json());
            }

            if (activitiesResponse.ok) {
                setActivitiesData(await activitiesResponse.json());
            }
        } catch (error) {
            console.error('Erro ao buscar turmas e atividades:', error);
        }
    };

    useEffect(() => {
        fetchTeacherStructure();
    }, [tipoUsuario, nomeUsuario]);

    const handleDeleteTema = async (id: string) => {
        try {
            const response = await fetch(`${API_URL}/temas/${id}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                setTemasData(temasData.filter(tema => tema._id !== id));
                message.success('Tema deletado com sucesso!');
            }
        } catch (error) {
            console.error('Erro ao deletar o tema:', error);
            message.error('Erro ao deletar o tema. Por favor, tente novamente.');
        }
    };

    const handleTemaEditado = (temaEditado: Tema) => {
        setTemasData(temasData.map(tema => (tema._id === temaEditado._id ? temaEditado : tema)));
    };

    const handleRedacaoEditado = (redacaoEditado: Redacao) => {
        setRedacoesData(redacoesData.map(redacao => (redacao._id === redacaoEditado._id ? redacaoEditado : redacao)));
    };

    const getTemaNome = (id_tema: string): string => {
        const tema = temasData.find((tema) => tema._id === id_tema);
        return tema ? tema.tema : 'Tema não encontrado';
    };

    const handleFilterTemas = () => {
        return temasData.filter(tema => tema.nome_professor === nomeUsuario);
    };

    const handleFilterRedacoes = () => {
        if (filter === 'meus') {
            return redacoesData.filter(redacao => {
                return temasData.find(tema => tema._id === redacao.id_tema && tema.nome_professor === nomeUsuario);
            });
        }

        if (filterAluno !== 'todos') {
            return redacoesData.filter(redacao => {
                return redacao.aluno === filterAluno
            })
        }
        return redacoesData;
    };

    const temasColumns = [
        { title: 'Professor', dataIndex: 'nome_professor', key: 'nome_professor', ellipsis: true },
        {
            title: 'Tema',
            dataIndex: 'tema',
            key: 'tema',
            render: (text: string, record: Tema) =>
                <Tooltip title={tipoUsuario === 'aluno' ? "Detalhes do tema" : "Editar tema"}>
                    <Button type="link" onClick={() => openModal(record)}>{text}</Button>
                </Tooltip>, ellipsis: true,
        },
        { title: 'Descrição', dataIndex: 'descricao', key: 'descricao', ellipsis: true },
        {
            title: 'Ações',
            key: 'acoes',
            render: (record: Tema) => (
                tipoUsuario === 'professor' && record.nome_professor === nomeUsuario ? (
                    <Tooltip title="Deletar tema">
                        <Button onClick={() => handleDeleteTema(record._id)} danger icon={<DeleteOutlined />} />
                    </Tooltip>
                ) :
                    tipoUsuario === 'aluno' && (
                        <Link href={`/quintana/redacao?id=${record._id}`}
                            onClick={() => {
                                localStorage.setItem('temaRedacao', record.tema)
                                localStorage.setItem('descricaoRedacao', record.descricao)
                            }} >
                            <PlusOutlined style={{ fontSize: '16px', marginRight: '8px' }} />
                            Inserir Nova Redação
                        </Link>
                    )
            ),
        },
    ];

    const redacaoColumns = [
        {
            title: 'Título',
            dataIndex: 'titulo',
            key: 'titulo',
            render: (text: string, record: Redacao) => {
                const titulo = text?.trim() ? text : 'sem título'
                const tituloLimitado = titulo.length > 40 ? `${titulo.slice(0, 40)}...` : titulo

                return (
                    <Tooltip title={titulo}>
                        <Button type="link" onClick={() => openRedacaoModal(record)}>
                            {tituloLimitado}
                        </Button>
                    </Tooltip>
                )
            },
            ellipsis: true,
        },
        { title: 'Aluno', dataIndex: 'aluno', key: 'aluno', ellipsis: true },
        {
            title: 'Tema',
            dataIndex: 'id_tema',
            key: 'id_tema',
            render: (id_tema: string) => getTemaNome(id_tema),
            ellipsis: true
        },
        { title: 'Nota total', dataIndex: 'nota_total', key: 'nota_total', align: 'center', ellipsis: true },
        { title: 'Nota Professor', dataIndex: 'nota_professor', key: 'nota_professor', align: 'center', ellipsis: true },
    ];

    const visibleRedacoes = handleFilterRedacoes();
    const latestRedacao = [...visibleRedacoes].sort((a, b) => {
        const aDate = a.created_at ? new Date(a.created_at).getTime() : parseInt(`${a._id || '00000000'}`.slice(0, 8), 16) * 1000;
        const bDate = b.created_at ? new Date(b.created_at).getTime() : parseInt(`${b._id || '00000000'}`.slice(0, 8), 16) * 1000;
        return bDate - aDate;
    })[0];
    const priority = latestRedacao ? getCompetencyScores(latestRedacao).sort((a, b) => a.score - b.score)[0] : null;
    const averageCompetencyRedacao = tipoUsuario === 'aluno' ? buildAverageCompetencyRedacao(visibleRedacoes) : null;
    const pageTitle = tipoUsuario === 'professor' ? 'Painel do professor' : 'Minhas redações';
    const pageDescription = tipoUsuario === 'professor'
        ? 'Acompanhe temas, submissões e correções dos estudantes.'
        : 'Acompanhe seus textos, visualize progresso e identifique prioridades de estudo.';
    const summaryTooltips = {
        redacoes: tipoUsuario === 'professor'
            ? 'Quantidade de redações disponíveis para consulta neste painel, considerando os filtros aplicados.'
            : 'Quantidade de redações que você já enviou, considerando as versões visíveis.',
        temas: tipoUsuario === 'professor'
            ? 'Quantidade de temas cadastrados por você.'
            : 'Quantidade de temas disponíveis para envio de redações.',
        ultimaNota: tipoUsuario === 'professor'
            ? 'Nota total da redação mais recente na listagem atual.'
            : 'Nota total da sua redação mais recente.',
        prioridade: tipoUsuario === 'professor'
            ? 'Quantidade de estudantes cadastrados como alunos na plataforma.'
            : 'Competência com menor nota na sua redação mais recente.'
    };

    return (
        <PageShell>
            <PageHeader title={pageTitle} description={pageDescription} />

            {isLoggedIn && (
                <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                    <Col xs={24} sm={12} lg={6}>
                        <Tooltip title={summaryTooltips.redacoes}>
                            <Card bordered={false} style={{ borderRadius: 8 }}>
                                <Statistic title="Redações" value={visibleRedacoes.length} prefix={<FileTextOutlined />} />
                            </Card>
                        </Tooltip>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Tooltip title={summaryTooltips.temas}>
                            <Card bordered={false} style={{ borderRadius: 8 }}>
                                <Statistic title="Temas disponíveis" value={tipoUsuario === 'professor' ? handleFilterTemas().length : temasData.length} prefix={<ReadOutlined />} />
                            </Card>
                        </Tooltip>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Tooltip title={summaryTooltips.ultimaNota}>
                            <Card bordered={false} style={{ borderRadius: 8 }}>
                                <Statistic title="Última nota" value={latestRedacao ? Math.round(Number(latestRedacao.nota_total) || 0) : 0} prefix={<TrophyOutlined />} />
                            </Card>
                        </Tooltip>
                    </Col>
                    <Col xs={24} sm={12} lg={6}>
                        <Tooltip title={summaryTooltips.prioridade}>
                            <Card bordered={false} style={{ borderRadius: 8 }}>
                                <Statistic title={tipoUsuario === 'professor' ? 'Alunos listados' : 'Prioridade atual'} value={tipoUsuario === 'professor' ? alunos.length : priority?.code || '-'} prefix={<UserOutlined />} />
                            </Card>
                        </Tooltip>
                    </Col>
                </Row>
            )}

            <SectionPanel>
            <Tabs activeKey={activeKey} onChange={handleTabChange} style={{ flex: 1 }}>
                <TabPane tab="Temas" key="1">
                    <Space style={{ marginBottom: 16 }}>
                        {tipoUsuario === 'professor' && (
                            <Link href="/quintana/tema">
                                <Button type="primary" icon={<PlusOutlined />} style={{ marginRight: 8 }}>
                                    Adicionar Tema
                                </Button>
                            </Link>
                        )}
                        {tipoUsuario === 'professor' && (
                            <Select defaultValue="todos" style={{ width: 140 }} onChange={value => setFilter(value)}>
                                <Option value="todos">Todos os Temas</Option>
                                <Option value="meus">Meus Temas</Option>
                            </Select>
                        )}
                    </Space>
                    {isLoggedIn &&
                        <CustomTable
                            dataSource={filter === 'meus' ? handleFilterTemas() : temasData}
                            columns={temasColumns}
                        />
                    }
                </TabPane>
                <TabPane tab={tipoUsuario === 'professor' ? 'Redações recebidas' : 'Minhas redações'} key="2">
                    <Space style={{ marginBottom: 16 }}>
                        {tipoUsuario === 'professor' && (
                            <Select defaultValue="todos" style={{ width: 200 }} onChange={value => setFilter(value)}>
                                <Option value="todos">Todas as Redações</Option>
                                <Option value="meus">Redações dos meus temas</Option>
                            </Select>
                        )}
                        {tipoUsuario === 'professor' && (
                            <Select defaultValue="todos" style={{ width: 200 }} onChange={value => setFilterAluno(value)}>
                                <Option value="todos">Todos os Alunos</Option>
                                {alunos.map(aluno => (
                                    <Option key={aluno._id} value={aluno.username}>
                                        {aluno.username}
                                    </Option>
                                ))}
                            </Select>
                        )}
                    </Space>
                    {isLoggedIn && tipoUsuario === 'aluno' && (
                        <>
                            {averageCompetencyRedacao && (
                                <CompetencyRadar
                                    redacao={averageCompetencyRedacao}
                                    title="Radar médio das competências"
                                    subtitle="Média das competências considerando as redações mais recentes de cada versão."
                                />
                            )}
                            <ProgressTimeline redacoes={visibleRedacoes} />
                        </>
                    )}
                    {isLoggedIn &&
                        <CustomTable
                            dataSource={visibleRedacoes}
                            columns={redacaoColumns}
                        />
                    }
                </TabPane>
                {tipoUsuario === 'aluno' && (
                    <TabPane tab="Atividades" key="3">
                        <StudentActivitiesPanel activities={studentActivities} />
                    </TabPane>
                )}
                {tipoUsuario === 'professor' && (
                    <TabPane tab="Análise da turma" key="3">
                        <Space style={{ marginBottom: 16 }} wrap>
                            <Select
                                value={selectedClassId}
                                style={{ minWidth: 220 }}
                                onChange={(value) => {
                                    setSelectedClassId(value);
                                    setSelectedActivityId('todos');
                                }}
                            >
                                <Option value="todos">Todas as turmas</Option>
                                {classesData.map((item) => (
                                    <Option key={item._id} value={item._id}>{item.name}</Option>
                                ))}
                            </Select>
                            <Select
                                value={selectedActivityId}
                                style={{ minWidth: 260 }}
                                onChange={setSelectedActivityId}
                            >
                                <Option value="todos">Todas as atividades</Option>
                                {activitiesData
                                    .filter((item) => selectedClassId === 'todos' || item.class_id === selectedClassId)
                                    .map((item) => (
                                        <Option key={item._id} value={item._id}>{item.title}</Option>
                                    ))}
                            </Select>
                            <Select
                                value={analyticsGroupBy}
                                style={{ minWidth: 180 }}
                                onChange={setAnalyticsGroupBy}
                            >
                                <Option value="activity">Agrupar por atividade</Option>
                                <Option value="theme">Agrupar por tema</Option>
                                <Option value="week">Agrupar por dia</Option>
                            </Select>
                        </Space>
                        {analyticsLoading ? (
                            <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
                                <Spin />
                            </div>
                        ) : analyticsError ? (
                            <Alert type="error" showIcon message={analyticsError} />
                        ) : (
                            <TeacherAnalyticsPanel data={teacherAnalytics} />
                        )}
                    </TabPane>
                )}
                {tipoUsuario === 'professor' && (
                    <TabPane tab="Turmas e atividades" key="4">
                        <TeacherClassActivityManager
                            teacher={nomeUsuario}
                            alunos={alunos}
                            temas={temasData}
                            onChanged={fetchTeacherStructure}
                        />
                    </TabPane>
                )}
            </Tabs>
            </SectionPanel>

            <ModalDetalhesTema
                open={modalVisible}
                onCancel={() => setModalVisible(false)}
                tema={selectedTema}
                onTemaEditado={handleTemaEditado}
            />

            <ModalDetalhesRedacao
                open={redacaoModalVisible}
                onCancel={() => setRedacaoModalVisible(false)}
                redacao={selectedRedacao}
                onRedacaoEditado={handleRedacaoEditado}
            />

        </PageShell>
    );
};

export default Home;
