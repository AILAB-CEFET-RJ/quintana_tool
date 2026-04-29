import { Tabs, Button, Modal, Tooltip, message, Select, Space } from 'antd';
import { useState, useEffect } from 'react';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import Link from 'next/link';
import { useAuth } from '../../context';
import CustomTable from '../../components/customTable';
import ModalDetalhesTema from '@/components/modalDetalhesTema';
import ModalDetalhesRedacao from "@/components/modalDetalhesRedacao";
import { API_URL } from "@/config/config";

const { TabPane } = Tabs;
const { Option } = Select;

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
            try {
                let url = `${API_URL}/redacoes`
                if (tipoUsuario === 'aluno') {
                    url += `?user=${nomeUsuario}`
                }
                const response = await fetch(url);
                console.log(response);
                const data = await response.json();
                setRedacoesData(data);
            } catch (error) {
                console.error('Erro ao buscar as redações:', error);
            }
        };

        fetchRedacoes();
    }, []);

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

    return (
        <div style={{ padding: '0 20px 0 20px', width: '100vw' }}>
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
                <TabPane tab="Redações" key="2">
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
                    {isLoggedIn &&
                        <CustomTable
                            dataSource={handleFilterRedacoes()}
                            columns={redacaoColumns}
                        />
                    }
                </TabPane>
            </Tabs>

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

        </div>
    );
};

export default Home;