from datetime import datetime
from io import BytesIO
from textwrap import wrap


COMPETENCIES = [
    ("C1", "Norma escrita", "nota_competencia_1_model"),
    ("C2", "Proposta e repertorio", "nota_competencia_2_model"),
    ("C3", "Argumentacao", "nota_competencia_3_model"),
    ("C4", "Coesao", "nota_competencia_4_model"),
    ("C5", "Intervencao", "nota_competencia_5_model"),
]


def _pdf_text(value):
    text = str(value or "")
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("latin-1", "replace").decode("latin-1")


class SimplePdf:
    def __init__(self, title="Relatorio Quintana"):
        self.title = title
        self.pages = []
        self.lines = []
        self.y = 800
        self.margin_left = 48
        self.line_height = 15
        self.page_width = 595
        self.page_height = 842

    def _new_page(self):
        if self.lines:
            self.pages.append(self.lines)
        self.lines = []
        self.y = 800

    def add_line(self, text="", size=10, bold=False):
        if self.y < 54:
            self._new_page()
        font = "F2" if bold else "F1"
        self.lines.append(f"BT /{font} {size} Tf {self.margin_left} {self.y} Td ({_pdf_text(text)}) Tj ET")
        self.y -= self.line_height if size <= 11 else self.line_height + 4

    def add_wrapped(self, text, size=10, bold=False, width=92):
        chunks = wrap(str(text or ""), width=width) or [""]
        for chunk in chunks:
            self.add_line(chunk, size=size, bold=bold)

    def add_gap(self, height=8):
        self.y -= height
        if self.y < 54:
            self._new_page()

    def render(self):
        if self.lines:
            self.pages.append(self.lines)

        objects = []
        objects.append("<< /Type /Catalog /Pages 2 0 R >>")
        page_refs = " ".join(f"{3 + index * 2} 0 R" for index in range(len(self.pages)))
        objects.append(f"<< /Type /Pages /Kids [{page_refs}] /Count {len(self.pages)} >>")

        for index, page_lines in enumerate(self.pages):
            page_obj = 3 + index * 2
            content_obj = page_obj + 1
            stream = "\n".join(page_lines)
            stream_bytes = stream.encode("latin-1", "replace")
            objects.append(
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.page_width} {self.page_height}] "
                f"/Resources << /Font << /F1 {3 + len(self.pages) * 2} 0 R /F2 {4 + len(self.pages) * 2} 0 R >> >> "
                f"/Contents {content_obj} 0 R >>"
            )
            objects.append(f"<< /Length {len(stream_bytes)} >>\nstream\n{stream}\nendstream")

        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")

        buffer = BytesIO()
        buffer.write(b"%PDF-1.4\n")
        offsets = [0]
        for number, obj in enumerate(objects, start=1):
            offsets.append(buffer.tell())
            buffer.write(f"{number} 0 obj\n{obj}\nendobj\n".encode("latin-1", "replace"))
        xref_pos = buffer.tell()
        buffer.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        buffer.write(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            buffer.write(f"{offset:010d} 00000 n \n".encode("ascii"))
        buffer.write(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("ascii")
        )
        return buffer.getvalue()


def average(values):
    numbers = [float(value or 0) for value in values]
    return sum(numbers) / len(numbers) if numbers else 0


def build_class_report_pdf(teacher_name, analytics, class_name=None, activity_name=None):
    pdf = SimplePdf("Relatorio da turma")
    scope = analytics.get("scope", {})
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    pdf.add_line("Quintana - Relatorio pedagogico da turma", size=16, bold=True)
    pdf.add_line(f"Professor: {teacher_name or 'Professor'}")
    pdf.add_line(f"Turma: {class_name or 'Todas as turmas'}")
    pdf.add_line(f"Atividade: {activity_name or 'Todas as atividades'}")
    pdf.add_line(f"Gerado em: {generated_at}")
    pdf.add_gap()
    pdf.add_line("Resumo", size=12, bold=True)
    pdf.add_line(f"Redacoes consideradas: {scope.get('essay_count', 0)}")
    pdf.add_line("Indicadores baseados nas notas automaticas geradas pela IA.")
    pdf.add_gap()

    pdf.add_line("Competencias que mais precisam de intervencao", size=12, bold=True)
    for item in (analytics.get("ranking") or [])[:5]:
        pdf.add_wrapped(
            f"{item.get('rank')}. {item.get('competency')} - {item.get('title')}: "
            f"media {round(item.get('average', 0))}/200; {item.get('below_120_percent', 0)}% abaixo de 120."
        )
    pdf.add_gap()

    pdf.add_line("Alertas pedagogicos", size=12, bold=True)
    alerts = analytics.get("alerts") or []
    if alerts:
        for item in alerts[:8]:
            pdf.add_wrapped(f"- {item.get('message')} Acao sugerida: {item.get('action')}")
    else:
        pdf.add_line("Nenhum alerta no recorte atual.")
    pdf.add_gap()

    pdf.add_line("Distribuicao por competencia", size=12, bold=True)
    for item in analytics.get("distribution") or []:
        pdf.add_wrapped(
            f"{item.get('competency')} - {item.get('title')}: media {round(item.get('average', 0))}, "
            f"mediana {round(item.get('median', 0))}, IQR {round(item.get('iqr', 0))}."
        )
    pdf.add_gap()

    pdf.add_line("Grupos por necessidade pedagogica", size=12, bold=True)
    groups = analytics.get("groups") or []
    if groups:
        for group in groups:
            students = ", ".join((group.get("students") or [])[:18])
            pdf.add_wrapped(f"{group.get('competency')} - {group.get('title')}: {students}")
            pdf.add_wrapped(f"Atividade sugerida: {group.get('recommended_activity')}", width=88)
    else:
        pdf.add_line("Sem grupos no recorte atual.")

    return pdf.render()


def build_student_report_pdf(teacher_name, student, redacoes):
    pdf = SimplePdf("Relatorio do aluno")
    student_name = student.get("display_name") if student else "Aluno"
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    pdf.add_line("Quintana - Relatorio pedagogico do aluno", size=16, bold=True)
    pdf.add_line(f"Professor: {teacher_name or 'Professor'}")
    pdf.add_line(f"Aluno: {student_name}")
    pdf.add_line(f"Gerado em: {generated_at}")
    pdf.add_line("Indicadores baseados nas notas automaticas geradas pela IA; revisoes do professor aparecem quando registradas.")
    pdf.add_gap()

    if not redacoes:
        pdf.add_line("Nao ha redacoes desse aluno no recorte selecionado.")
        return pdf.render()

    latest = [item for item in redacoes if item.get("is_latest_version") is not False]
    dataset = latest or redacoes
    total_average = average(item.get("nota_total") for item in dataset)
    pdf.add_line("Resumo", size=12, bold=True)
    pdf.add_line(f"Redacoes consideradas: {len(dataset)}")
    pdf.add_line(f"Media geral IA: {round(total_average)}/1000")
    professor_reviews = [item for item in dataset if (item.get("teacher_review") or {}).get("status") in ("accepted", "adjusted")]
    pdf.add_line(f"Revisoes do professor registradas: {len(professor_reviews)}")
    pdf.add_gap()

    pdf.add_line("Media por competencia", size=12, bold=True)
    for code, title, field in COMPETENCIES:
        pdf.add_line(f"{code} - {title}: {round(average(item.get(field) for item in dataset))}/200")
    pdf.add_gap()

    ordered = sorted(dataset, key=lambda item: item.get("submitted_at") or item.get("created_at") or "")
    if len(ordered) >= 2:
        first = ordered[0]
        last = ordered[-1]
        pdf.add_line("Evolucao", size=12, bold=True)
        pdf.add_line(f"Primeira redacao: {round(float(first.get('nota_total') or 0))}/1000")
        pdf.add_line(f"Ultima redacao: {round(float(last.get('nota_total') or 0))}/1000")
        pdf.add_line(f"Variacao: {round(float(last.get('nota_total') or 0) - float(first.get('nota_total') or 0))} pontos")
        for code, title, field in COMPETENCIES:
            delta = float(last.get(field) or 0) - float(first.get(field) or 0)
            pdf.add_line(f"{code}: {delta:+.0f}")
        pdf.add_gap()

    pdf.add_line("Redacoes recentes", size=12, bold=True)
    for item in ordered[-8:]:
        review = item.get("teacher_review") or {}
        review_status = review.get("status") or "pending"
        pdf.add_wrapped(
            f"- {item.get('titulo') or 'Sem titulo'}: nota IA {round(float(item.get('nota_total') or 0))}/1000; "
            f"versao {item.get('version_number', 1)}; revisao professor: {review_status}."
        )

    return pdf.render()
