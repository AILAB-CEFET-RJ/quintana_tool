import { useEffect, useState } from 'react'

const Sobre = () => {
  const [content, setContent] = useState('')

  useEffect(() => {
    fetch('/README.md').then(response => {
      response.text().then(text => {
        setContent(text)
      })
    })
  }, [])

  return (

    <div style={{ display: 'flex', justifyContent: 'center' }}>
      <title>Sobre</title>
      <div style={{ maxWidth: '50%', padding: '40px' }}>
        <>
          <h1 style={{ color: '#1a73e8' }}>Sobre o Quintana</h1>
          <p>
            O <strong>Quintana</strong> é uma iniciativa acadêmica desenvolvida no&nbsp;
            <a
              href="https://github.com/AILAB-CEFET-RJ"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#1a73e8', fontWeight: 'bold' }}
            >
              AILab do CEFET/RJ
            </a>, com o objetivo de democratizar o acesso à avaliação formativa de textos dissertativos em língua portuguesa.
          </p>
          <p>
            Utilizando técnicas avançadas de <em>Processamento de Linguagem Natural</em> e modelos de aprendizado de máquina
            treinados com base nos critérios do ENEM, a ferramenta oferece uma alternativa escalável, transparente e pedagógica
            para a correção automatizada de redações.
          </p>
          <p>
            O projeto está alinhado com os princípios de inovação educacional, equidade avaliativa e uso ético de inteligência
            artificial na educação pública brasileira.
          </p>
          <p>
            Seu código-fonte é aberto e pode ser encontrado neste repositório GitHub:&nbsp;
            <a
              href="https://github.com/AILAB-CEFET-RJ/quintana_tool"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#1a73e8' }}
            >
              Acessar repositório
            </a>.
          </p>
        </>

      </div>
    </div>
  )
}

export default Sobre
