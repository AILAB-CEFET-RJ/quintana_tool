import PageHeader from '@/components/ui/PageHeader'
import PageShell from '@/components/ui/PageShell'
import SectionPanel from '@/components/ui/SectionPanel'
import { COMPETENCIES } from '@/lib/competencias'

const Competencias = () => {
  return (
    <PageShell maxWidth={980}>
      <PageHeader
        title="Competências da redação do ENEM"
        description="As cinco competências organizam a correção como um conjunto de habilidades, não apenas como uma nota total."
      />
      <div style={{ display: 'grid', gap: 14 }}>
        {COMPETENCIES.map((competency, index) => (
          <SectionPanel key={competency.code}>
            <div style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
              <div style={{
                width: 44,
                height: 44,
                borderRadius: 8,
                background: '#e6f4ff',
                color: '#0958d9',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                flex: '0 0 auto'
              }}>
                {competency.code}
              </div>
              <div>
                <h2 style={{ margin: 0, fontSize: 19 }}>{competency.title}</h2>
                <p style={{ margin: '8px 0 0', color: '#4b5563', lineHeight: 1.65 }}>
                  {[
                    'Avalia domínio da escrita formal, incluindo gramática, pontuação, ortografia e precisão vocabular.',
                    'Avalia compreensão da proposta, manutenção do tema e uso produtivo de repertório sociocultural.',
                    'Avalia a capacidade de selecionar, organizar e desenvolver argumentos em defesa de um ponto de vista.',
                    'Avalia coesão textual, encadeamento lógico e uso de recursos linguísticos para conectar ideias.',
                    'Avalia a proposta de intervenção, considerando agente, ação, meio, finalidade e detalhamento.'
                  ][index]}
                </p>
              </div>
            </div>
          </SectionPanel>
        ))}
      </div>
    </PageShell>
  )
}

export default Competencias
