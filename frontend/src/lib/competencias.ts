export type CompetencyCode = 'C1' | 'C2' | 'C3' | 'C4' | 'C5'

export interface CompetencyInfo {
  code: CompetencyCode
  shortTitle: string
  title: string
  modelField: string
  professorField: string
  defaultAction: string
}

export const COMPETENCIES: CompetencyInfo[] = [
  {
    code: 'C1',
    shortTitle: 'Norma escrita',
    title: 'Domínio da modalidade escrita formal',
    modelField: 'nota_competencia_1_model',
    professorField: 'nota_competencia_1_professor',
    defaultAction: 'Revise desvios gramaticais, pontuação e escolhas vocabulares antes de reenviar.'
  },
  {
    code: 'C2',
    shortTitle: 'Proposta e repertório',
    title: 'Compreensão da proposta e uso de repertório sociocultural',
    modelField: 'nota_competencia_2_model',
    professorField: 'nota_competencia_2_professor',
    defaultAction: 'Garanta que tese, repertório e argumentos estejam diretamente ligados ao tema.'
  },
  {
    code: 'C3',
    shortTitle: 'Argumentação',
    title: 'Seleção e organização de argumentos',
    modelField: 'nota_competencia_3_model',
    professorField: 'nota_competencia_3_professor',
    defaultAction: 'Desenvolva cada argumento com explicação, evidência e relação clara com a tese.'
  },
  {
    code: 'C4',
    shortTitle: 'Coesão',
    title: 'Mecanismos linguísticos para construção da argumentação',
    modelField: 'nota_competencia_4_model',
    professorField: 'nota_competencia_4_professor',
    defaultAction: 'Use conectivos variados para explicitar oposição, causa, consequência e conclusão.'
  },
  {
    code: 'C5',
    shortTitle: 'Intervenção',
    title: 'Proposta de intervenção',
    modelField: 'nota_competencia_5_model',
    professorField: 'nota_competencia_5_professor',
    defaultAction: 'Explicite agente, ação, meio, finalidade e detalhamento na conclusão.'
  }
]

export const getScore = (redacao: any, competency: CompetencyInfo, source: 'model' | 'professor' = 'model') => {
  const field = source === 'professor' ? competency.professorField : competency.modelField
  const value = Number(redacao[field])
  return Number.isFinite(value) ? value : 0
}

export const getCompetencyScores = (redacao: any, source: 'model' | 'professor' = 'model') =>
  COMPETENCIES.map((competency) => ({
    ...competency,
    score: getScore(redacao, competency, source)
  }))
