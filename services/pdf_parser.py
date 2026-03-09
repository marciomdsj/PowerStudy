"""
PowerStudy - Extração de conteúdo de PDFs
"""
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extrai texto completo de um PDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    doc.close()
    return text.strip()


def extract_topics_from_text(text: str) -> list:
    """
    Tenta extrair tópicos de um texto de plano de aula.
    Busca por padrões comuns em planos de aula brasileiros.
    """
    lines = text.split("\n")
    topics = []

    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        # Ignora linhas muito curtas ou que são apenas números
        if line.replace(".", "").replace("-", "").strip().isdigit():
            continue
        # Busca linhas que parecem ser tópicos (começam com número, bullet, etc)
        if (
            line[0].isdigit()
            or line.startswith("-")
            or line.startswith("•")
            or line.startswith("*")
            or line.startswith("–")
        ):
            # Remove prefixo numérico/bullet
            cleaned = line.lstrip("0123456789.-•*–) ").strip()
            if cleaned and len(cleaned) > 3:
                topics.append(cleaned)

    return topics if topics else []
