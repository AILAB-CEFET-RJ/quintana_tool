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
    {"key": "prof_mariana", "nome": "Profa. Dra. Mariana Oliveira", "email": "mariana.oliveira@quintana.local"},
    {"key": "prof_rafael", "nome": "Prof. Dr. Rafael Mendes", "email": "rafael.mendes@quintana.local"},
    {"key": "prof_carla", "nome": "Profa. Ma. Carla Santos", "email": "carla.santos@quintana.local"},
]

TURMAS_POR_PROFESSOR = {
    "prof_mariana": ["3º Ano A - EM", "3º Ano B - EM"],
    "prof_rafael": ["2º Ano A - EM", "2º Ano B - EM"],
    "prof_carla": ["1º Ano A - EM", "1º Ano B - EM"],
}

ALUNOS_POR_TURMA = 20
ATIVIDADES_POR_TURMA = 5

COMPETENCIAS_NOMES = [
    "Domínio da modalidade escrita formal",
    "Compreender a proposta e aplicar conceitos das várias áreas de conhecimento para desenvolver o texto dissertativo-argumentativo em prosa",
    "Selecionar, relacionar, organizar e interpretar informações em defesa de um ponto de vista",
    "Conhecimento dos mecanismos linguísticos necessários para a construção da argumentação",
    "Proposta de intervenção com respeito aos direitos humanos"
]

DEMO_PROGRESS_PROFILES = {
    "aluno001": {
        "profile": "progressivo_c5",
        "label": "Progresso claro com foco em C5",
        "focus_competency": "C5",
        "scores": [
            [120, 120, 120, 120, 40],
            [120, 120, 120, 160, 80],
            [160, 120, 160, 160, 80],
            [160, 160, 160, 160, 120],
            [160, 160, 160, 160, 200],
        ],
        "rewrite_activity_index": 2,
        "rewrite_before_scores": [120, 120, 120, 160, 80],
    },
    "aluno002": {
        "profile": "melhora_argumentacao",
        "label": "Melhora gradual em argumentação",
        "focus_competency": "C3",
        "scores": [
            [120, 120, 80, 120, 120],
            [120, 120, 120, 120, 120],
            [120, 160, 120, 120, 120],
            [160, 160, 160, 120, 120],
            [160, 160, 200, 120, 120],
        ],
    },
    "aluno003": {
        "profile": "oscilante_mas_melhora",
        "label": "Trajetória oscilante, mas positiva",
        "focus_competency": "C4",
        "scores": [
            [120, 120, 120, 120, 120],
            [120, 120, 120, 80, 120],
            [160, 120, 120, 120, 120],
            [160, 120, 160, 120, 120],
            [160, 160, 160, 160, 120],
        ],
    },
}

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
    def __init__(self, mongo_uri: str, seed_batch: str, db_name: str = MONGO_DB_NAME, demo_progress: bool = False):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.seed_batch = seed_batch
        self.demo_progress = demo_progress
        self.professores = {}
        self.alunos = {}
        self.temas = {}
        self.turmas = {}
        self.alunos_por_turma = {}
        self.atividades_por_turma = {}

    def criar_indices(self):
        print("\n🔎 GARANTINDO ÍNDICES")
        self.db.users.create_index("email")
        self.db.users.create_index("display_name")
        self.db.users.create_index("tipoUsuario")
        self.db.users.create_index("seed_batch")
        self.db.temas.create_index("teacher_id")
        self.db.temas.create_index("seed_batch")
        self.db.classes.create_index("teacher_id")
        self.db.classes.create_index("student_ids")
        self.db.classes.create_index("seed_batch")
        self.db.activities.create_index("teacher_id")
        self.db.activities.create_index("class_id")
        self.db.activities.create_index([("teacher_id", 1), ("class_id", 1)])
        self.db.activities.create_index("theme_id")
        self.db.activities.create_index("seed_batch")
        self.db.redacoes.create_index("student_id")
        self.db.redacoes.create_index([("student_id", 1), ("created_at", -1)])
        self.db.redacoes.create_index("class_id")
        self.db.redacoes.create_index([("class_id", 1), ("created_at", -1)])
        self.db.redacoes.create_index("activity_id")
        self.db.redacoes.create_index([("activity_id", 1), ("student_id", 1)])
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
                "display_name": prof["nome"],
                "tipoUsuario": "professor",
                "seed_batch": self.seed_batch
            }
            result = self.db.users.insert_one(user_data)
            self.professores[prof["key"]] = {
                "id": str(result.inserted_id),
                "display_name": prof["nome"],
                "email": prof["email"],
            }
            print(f"   ✅ Professor: {prof['email']}")
        
        # Alunos
        aluno_counter = 1
        for prof_key, turmas in TURMAS_POR_PROFESSOR.items():
            for turma_nome in turmas:
                turma_key = f"{prof_key}_{turma_nome}"
                self.alunos_por_turma[turma_key] = []
                
                for _ in range(ALUNOS_POR_TURMA):
                    nome = random.choice(NOMES_ALUNOS)
                    sobrenome = random.choice(SOBRENOMES)
                    username = f"aluno{aluno_counter:03d}"
                    
                    user_data = {
                        "email": f"{username}@quintana.local",
                        "password": SENHA_HASH,
                        "display_name": f"{nome} {sobrenome}",
                        "tipoUsuario": "aluno",
                        "seed_batch": self.seed_batch
                    }
                    
                    result = self.db.users.insert_one(user_data)
                    self.alunos[username] = {
                        "id": str(result.inserted_id),
                        "username": username,
                        "display_name": user_data["display_name"],
                        "email": user_data["email"],
                    }
                    self.alunos_por_turma[turma_key].append(self.alunos[username])
                    aluno_counter += 1
        
        print(f"   ✅ Total de {aluno_counter - 1} alunos criados")

    def criar_temas(self, redacoes_por_tema: Dict[str, List[Dict]]):
        print("\n📚 CRIANDO TEMAS")
        
        for i, tema_nome in enumerate(redacoes_por_tema.keys()):
            if "beleza" in tema_nome.lower() or "mulher" in tema_nome.lower():
                professor_key = "prof_mariana"
            elif "autoridade" in tema_nome.lower() or "abuso" in tema_nome.lower():
                professor_key = "prof_rafael"
            else:
                professor_key = PROFESSORES[i % len(PROFESSORES)]["key"]
            professor = self.professores[professor_key]
            
            tema_data = {
                "teacher_id": professor["id"],
                "teacher_name": professor["display_name"],
                "tema": tema_nome,
                "descricao": f"Proposta de redação sobre: {tema_nome}",
                "seed_batch": self.seed_batch
            }
            
            result = self.db.temas.insert_one(tema_data)
            self.temas[tema_nome] = {
                "id": result.inserted_id,
                "professor_key": professor_key,
                "teacher_id": professor["id"]
            }
            print(f"   ✅ Tema: {tema_nome[:50]}...")

    def criar_turmas(self):
        print("\n🏫 CRIANDO TURMAS")
        
        for prof_key, turmas_nomes in TURMAS_POR_PROFESSOR.items():
            for turma_nome in turmas_nomes:
                turma_key = f"{prof_key}_{turma_nome}"
                alunos_turma = self.alunos_por_turma.get(turma_key, [])
                professor = self.professores[prof_key]
                
                turma_data = {
                    "name": turma_nome,
                    "teacher_id": professor["id"],
                    "student_ids": [aluno["id"] for aluno in alunos_turma],
                    "created_at": gerar_data_iso(),
                    "updated_at": gerar_data_iso(),
                    "seed_batch": self.seed_batch
                }
                
                result = self.db.classes.insert_one(turma_data)
                self.turmas[turma_key] = {
                    "id": result.inserted_id,
                    "nome": turma_nome,
                    "professor_key": prof_key,
                    "teacher_id": professor["id"],
                    "alunos": alunos_turma
                }
                print(f"   ✅ Turma '{turma_nome}': {len(alunos_turma)} alunos")

    def criar_atividades(self, redacoes_por_tema: Dict[str, List[Dict]]):
        print("\n📝 CRIANDO ATIVIDADES")
        
        atividade_count = 0
        for turma_key, turma_info in self.turmas.items():
            professor_key = turma_info["professor_key"]
            professor_id = turma_info["teacher_id"]
            
            temas_do_professor = [(nome, info) for nome, info in self.temas.items() 
                                  if info["professor_key"] == professor_key]
            
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
                    "teacher_id": professor_id,
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

    def normalizar_nota(self, nota_raw: Any) -> float:
        if isinstance(nota_raw, str):
            nota_raw = nota_raw.strip().replace(",", ".")
            return float(nota_raw) if nota_raw.replace('.', '', 1).isdigit() else 0
        if isinstance(nota_raw, (int, float)):
            return float(nota_raw)
        return 0

    def extrair_notas_lista(self, redacao: Dict) -> List[float]:
        notas = []

        # Pega as notas do array competencias
        if "competencias" in redacao and isinstance(redacao["competencias"], list):
            for i, comp in enumerate(redacao["competencias"][:5], 1):
                nota = self.normalizar_nota(comp.get("nota", 0))
                if nota > 0:
                    notas.append(nota)

        return notas[:5]

    def montar_grades(self, notas_valores: List[float]) -> Dict[str, float]:
        return {
            COMPETENCIAS_NOMES[i]: float(notas_valores[i])
            for i in range(min(len(notas_valores), len(COMPETENCIAS_NOMES)))
        }

    def extrair_notas_para_feedback(self, redacao: Dict) -> Dict[str, float]:
        """Extrai notas no formato esperado pelo build_structured_feedback."""
        return self.montar_grades(self.extrair_notas_lista(redacao))

    def calcular_total_redacao(self, redacao: Dict) -> float:
        nota_total = self.normalizar_nota(redacao.get("nota", 0))
        if nota_total > 0:
            return nota_total
        return sum(self.extrair_notas_lista(redacao))

    def escolher_redacao_por_nota(self, redacoes: List[Dict], nota_alvo: float) -> Dict:
        if not redacoes:
            return {}
        return min(redacoes, key=lambda item: abs(self.calcular_total_redacao(item) - nota_alvo))

    def get_demo_profile(self, aluno: Dict) -> Dict:
        if not self.demo_progress:
            return {}
        return DEMO_PROGRESS_PROFILES.get(aluno.get("username", ""), {})

    def get_demo_scores(self, profile: Dict, activity_index: int) -> List[int]:
        scores = profile.get("scores", [])
        if not scores:
            return []
        return scores[min(activity_index, len(scores) - 1)]

    def get_demo_submitted_at(self, activity_index: int, hour: int = 10) -> str:
        offsets = [35, 28, 21, 14, 7]
        offset = offsets[min(activity_index, len(offsets) - 1)]
        return gerar_data_iso(offset_dias=offset, hora=hour)

    def gerar_feedback_estruturado(self, grades: Dict[str, float], notas_valores: List[float]) -> tuple[Dict, str]:
        if HAS_PEDAGOGY and grades:
            try:
                return build_structured_feedback(grades), "synthetic"
            except Exception as e:
                print(f"   ⚠️ Erro ao gerar feedback: {e}")
        return self._gerar_feedback_basico(notas_valores), "fallback"

    def preparar_titulo_texto(self, redacao_original: Dict, tema_nome: str) -> tuple[str, str]:
        titulo = redacao_original.get("titulo", "")
        if not titulo or titulo == "." or titulo == "Text" or titulo == "A":
            titulo = redacao_original.get("titulo_redacao", "")

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

        texto_original = redacao_original.get("texto", redacao_original.get("texto_comentado", ""))
        if not texto_original:
            texto_original = f"Redação sobre {tema_nome}."

        if titulo and texto_original.startswith(titulo):
            texto_original = texto_original[len(titulo):].strip()
            if texto_original.startswith('\n'):
                texto_original = texto_original[1:].strip()

        return titulo, texto_original

    def montar_redacao_data(
        self,
        aluno: Dict,
        turma_info: Dict,
        atividade: Dict,
        tema_nome: str,
        redacao_original: Dict,
        notas_valores: List[float],
        submitted_at: str,
        demo_profile: Dict | None = None,
        demo_sequence_index: int | None = None,
        version_group_id: str | None = None,
        parent_redacao_id: str | None = None,
        version_number: int = 1,
        is_latest_version: bool = True,
    ) -> Dict:
        grades = self.montar_grades(notas_valores)
        feedback_structured, feedback_structured_source = self.gerar_feedback_estruturado(grades, notas_valores)
        titulo, texto_original = self.preparar_titulo_texto(redacao_original, tema_nome)

        nota_c1 = notas_valores[0] if len(notas_valores) > 0 else 0
        nota_c2 = notas_valores[1] if len(notas_valores) > 1 else 0
        nota_c3 = notas_valores[2] if len(notas_valores) > 2 else 0
        nota_c4 = notas_valores[3] if len(notas_valores) > 3 else 0
        nota_c5 = notas_valores[4] if len(notas_valores) > 4 else 0
        nota_total = sum(notas_valores) if notas_valores else 0

        redacao_data = {
            "titulo": titulo,
            "texto": texto_original,
            "nota_total": int(nota_total),
            "id_tema": atividade["tema_id"],
            "student_id": aluno["id"],
            "student_name": aluno["display_name"],
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
            "version_group_id": version_group_id,
            "parent_redacao_id": parent_redacao_id,
            "version_number": version_number,
            "feedback_structured": feedback_structured,
            "feedback_structured_source": feedback_structured_source,
            "rewrite_checklist_state": {},
            "class_id": str(turma_info["id"]),
            "activity_id": str(atividade["id"]),
            "correction_source": "model",
            "is_latest_version": is_latest_version,
            "schema_version": 1,
            "seed_batch": self.seed_batch
        }

        if demo_profile:
            redacao_data.update({
                "demo_profile": demo_profile.get("profile"),
                "demo_profile_label": demo_profile.get("label"),
                "demo_focus_competency": demo_profile.get("focus_competency"),
                "demo_sequence_index": demo_sequence_index,
                "demo_target_total": int(nota_total),
            })

        return redacao_data

    def criar_redacoes(self, redacoes_por_tema: Dict[str, List[Dict]]):
        print("\n✍️ CRIANDO REDAÇÕES")
        
        redacao_count = 0
        demo_rewrite_count = 0
        for turma_key, atividades in self.atividades_por_turma.items():
            turma_info = self.turmas[turma_key]
            alunos_turma = turma_info["alunos"]
            
            for activity_index, atividade in enumerate(atividades):
                tema_nome = atividade["tema"]
                redacoes_disponiveis = redacoes_por_tema.get(tema_nome, [])
                
                if not redacoes_disponiveis:
                    continue
                
                num_sem_entrega = max(1, int(len(alunos_turma) * 0.1))
                alunos_sem_entrega = {
                    aluno["id"]
                    for aluno in random.sample(alunos_turma, min(num_sem_entrega, len(alunos_turma)))
                }
                
                for aluno in alunos_turma:
                    demo_profile = self.get_demo_profile(aluno)
                    if aluno["id"] in alunos_sem_entrega and not demo_profile:
                        continue

                    if demo_profile:
                        notas_valores = self.get_demo_scores(demo_profile, activity_index)
                        target_total = sum(notas_valores)
                        redacao_original = self.escolher_redacao_por_nota(redacoes_disponiveis, target_total)
                        submitted_at = self.get_demo_submitted_at(activity_index)
                    else:
                        redacao_original = random.choice(redacoes_disponiveis)
                        notas_valores = self.extrair_notas_lista(redacao_original)

                        due_date_obj = atividade["due_date_obj"]
                        if random.random() < 0.8:
                            dias_antes = random.randint(0, max(1, (datetime.now() - due_date_obj).days - 1))
                            submitted_at = gerar_data_iso(offset_dias=dias_antes, hora=random.randint(8, 20))
                        else:
                            dias_depois = random.randint(1, 10)
                            submitted_at = gerar_data_iso(offset_dias=-dias_depois, hora=random.randint(8, 20))

                    if (
                        demo_profile
                        and demo_profile.get("rewrite_activity_index") == activity_index
                        and demo_profile.get("rewrite_before_scores")
                    ):
                        before_scores = demo_profile["rewrite_before_scores"]
                        before_redacao = self.montar_redacao_data(
                            aluno,
                            turma_info,
                            atividade,
                            tema_nome,
                            redacao_original,
                            before_scores,
                            gerar_data_iso(offset_dias=22, hora=10),
                            demo_profile=demo_profile,
                            demo_sequence_index=activity_index + 1,
                            version_number=1,
                            is_latest_version=False,
                        )
                        before_id = self.db.redacoes.insert_one(before_redacao).inserted_id
                        version_group_id = str(before_id)
                        self.db.redacoes.update_one(
                            {"_id": before_id},
                            {"$set": {"version_group_id": version_group_id}}
                        )

                        redacao_data = self.montar_redacao_data(
                            aluno,
                            turma_info,
                            atividade,
                            tema_nome,
                            redacao_original,
                            notas_valores,
                            submitted_at,
                            demo_profile=demo_profile,
                            demo_sequence_index=activity_index + 1,
                            version_group_id=version_group_id,
                            parent_redacao_id=version_group_id,
                            version_number=2,
                            is_latest_version=True,
                        )
                        self.db.redacoes.insert_one(redacao_data)
                        redacao_count += 2
                        demo_rewrite_count += 1
                    else:
                        redacao_data = self.montar_redacao_data(
                            aluno,
                            turma_info,
                            atividade,
                            tema_nome,
                            redacao_original,
                            notas_valores,
                            submitted_at,
                            demo_profile=demo_profile if demo_profile else None,
                            demo_sequence_index=activity_index + 1 if demo_profile else None,
                        )
                        self.db.redacoes.insert_one(redacao_data)
                        redacao_count += 1

                    if redacao_count % 50 == 0:
                        print(f"   📝 {redacao_count} redações criadas...")
        
        print(f"   ✅ {redacao_count} redações criadas")
        if self.demo_progress:
            print(f"   🎬 {demo_rewrite_count} reescrita(s) demonstrativa(s) criada(s)")


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
    parser.add_argument(
        '--demo-progress',
        action='store_true',
        help='Cria trajetórias controladas de progresso para alunos âncora usados em demonstrações'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🚀 CARGA DE DADOS PARA O QUINTANA (Respeitando schemas.py)")
    print("=" * 70)
    
    loader = CorpusLoader(args.mongo_uri, args.seed_batch, args.db_name, demo_progress=args.demo_progress)
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
    print("   Professores: mariana.oliveira@quintana.local, rafael.mendes@quintana.local, carla.santos@quintana.local")
    print("   Alunos: aluno001@quintana.local a aluno120@quintana.local")

    if args.demo_progress:
        print("\n🎬 Contas recomendadas para demonstração:")
        for username, profile in DEMO_PROGRESS_PROFILES.items():
            totals = [sum(scores) for scores in profile["scores"]]
            print(f"   {username}@quintana.local / {SENHA_PADRAO}")
            print(f"      {profile['label']}: {' -> '.join(str(total) for total in totals)}")
            print(f"      Foco pedagógico: {profile['focus_competency']}")
        print("   Professor sugerido: mariana.oliveira@quintana.local / 123456")


if __name__ == "__main__":
    main()
