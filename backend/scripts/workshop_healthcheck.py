#!/usr/bin/env python3
"""
Health check operacional para oficinas do Quintana.

Valida MongoDB, backend, login de professor/aluno e endpoints principais
usando tokens de autenticação.
"""

import argparse
import json
import sys
from urllib import error, request

from pymongo import MongoClient


def http_json(method, url, payload=None, token=None, timeout=10):
    headers = {"Accept": "application/json"}
    body = None

    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = request.Request(url, data=body, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
            return response.status, json.loads(response_body) if response_body else {}
    except error.HTTPError as exc:
        response_body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(response_body) if response_body else {}
        except json.JSONDecodeError:
            parsed = {"error": response_body}
        return exc.code, parsed


def check(condition, label, detail="", critical=True):
    icon = "OK" if condition else "FAIL"
    print(f"[{icon}] {label}{f' - {detail}' if detail else ''}")
    return bool(condition) or not critical


def login(backend_url, email, password, label):
    status, payload = http_json(
        "POST",
        f"{backend_url}/userLogin",
        {"email": email, "password": password},
    )
    ok = status == 200 and payload.get("token") and payload.get("nomeUsuario") and payload.get("userId")
    check(ok, f"Login {label}", f"status={status}")
    return payload if ok else None


def collection_counts(mongo_uri, db_name, seed_batch=None):
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    client.admin.command("ping")

    query = {"seed_batch": seed_batch} if seed_batch else {}
    return {
        "users": db.users.count_documents(query),
        "temas": db.temas.count_documents(query),
        "classes": db.classes.count_documents(query),
        "activities": db.activities.count_documents(query),
        "redacoes": db.redacoes.count_documents(query),
    }


def main():
    parser = argparse.ArgumentParser(description="Valida ambiente de oficina do Quintana")
    parser.add_argument("--backend-url", default="http://localhost:5000", help="URL do backend")
    parser.add_argument("--mongo-uri", default="mongodb://localhost:27017", help="URI do MongoDB")
    parser.add_argument("--db-name", default="textgrader", help="Nome do banco MongoDB")
    parser.add_argument("--seed-batch", default="", help="Filtra contagens por seed_batch")
    parser.add_argument("--professor-email", default="rafael.mendes@quintana.local", help="E-mail do professor de teste")
    parser.add_argument("--student-email", default="aluno001@quintana.local", help="E-mail do aluno de teste")
    parser.add_argument("--password", default="123456", help="Senha dos usuários de teste")
    args = parser.parse_args()

    backend_url = args.backend_url.rstrip("/")
    all_ok = True

    print("\n== MongoDB ==")
    try:
        counts = collection_counts(args.mongo_uri, args.db_name, args.seed_batch or None)
        all_ok &= check(True, "Conexão com MongoDB", args.db_name)
        for collection, count in counts.items():
            all_ok &= check(count > 0, f"Coleção {collection}", f"{count} documentos")
    except Exception as exc:
        all_ok &= check(False, "Conexão com MongoDB", str(exc))

    print("\n== Backend ==")
    try:
        status, payload = http_json("GET", f"{backend_url}/")
        all_ok &= check(status == 200 and payload.get("status") == "ok", "Health endpoint", f"status={status}")
    except Exception as exc:
        all_ok &= check(False, "Health endpoint", str(exc))

    print("\n== Autenticação ==")
    professor = login(backend_url, args.professor_email, args.password, "professor")
    student = login(backend_url, args.student_email, args.password, "aluno")
    all_ok &= bool(professor and student)

    if professor:
        professor_token = professor["token"]
        professor_id = professor["userId"]
        print("\n== Fluxo Professor ==")

        checks = [
            ("GET", "/temas", "Temas do professor"),
            ("GET", "/users/alunos", "Lista de alunos"),
            ("GET", "/classes", "Turmas"),
            ("GET", "/activities", "Atividades"),
            ("GET", "/redacoes?page=1&page_size=5", "Redações recebidas"),
            ("GET", f"/professores/{professor_id}/analytics", "Analytics do professor"),
        ]

        for method, path, label in checks:
            status, payload = http_json(method, f"{backend_url}{path}", token=professor_token)
            size = len(payload.get("items", payload)) if isinstance(payload, (dict, list)) else 0
            all_ok &= check(status == 200, label, f"status={status}, itens={size}")

    if student:
        student_token = student["token"]
        student_id = student["userId"]
        print("\n== Fluxo Aluno ==")

        checks = [
            ("GET", "/temas", "Temas disponíveis"),
            ("GET", "/redacoes?page=1&page_size=5", "Minhas redações"),
            ("GET", f"/students/{student_id}/activities", "Atividades do aluno"),
        ]

        for method, path, label in checks:
            status, payload = http_json(method, f"{backend_url}{path}", token=student_token)
            size = len(payload.get("items", payload)) if isinstance(payload, (dict, list)) else 0
            all_ok &= check(status == 200, label, f"status={status}, itens={size}")

    print("\n== Resultado ==")
    if all_ok:
        print("Ambiente pronto para smoke test manual.")
        return 0

    print("Ambiente com falhas. Corrija os itens FAIL antes da oficina.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
