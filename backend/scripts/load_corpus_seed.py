#!/usr/bin/env python3
"""
Script de carga de dados no MongoDB para o Quintana.
Respeita os schemas definidos em backend/schemas.py
"""

import argparse
import json
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pymongo import MongoClient
from bson import ObjectId
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import MONGO_DB_NAME, MONGO_URI
except ImportError:
    MONGO_URI = "mongodb://localhost:27017"
    MONGO_DB_NAME = "textgrader"

try:
    from pedagogy import build_structured_feedback
    HAS_PEDAGOGY = True
except ImportError:
    HAS_PEDAGOGY = False
    print("⚠️  pedagogy.py não encontrado. Usando feedback estruturado básico.")

# Configurações
SENHA_PADRAO = "123456"
SENHA_HASH = bcrypt.hashpw(SENHA_PADRAO.encode('utf-8'), bcrypt.gensalt())  # bytes

PROFESSORES = [
    {"username": "prof_mariana", "nome": "Profa. Dra. Mariana Oliveira", "email": "mariana.oliveira@quintana.local"},
    {"username": "prof_rafael", "nome": "Prof. Dr. Rafael Mendes", "email": "rafael.mendes@quintana.local"},
    {"username": "prof_carla", "nome": "Profa. Ma. Carla Santos", "email": "carla.santos@quintana.local"},
]

TURMAS_POR_PROFESSOR = {
    "prof_mariana": ["3º Ano A - EM", "3º Ano B - EM"],
    "prof_rafael": ["2º Ano A - EM", "2º Ano B - EM"],
    "prof_carla": ["1º Ano A - EM", "1º Ano B - EM"],
}

ALUNOS_POR_TURMA = 20
ATIVIDADES_POR_TURMA = 5

NOMES_ALUNOS = ["João", "Maria", "Pedro", "Ana", "Lucas", "Fernanda", "Rafael", "Camila",
                "Bruno", "Juliana", "Carlos", "Patrícia", "André", "Tatiana", "Fábio",
                "Larissa", "Gustavo", "Renata", "Eduardo", "Cláudia", "Diego", "Vanessa",
                "Thiago", "Raquel", "Marcelo", "Natália", "Felipe", "Luciana", "Rodrigo", "Beatriz"]

SOBRENOMES = ["Silva", "Santos", "Oliveira", "Costa", "Lima", "Souza", "Alves", "Rocha",
              "Pereira", "Gomes", "Mendes", "Dias", "Ribeiro", "Monteiro", "Cunha",
              "Duarte", "Farias", "Cardoso", "Soares", "Azevedo", "Batista", "Pinto",
              "Neves", "Moura", "Maia", "Castro", "Borges", "Lopes", "Moreira", "Correia"]


def gerar_data_iso(offset_dias: int = 0, hora: int = 12) -> str:
    data = datetime.now() - timedelta(days=offset_dias)
    data = data.replace(hour=hora, minute=0, second=0, microsecond=0)
    return data.isoformat() + "+00:00"


class CorpusLoader:
    def __init__(self, mongo_uri: str, seed_batch: str, db_name: str = MONGO_DB_NAME):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.seed_batch = seed_batch
        self.professores = {}
        self.alunos = {}
        self.temas = {}
        self.turmas = {}
        self.alunos_por_turma = {}
        self.atividades_por_turma = {}

    def criar_indices(self):
        print("\n🔎 GARANTINDO ÍNDICES")
        self.db.users.create_index("email")
        self.db.users.create_index("username")
        self.db.users.create_index("tipoUsuario")
        self.db.users.create_index("seed_batch")
        self.db.temas.create_index("nome_professor")
        self.db.temas.create_index("seed_batch")
        self.db.classes.create_index("teacher")
        self.db.classes.create_index("students")
        self.db.classes.create_index("seed_batch")
        self.db.activities.create_index("teacher")
        self.db.activities.create_index("class_id")
        self.db.activities.create_index([("teacher", 1), ("class_id", 1)])
        self.db.activities.create_index("theme_id")
        self.db.activities.create_index("seed_batch")
        self.db.redacoes.create_index("aluno")
        self.db.redacoes.create_index([("aluno", 1), ("created_at", -1)])
        self.db.redacoes.create_index("class_id")
        self.db.redacoes.create_index([("class_id", 1), ("created_at", -1)])
        self.db.redacoes.create_index("activity_id")
        self.db.redacoes.create_index([("activity_id", 1), ("aluno", 1)])
        self.db.redacoes.create_index("id_tema")
        self.db.redacoes.create_index([("id_tema", 1), ("created_at", -1)])
        self.db.redacoes.create_index("version_group_id")
        self.db.redacoes.create_index("is_latest_version")
        self.db.redacoes.create_index("created_at")
        self.db.redacoes.create_index("seed_batch")
        print("   ✅ Índices prontos")

    def limpar_dados_anteriores(self):
        print(f"\n🧹 Limpando dados anteriores com seed_batch: {self.seed_batch}")
        for colecao in ["users", "temas", "classes", "activities", "redacoes"]:
            result = self.db[colecao].delete_many({"seed_batch": self.seed_batch})
            if result.deleted_count > 0:
                print(f"   - {colecao}: {result.deleted_count} removidos")

    def criar_usuarios(self):
        print("\n👥 CRIANDO USUÁRIOS")
        
        # Professores
        for prof in PROFESSORES:
            user_data = {
                "email": prof["email"],
                "password": SENHA_HASH,
                "username": prof["username"],
                "tipoUsuario": "professor",
                "seed_batch": self.seed_batch
            }
            result = self.db.users.insert_one(user_data)
            self.professores[prof["username"]] = result.inserted_id
            print(f"   ✅ Professor: {prof['username']}")
        
        # Alunos
        aluno_counter = 1
        for prof_username, turmas in TURMAS_POR_PROFESSOR.items():
            for turma_nome in turmas:
                turma_key = f"{prof_username}_{turma_nome}"
                self.alunos_por_turma[turma_key] = []
                
                for _ in range(ALUNOS_POR_TURMA):
                    nome = random.choice(NOMES_ALUNOS)
                    sobrenome = random.choice(SOBRENOMES)
                    username = f"aluno{aluno_counter:03d}"
                    
                    user_data = {
                        "email": f"{username}@quintana.local",
                        "password": SENHA_HASH,
                        "username": username,
                        "tipoUsuario": "aluno",
                        "seed_batch": self.seed_batch
                    }
                    
                    result = self.db.users.insert_one(user_data)
                    self.alunos[username] = result.inserted_id
                    self.alunos_por_turma[turma_key].append(username)
                    aluno_counter += 1
        
        print(f"   ✅ Total de {aluno_counter - 1} alunos criados")

    def criar_temas(self, redacoes_por_tema: Dict[str, List[Dict]]):
        print("\n📚 CRIANDO TEMAS")
        
        for i, tema_nome in enumerate(redacoes_por_tema.keys()):
            if "beleza" in tema_nome.lower() or "mulher" in tema_nome.lower():
                professor_username = "prof_mariana"
            elif "autoridade" in tema_nome.lower() or "abuso" in tema_nome.lower():
                professor_username = "prof_rafael"
            else:
                professor_username = PROFESSORES[i % len(PROFESSORES)]["username"]
            
            tema_data = {
                "nome_professor": professor_username,
                "tema": tema_nome,
                "descricao": f"Proposta de redação sobre: {tema_nome}",
                "seed_batch": self.seed_batch
            }
            
            result = self.db.temas.insert_one(tema_data)
            self.temas[tema_nome] = {
                "id": result.inserted_id,
                "professor": professor_username
            }
            print(f"   ✅ Tema: {tema_nome[:50]}...")

    def criar_turmas(self):
        print("\n🏫 CRIANDO TURMAS")
        
        for prof_username, turmas_nomes in TURMAS_POR_PROFESSOR.items():
            for turma_nome in turmas_nomes:
                turma_key = f"{prof_username}_{turma_nome}"
                alunos_usernames = self.alunos_por_turma.get(turma_key, [])
                
                turma_data = {
                    "name": turma_nome,
                    "teacher": prof_username,
                    "students": alunos_usernames,
                    "created_at": gerar_data_iso(),
                    "updated_at": gerar_data_iso(),
                    "seed_batch": self.seed_batch
                }
                
                result = self.db.classes.insert_one(turma_data)
                self.turmas[turma_key] = {
                    "id": result.inserted_id,
                    "nome": turma_nome,
                    "professor": prof_username,
                    "alunos": alunos_usernames
                }
                print(f"   ✅ Turma '{turma_nome}': {len(alunos_usernames)} alunos")

    def criar_atividades(self, redacoes_por_tema: Dict[str, List[Dict]]):
        print("\n📝 CRIANDO ATIVIDADES")
        
        atividade_count = 0
        for turma_key, turma_info in self.turmas.items():
            professor_username = turma_info["professor"]
            
            temas_do_professor = [(nome, info) for nome, info in self.temas.items() 
                                  if info["professor"] == professor_username]
            
            if not temas_do_professor:
                continue
            
            self.atividades_por_turma[turma_key] = []
            
            for i in range(ATIVIDADES_POR_TURMA):
                tema_nome, tema_info = temas_do_professor[i % len(temas_do_professor)]
                
                semanas_offset = i - ATIVIDADES_POR_TURMA + 4
                data_criacao = gerar_data_iso(offset_dias=(semanas_offset * 7))
                due_date_obj = datetime.now() + timedelta(weeks=semanas_offset)
                due_date = due_date_obj.strftime("%Y-%m-%d")
                
                atividade_data = {
                    "title": f"Redação {i+1} - {tema_nome[:40]}",
                    "teacher": professor_username,
                    "class_id": str(turma_info["id"]),
                    "theme_id": str(tema_info["id"]),
                    "due_date": due_date,
                    "created_at": data_criacao,
                    "updated_at": data_criacao,
                    "seed_batch": self.seed_batch
                }
                
                result = self.db.activities.insert_one(atividade_data)
                self.atividades_por_turma[turma_key].append({
                    "id": result.inserted_id,
                    "tema": tema_nome,
                    "tema_id": str(tema_info["id"]),
                    "due_date_obj": due_date_obj
                })
                atividade_count += 1
        
        print(f"   ✅ {atividade_count} atividades criadas")

    def extrair_notas_para_feedback(self, redacao: Dict) -> Dict[str, float]:
        """Extrai notas no formato esperado pelo build_structured_feedback."""
        notas = {}
        
        # Mapeamento dos nomes das competências
        competencias_nomes = {
            1: "Domínio da modalidade escrita formal",
            2: "Compreender a proposta e aplicar conceitos das várias áreas de conhecimento para desenvolver o texto dissertativo-argumentativo em prosa",
            3: "Selecionar, relacionar, organizar e interpretar informações em defesa de um ponto de vista",
            4: "Conhecimento dos mecanismos linguísticos necessários para a construção da argumentação",
            5: "Proposta de intervenção com respeito aos direitos humanos"
        }
        
        # Pega as notas do array competencias
        if "competencias" in redacao and isinstance(redacao["competencias"], list):
            for i, comp in enumerate(redacao["competencias"][:5], 1):
                nota_raw = comp.get("nota", 0)
                
                if isinstance(nota_raw, str):
                    nota_raw = float(nota_raw) if nota_raw.replace('.', '').isdigit() else 0
                elif isinstance(nota_raw, (int, float)):
                    nota_raw = float(nota_raw)
                else:
                    nota_raw = 0
                
                if nota_raw > 0:
                    notas[competencias_nomes[i]] = nota_raw
        
        return notas

    # Dentro do método criar_redacoes:
    def criar_redacoes(self, redacoes_por_tema: Dict[str, List[Dict]]):
        print("\n✍️ CRIANDO REDAÇÕES")
        
        redacao_count = 0
        for turma_key, atividades in self.atividades_por_turma.items():
            turma_info = self.turmas[turma_key]
            alunos_turma = turma_info["alunos"]
            
            for atividade in atividades:
                tema_nome = atividade["tema"]
                redacoes_disponiveis = redacoes_por_tema.get(tema_nome, [])
                
                if not redacoes_disponiveis:
                    continue
                
                num_sem_entrega = max(1, int(len(alunos_turma) * 0.1))
                alunos_sem_entrega = set(random.sample(alunos_turma, min(num_sem_entrega, len(alunos_turma))))
                
                for aluno_username in alunos_turma:
                    if aluno_username in alunos_sem_entrega:
                        continue
                    
                    redacao_original = random.choice(redacoes_disponiveis)
                    
                    # Extrai notas no formato correto para o pedagogy
                    grades = self.extrair_notas_para_feedback(redacao_original)
                    
                    # Pega as notas individuais para salvar no banco
                    competencias_nomes_lista = list(grades.keys())
                    notas_valores = list(grades.values())
                    
                    # ============================================
                    # GERAR FEEDBACK ESTRUTURADO USANDO PEDAGOGY
                    # ============================================
                    feedback_structured = {}
                    feedback_structured_source = "fallback"
                    
                    if HAS_PEDAGOGY and grades:
                        try:
                            feedback_structured = build_structured_feedback(grades)
                            feedback_structured_source = "synthetic"
                        except Exception as e:
                            print(f"   ⚠️ Erro ao gerar feedback: {e}")
                            feedback_structured = self._gerar_feedback_basico(notas_valores)
                    else:
                        feedback_structured = self._gerar_feedback_basico(notas_valores)
                    
                    # Tenta extrair título do JSON
                    titulo = redacao_original.get("titulo", "")
                    if not titulo or titulo == "." or titulo == "Text" or titulo == "A":
                        titulo = redacao_original.get("titulo_redacao", "")
                    
                    # Se não tem título, usa o tema
                    if not titulo or len(titulo) < 3:
                        if "beleza" in tema_nome.lower():
                            titulos_opcoes = [
                                "Os Impactos da Ditadura da Beleza na Saúde da Mulher",
                                "Padrões de Beleza: Entre a Estética e o Sofrimento",
                                "A Construção Social da Beleza e Seus Reflexos",
                                "Quando a Busca pela Beleza se Torna Doença"
                            ]
                        else:
                            titulos_opcoes = [
                                "Os Limites do Poder: Análise do Abuso de Autoridade",
                                "Autoridade e Arbítrio: A Linha Tênue do Poder",
                                "Quando o Estado Abusa: Reflexões sobre Autoritarismo"
                            ]
                        titulo = random.choice(titulos_opcoes)
                    
                    # Data de submissão
                    due_date_obj = atividade["due_date_obj"]
                    if random.random() < 0.8:
                        dias_antes = random.randint(0, max(1, (datetime.now() - due_date_obj).days - 1))
                        submitted_at = gerar_data_iso(offset_dias=dias_antes, hora=random.randint(8, 20))
                    else:
                        dias_depois = random.randint(1, 10)
                        submitted_at = gerar_data_iso(offset_dias=-dias_depois, hora=random.randint(8, 20))
                    
                    # Texto original
                    texto_original = redacao_original.get("texto", redacao_original.get("texto_comentado", ""))
                    if not texto_original:
                        texto_original = f"Redação sobre {tema_nome}."
                    
                    # Remove título do texto se estiver duplicado
                    if titulo and texto_original.startswith(titulo):
                        texto_original = texto_original[len(titulo):].strip()
                        if texto_original.startswith('\n'):
                            texto_original = texto_original[1:].strip()
                    
                    # Calcula nota total
                    nota_total = sum(notas_valores) if notas_valores else 0
                    
                    # Pega cada nota individual
                    nota_c1 = notas_valores[0] if len(notas_valores) > 0 else 0
                    nota_c2 = notas_valores[1] if len(notas_valores) > 1 else 0
                    nota_c3 = notas_valores[2] if len(notas_valores) > 2 else 0
                    nota_c4 = notas_valores[3] if len(notas_valores) > 3 else 0
                    nota_c5 = notas_valores[4] if len(notas_valores) > 4 else 0
                    
                    redacao_data = {
                        "titulo": titulo,
                        "texto": texto_original,
                        "nota_total": int(nota_total),
                        "id_tema": atividade["tema_id"],
                        "aluno": aluno_username,
                        "nota_competencia_1_model": int(nota_c1),
                        "nota_competencia_2_model": int(nota_c2),
                        "nota_competencia_3_model": int(nota_c3),
                        "nota_competencia_4_model": int(nota_c4),
                        "nota_competencia_5_model": int(nota_c5),
                        "nota_professor": "",
                        "nota_competencia_1_professor": 0,
                        "nota_competencia_2_professor": 0,
                        "nota_competencia_3_professor": 0,
                        "nota_competencia_4_professor": 0,
                        "nota_competencia_5_professor": 0,
                        "feedback_llm": f"Nota total: {int(nota_total)}",
                        "feedback_professor": "",
                        "competencias": {},
                        "created_at": submitted_at,
                        "updated_at": submitted_at,
                        "submitted_at": submitted_at,
                        "version_group_id": None,
                        "parent_redacao_id": None,
                        "version_number": 1,
                        "feedback_structured": feedback_structured,
                        "feedback_structured_source": feedback_structured_source,
                        "rewrite_checklist_state": {},
                        "class_id": str(turma_info["id"]),
                        "activity_id": str(atividade["id"]),
                        "correction_source": "model",
                        "is_latest_version": True,
                        "schema_version": 1,
                        "seed_batch": self.seed_batch
                    }
                    
                    self.db.redacoes.insert_one(redacao_data)
                    redacao_count += 1
                    
                    if redacao_count % 50 == 0:
                        print(f"   📝 {redacao_count} redações criadas...")
        
        print(f"   ✅ {redacao_count} redações criadas")


    def _gerar_feedback_basico(self, notas: List[int]) -> Dict:
        """Gera feedback estruturado básico quando o pedagogy não está disponível."""
        competencias_nomes = [
            "Domínio da modalidade escrita formal",
            "Compreender a proposta e aplicar conceitos",
            "Selecionar, relacionar, organizar e interpretar informações",
            "Conhecimento dos mecanismos linguísticos",
            "Proposta de intervenção com respeito aos direitos humanos"
        ]
        
        competencies = []
        for i, nota in enumerate(notas[:5]):
            if nota < 120:
                diagnosis = "A competência ainda precisa de desenvolvimento significativo."
                suggestion = "Revise os conceitos básicos e pratique mais."
            elif nota < 160:
                diagnosis = "A competência está adequada, mas pode melhorar."
                suggestion = "Continue praticando e aprofundando os conhecimentos."
            else:
                diagnosis = "A competência está muito bem desenvolvida."
                suggestion = "Mantenha o bom trabalho e refine os detalhes."
            
            competencies.append({
                "code": f"C{i+1}",
                "title": competencias_nomes[i],
                "description": "",
                "score": nota,
                "diagnosis": diagnosis,
                "suggestion": suggestion,
                "practice_action": "Pratique com exercícios específicos para esta competência."
            })
        
        priorities = sorted(competencies, key=lambda x: x["score"])[:3]
        for rank, priority in enumerate(priorities):
            priority["rank"] = rank + 1
            priority["reason"] = "Menor nota entre as competências avaliadas."
            priority["next_action"] = priority.get("suggestion", "Revisar e praticar.")
        
        rewrite_checklist = [
            {"id": f"c{i+1}", "competency": f"C{i+1}", "label": f"Revisei os aspectos da competência C{i+1}?"}
            for i in range(5)
        ]
        
        return {
            "competencies": competencies,
            "priorities": priorities,
            "rewrite_checklist": rewrite_checklist
        }


def main():
    parser = argparse.ArgumentParser(description='Carrega dados no MongoDB para o Quintana')
    parser.add_argument('--input', nargs='+', help='Arquivos JSON de entrada')
    parser.add_argument('--mongo-uri', default=MONGO_URI, help='URI do MongoDB')
    parser.add_argument('--seed-batch', default='corpus_2026_01', help='Identificador do batch')
    parser.add_argument('--db-name', default=MONGO_DB_NAME, help='Nome do banco de dados')
    parser.add_argument('--clear-only', action='store_true', help='Apenas remove dados do seed_batch informado')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 CARGA DE DADOS PARA O QUINTANA (Respeitando schemas.py)")
    print("=" * 70)
    
    loader = CorpusLoader(args.mongo_uri, args.seed_batch, args.db_name)
    loader.criar_indices()

    if args.clear_only:
        loader.limpar_dados_anteriores()
        print("\n✅ Limpeza concluída.")
        return

    if not args.input:
        parser.error("--input é obrigatório quando --clear-only não é usado")

    # Carregar corpus
    redacoes_por_tema = {}
    for arquivo in args.input:
        if not os.path.exists(arquivo):
            print(f"❌ Arquivo não encontrado: {arquivo}")
            continue
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        if isinstance(dados, list):
            for item in dados:
                tema = item.get("tema", "Tema não especificado")
                redacoes_por_tema.setdefault(tema, []).append(item)
        else:
            tema = dados.get("tema", "Tema não especificado")
            redacoes_por_tema.setdefault(tema, []).append(dados)
    
    print(f"✅ {sum(len(v) for v in redacoes_por_tema.values())} redações em {len(redacoes_por_tema)} temas")
    
    loader.limpar_dados_anteriores()
    loader.criar_usuarios()
    loader.criar_temas(redacoes_por_tema)
    loader.criar_turmas()
    loader.criar_atividades(redacoes_por_tema)
    loader.criar_redacoes(redacoes_por_tema)
    
    print("\n" + "=" * 70)
    print("🎉 CARGA CONCLUÍDA!")
    print("=" * 70)
    print(f"\n📊 Totais:")
    print(f"   Users: {loader.db.users.count_documents({'seed_batch': args.seed_batch})}")
    print(f"   Temas: {loader.db.temas.count_documents({'seed_batch': args.seed_batch})}")
    print(f"   Classes: {loader.db.classes.count_documents({'seed_batch': args.seed_batch})}")
    print(f"   Activities: {loader.db.activities.count_documents({'seed_batch': args.seed_batch})}")
    print(f"   Redações: {loader.db.redacoes.count_documents({'seed_batch': args.seed_batch})}")
    
    print(f"\n🔑 Senha padrão: {SENHA_PADRAO}")
    print("   Professores: prof_mariana, prof_rafael, prof_carla")
    print("   Alunos: aluno001 a aluno120")


if __name__ == "__main__":
    main()
