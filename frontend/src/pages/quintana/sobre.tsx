import PageHeader from '@/components/ui/PageHeader'
import PageShell from '@/components/ui/PageShell'
import SectionPanel from '@/components/ui/SectionPanel'

const Sobre = () => {
  return (
    <PageShell maxWidth={920}>
      <PageHeader
        title="Sobre o Quintana"
        description="Uma ferramenta acadêmica para avaliação formativa de redações em língua portuguesa, baseada nas competências do ENEM."
      />
      <SectionPanel>
        <div style={{ color: '#374151', fontSize: 16, lineHeight: 1.75 }}>
          <p>
            O <strong>Quintana</strong> é uma ferramenta de avaliação automatizada de redações em língua portuguesa,
            baseada nas cinco competências do Exame Nacional do Ensino Médio (ENEM). A plataforma permite que estudantes
            submetam textos dissertativo-argumentativos e recebam notas por competência, visualizações de progresso e
            sugestões de melhoria.
          </p>
          <p>
            A iniciativa é desenvolvida no&nbsp;
            <a href="https://github.com/AILAB-CEFET-RJ" target="_blank" rel="noopener noreferrer">
              AILab do CEFET/RJ
            </a>, com foco em ampliar o acesso a ferramentas educacionais com retorno formativo, objetivo e explicável.
          </p>
          <p>
            Utilizando técnicas de Processamento de Linguagem Natural e modelos de aprendizado de máquina treinados com base
            nos critérios do ENEM, o Quintana oferece apoio pedagógico para estudantes e professores, sem substituir o olhar
            humano sobre o texto.
          </p>
          <p>
            O projeto está alinhado com princípios de inovação educacional, equidade avaliativa e uso ético de inteligência
            artificial na educação pública brasileira.
          </p>
        </div>
      </SectionPanel>

      <SectionPanel>
        <div style={{ color: '#374151', fontSize: 16, lineHeight: 1.75 }}>
          <h2 style={{ color: '#111827', fontSize: 22, marginTop: 0 }}>Por que Quintana?</h2>
          <p>
            O nome <strong>Quintana</strong> é uma homenagem a <strong>Mário Quintana</strong>, escritor, poeta, jornalista
            e tradutor brasileiro. Reconhecido como o poeta das coisas simples, Quintana construiu uma obra marcada pela
            delicadeza, pela ironia, pela profundidade e pelo cuidado técnico com a linguagem.
          </p>
          <p>
            Ao adotar esse nome, a ferramenta faz referência a essa relação sensível e rigorosa com a escrita. Assim como
            a obra de Mário Quintana valoriza a expressão em língua portuguesa e a capacidade de comunicar ideias com
            clareza, simplicidade e profundidade, o Quintana busca apoiar estudantes no desenvolvimento de suas redações.
          </p>
          <p>
            A escolha do nome também reforça a intenção educacional do projeto: oferecer um apoio formativo que ajude o
            estudante a refletir sobre sua produção escrita e a aperfeiçoá-la ao longo do processo de aprendizagem.
          </p>
        </div>
      </SectionPanel>

      <SectionPanel>
        <div style={{ color: '#374151', fontSize: 16, lineHeight: 1.75 }}>
          <h2 style={{ color: '#111827', fontSize: 22, marginTop: 0 }}>Código-fonte</h2>
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
