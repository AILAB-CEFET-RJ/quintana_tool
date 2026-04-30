import PageHeader from '@/components/ui/PageHeader'
import PageShell from '@/components/ui/PageShell'
import SectionPanel from '@/components/ui/SectionPanel'

const Sobre = () => {
  return (
    <PageShell maxWidth={920}>
      <PageHeader
        title="Sobre o Quintana"
        description="Uma ferramenta acadêmica para avaliação formativa de redações em língua portuguesa."
      />
      <SectionPanel>
        <div style={{ color: '#374151', fontSize: 16, lineHeight: 1.75 }}>
          <p>
            O <strong>Quintana</strong> é uma iniciativa acadêmica desenvolvida no&nbsp;
            <a href="https://github.com/AILAB-CEFET-RJ" target="_blank" rel="noopener noreferrer">
              AILab do CEFET/RJ
            </a>, com o objetivo de democratizar o acesso à avaliação formativa de textos dissertativos em língua portuguesa.
          </p>
          <p>
            Utilizando técnicas de Processamento de Linguagem Natural e modelos de aprendizado de máquina treinados com base nos
            critérios do ENEM, a ferramenta oferece uma alternativa escalável, transparente e pedagógica para a correção automatizada
            de redações.
          </p>
          <p>
            O projeto está alinhado com princípios de inovação educacional, equidade avaliativa e uso ético de inteligência artificial
            na educação pública brasileira.
          </p>
          <p>
            Código-fonte:&nbsp;
            <a href="https://github.com/AILAB-CEFET-RJ/quintana_tool" target="_blank" rel="noopener noreferrer">
              github.com/AILAB-CEFET-RJ/quintana_tool
            </a>
          </p>
        </div>
      </SectionPanel>
    </PageShell>
  )
}

export default Sobre
