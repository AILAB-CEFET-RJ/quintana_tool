import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import rehypeRaw from 'rehype-raw'

const Competencias = () => {
  const [content, setContent] = useState('')

  return (
    <div style={{ display: 'flex', justifyContent: 'center' }}>
        <div style={{maxWidth: '50%', padding: '16px'}}>
            <div>
                <title>Competências da redação do Enem</title>
                <h1>Competências da redação do Enem</h1>
                <p>Veja abaixo quais são as cinco competências da redação do Enem:</p>
                <ul>
                    <li><b>Competência 1</b>: Demonstrar domínio da modalidade escrita formal da língua portuguesa</li>
                    <li><b>Competência 2</b>: Compreender a proposta de redação e aplicar conceitos das várias áreas de
                        conhecimento para desenvolver o tema, dentro dos limites estruturais do texto
                        dissertativo-argumentativo em prosa.
                    </li>
                    <li><b>Competência 3</b>: Selecionar, relacionar, organizar e interpretar informações, fatos,
                        opiniões e
                        argumentos em defesa de um ponto de vista.
                    </li>
                    <li><b>Competência 4</b>: Demonstrar conhecimento dos mecanismos linguísticos necessários para a
                        construção
                        da argumentação.
                    </li>
                    <li><b>Competência 5</b>: Elaborar proposta de intervenção para o problema abordado, respeitando os
                        direitos
                        humanos.
                    </li>
                </ul>

                <h2>Entenda as 5 competências da redação do Enem</h2>
                <p>Ao entender as cinco competências da redação do Enem, o estudante chegará preparado para cumprir os
                    critérios que serão observados no seu texto. Confira abaixo alguns detalhes importantes sobre as
                    competências:</p>

                <h3>Competência 1 da redação do Enem</h3>
                <p>A Competência 1 da redação do Enem é um critério que analisa se o participante possui escrita formal
                    da
                    língua portuguesa, usando as regras gramaticais e a construção sintática de forma adequada. Essa
                    competência também verifica se ele adota as regras de ortografia e de acentuação gráfica em
                    conformidade com o atual Acordo Ortográfico.</p>
                <p><a
                    href="https://vestibular.brasilescola.uol.com.br/enem/competencia-1-redacao-enem-os-erros-mais-comuns.htm">Leia
                    mais sobre a competência 1 e veja os erros mais comuns</a></p>

                <h3>Competência 2 da redação do Enem</h3>
                <p>A Competência 2 da redação do Enem avalia se o estudante seguiu o formativo
                    dissertativo-argumentativo.
                    Outro aspecto analisado é a presença de repertório sociocultural, que é uma informação, um fato, uma
                    citação ou uma experiência vivida que, de alguma forma, contribui como argumento para a discussão
                    proposta.</p>
                <p><a href="https://brasilescola.uol.com.br/redacao/competencia-2-redacao-enem.htm">Veja mais detalhes
                    sobre a competência 2</a></p>

                <h3>Competência 3 da redação do Enem</h3>
                <p>A Competência 3 da redação do Enem analisa se o inscrito elaborou um texto que possui coerência e da
                    plausibilidade entre as ideias apresentadas e se atende o projeto de redação (planejamento prévio à
                    escrita) que deve ser produzida.</p>
                <p><a href="https://brasilescola.uol.com.br/redacao/competencia-3-da-redacao-do-enem.htm">Saiba mais
                    sobre a competência 3</a></p>

                <h3>Competência 4 da redação do Enem</h3>
                <p>A Competência 4 da redação do Enem é um critério que analisa se o estudante produziu o texto com uma
                    estruturação lógica e formal. Sendo assim, as frases e os parágrafos devem estar interligados,
                    apresentando as ideias de forma coerente.</p>
                <p><a href="https://brasilescola.uol.com.br/redacao/competencia-3-da-redacao-do-enem.htm">Confira como
                    funciona a competência 4</a></p>

                <h3>Competência 5 da redação do Enem</h3>
                <p>Na Competência 5 da redação do Enem, é avaliado se participante apresentou uma proposta de
                    intervenção,
                    ou seja, uma iniciativa que busque enfrentar o problema exposto. Conforme a cartilha de redação, é a
                    ocasião para que o estudante demonstre seu preparo para exercitar a cidadania e atuar na realidade,
                    em
                    consonância com os direitos humanos.</p>
            </div>
            <p>Fonte:
                https://vestibular.brasilescola.uol.com.br/enem/enem-2023-entenda-as-5-competencias-da-redacao/355070.html</p>
        </div>


    </div>
  )
}

export default Competencias
