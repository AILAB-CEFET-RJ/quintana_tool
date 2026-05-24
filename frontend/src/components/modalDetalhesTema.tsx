import { Modal, Input, Button, message } from 'antd';
import { useEffect, useState } from 'react';
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
    const { tipoUsuario, userId } = useAuth();
    const canEdit = tipoUsuario === 'professor' && tema?.teacher_id === userId;

    useEffect(() => {
        if (tema && open) {
            setTemaEditado(tema.tema || '');
            setDescricaoEditada(tema.descricao || '');
        }
    }, [tema, open]);

    const handleEditarTema = async () => {
        try {
            if (tema) {
                const response = await authFetch(`${API_URL}/temas/${tema._id}`, {
                    method: 'PUT',
                    headers: authHeaders({
                        'Content-Type': 'application/json'
                    }),
                    body: JSON.stringify({
                        tema: temaEditado,
                        descricao: descricaoEditada
                    })
                });
                if (response.ok) {
                    message.success('Tema atualizado com sucesso!');
                    onCancel();
                    onTemaEditado({
                        ...tema,
                        tema: temaEditado,
                        descricao: descricaoEditada
                    });
                } else {
                    message.error('Erro ao atualizar o tema. Por favor, tente novamente.');
                }
            }
        } catch (error) {
            console.error('Erro ao atualizar o tema:', error);
            message.error('Erro ao atualizar o tema. Por favor, tente novamente.');
        }
    };

    return (
        <Modal
            title={canEdit ? 'Editar Tema' : 'Detalhes do Tema'}
            open={open}
            onCancel={onCancel}
            footer={null}
        >

            {tema && !canEdit ? (
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
                    <Input style={{ marginBottom: '10px' }} value={temaEditado} onChange={(e) => setTemaEditado(e.target.value)} />
                    <label style={{ marginBottom: '10px' }}><b>Descrição</b>:</label>
                    <Input.TextArea style={{ marginBottom: '10px' }} value={descricaoEditada} onChange={(e) => setDescricaoEditada(e.target.value)} />
                    <Button type="primary" onClick={handleEditarTema}>Salvar alterações</Button>
                </div>
            )}
        </Modal>
    );
};

export default ModalDetalhesTema;
