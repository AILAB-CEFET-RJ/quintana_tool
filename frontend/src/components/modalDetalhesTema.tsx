import { Modal, Input, Button, message } from 'antd';
import { useState } from 'react';
import { Tema } from '@/pages/quintana/home';
import { useAuth } from '@/context';
import { API_URL } from "@/config/config";
import { authFetch, authHeaders } from '@/lib/authFetch';

interface TemaDetalhes {
    open: boolean;
    onCancel: () => void;
    tema: Tema | null;
    onTemaEditado: (temaEditado: Tema) => void;
}

const ModalDetalhesTema: React.FC<TemaDetalhes> = ({ open, onCancel, tema, onTemaEditado }) => {
    const [temaEditado, setTemaEditado] = useState<string>('');
    const [descricaoEditada, setDescricaoEditada] = useState<string>('');
    const { tipoUsuario } = useAuth();

    const handleEditarTema = async () => {
        try {
            if (tema && (descricaoEditada !== '' || temaEditado !== '')) {
                const response = await authFetch(`${API_URL}/temas/${tema._id}`, {
                    method: 'PUT',
                    headers: authHeaders({
                        'Content-Type': 'application/json'
                    }),
                    body: JSON.stringify({
                        tema: temaEditado !== '' ? temaEditado : tema.tema,
                        descricao: descricaoEditada !== '' ? descricaoEditada : tema.descricao
                    })
                });
                if (response.ok) {
                    message.success('Tema atualizado com sucesso!');
                    onCancel();
                    onTemaEditado({
                        ...tema,
                        tema: temaEditado !== '' ? temaEditado : tema.tema,
                        descricao: descricaoEditada !== '' ? descricaoEditada : tema.descricao
                    });
                }
            }
        } catch (error) {
            console.error('Erro ao atualizar o tema:', error);
            message.error('Erro ao atualizar o tema. Por favor, tente novamente.');
        }
    };

    return (
        <Modal
            title={tipoUsuario === 'aluno' ? 'Detalhes do Tema' : 'Editar Tema'}
            open={open}
            onCancel={onCancel}
            footer={null}
        >

            {tema && tipoUsuario === 'aluno' ? (
                <div>
                    <p><b>Professor</b>: {tema.teacher_name || 'Professor'}</p>
                    <p><b>Tema</b>: {tema.tema}</p>
                    <p>
                        <b>Descrição</b>:<br />
                        <span style={{ whiteSpace: 'pre-line' }}>{tema.descricao}</span>
                    </p>
                </div>
            ) : tema && (
                <div>
                    <label style={{ marginBottom: '10px' }}><b>Professor</b>:</label>
                    <Input style={{ marginBottom: '10px' }} value={tema.teacher_name || 'Professor'} disabled />
                    <label style={{ marginBottom: '10px' }}><b>Tema</b>:</label>
                    <Input style={{ marginBottom: '10px' }} defaultValue={tema.tema} onChange={(e) => setTemaEditado(e.target.value)} />
                    <label style={{ marginBottom: '10px' }}><b>Descrição</b>:</label>
                    <Input.TextArea style={{ marginBottom: '10px' }} defaultValue={tema.descricao} onChange={(e) => setDescricaoEditada(e.target.value)} />
                    <Button onClick={handleEditarTema}>Editar</Button>
                </div>
            )}
        </Modal>
    );
};

export default ModalDetalhesTema;
