"""
PowerStudy - Integração com IA para recomendações de estudo
Suporta: Groq (Llama 3) e Google Gemini
"""


import time

MAX_RETRIES = 3
RETRY_DELAY_BASE = 5  # segundos

# Estado global do provider
_provider = None  # "groq" ou "gemini"
_groq_client = None


def configure_groq(api_key: str):
    """Configura o Groq (Llama 3)."""
    global _provider, _groq_client
    from groq import Groq
    _groq_client = Groq(api_key=api_key)
    _provider = "groq"


def configure_gemini(api_key: str):
    """Configura o Google Gemini."""
    global _provider
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    _provider = "gemini"


def is_configured() -> bool:
    return _provider is not None


def _call_ai(prompt: str, retries: int = MAX_RETRIES) -> str:
    """Chama a IA configurada com retry automático para rate limits."""
    for attempt in range(retries):
        try:
            if _provider == "groq":
                response = _groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000,
                )
                return response.choices[0].message.content
            elif _provider == "gemini":
                import google.generativeai as genai
                model = genai.GenerativeModel("gemini-2.0-flash")
                response = model.generate_content(prompt)
                return response.text
            else:
                return "⚠️ Nenhum provedor de IA configurado. Configure uma API Key no sidebar."
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower() or "rate" in error_str.lower():
                if attempt < retries - 1:
                    time.sleep(RETRY_DELAY_BASE * (attempt + 1))
                    continue
                else:
                    return (
                        "⚠️ **Limite de uso da API atingido.**\n\n"
                        "Tente novamente em alguns minutos.\n\n"
                        "**Dicas:**\n"
                        "- Aguarde ~1 minuto e tente novamente\n"
                        "- Se persistir, a cota diária pode ter acabado\n"
                    )
            else:
                return f"❌ Erro ao processar com IA: {error_str}"
    return "❌ Erro inesperado ao chamar a IA."


def extract_topics_with_ai(syllabus_text: str, subject_name: str) -> list:
    """Usa IA para extrair tópicos estruturados de um plano de aula."""
    prompt = f"""Analise o seguinte plano de aula/ementa da disciplina "{subject_name}" 
e extraia uma lista ordenada de tópicos de estudo. 

Retorne APENAS os tópicos, um por linha, sem numeração, sem bullets, sem explicações extras.
Cada linha deve ser um tópico conciso e claro.

Plano de aula:
{syllabus_text}
"""
    result = _call_ai(prompt)
    topics = [
        line.strip()
        for line in result.strip().split("\n")
        if line.strip() and len(line.strip()) > 2
    ]
    return topics


def get_study_recommendations(
    subject_name: str,
    all_topics: list,
    studied_topics: list,
    study_hours: float,
    total_sessions: int,
) -> str:
    """Gera recomendações personalizadas de estudo."""
    studied_list = "\n".join(f"  ✅ {t}" for t in studied_topics) if studied_topics else "  Nenhum tópico marcado como estudado"
    pending_list = "\n".join(f"  ⬜ {t}" for t in all_topics if t not in studied_topics) if all_topics else "  Sem tópicos cadastrados"

    prompt = f"""Você é um assistente educacional especializado. Com base nas informações abaixo,
forneça recomendações de estudo personalizadas em português brasileiro.

📚 Disciplina: {subject_name}
⏱️ Horas estudadas: {study_hours:.1f}h
📝 Sessões de estudo: {total_sessions}

Tópicos já estudados:
{studied_list}

Tópicos pendentes:
{pending_list}

Por favor, forneça:
1. 🎯 **Próximos tópicos recomendados** (os 3 mais prioritários, explicando por quê)
2. 📋 **Ordem de estudo sugerida** para os tópicos pendentes
3. 💡 **Dicas de estudo** específicas para esta disciplina
4. ⚠️ **Alertas** se houver tópicos que parecem fundamentais e ainda não foram estudados

Seja conciso mas útil. Use emojis para organizar.
"""
    return _call_ai(prompt)


def get_general_study_advice(
    subjects_data: list,
    total_hours: float,
    streak: int,
) -> str:
    """Gera conselhos gerais de estudo baseado no panorama geral."""
    subjects_summary = "\n".join(
        f"  - {s['name']}: {s['total_hours']:.1f}h ({s['session_count']} sessões)"
        for s in subjects_data
    )

    prompt = f"""Você é um coach de estudos universitários. Analise o panorama de estudos abaixo
e forneça conselhos personalizados em português brasileiro.

📊 Panorama Geral:
- Horas totais estudadas: {total_hours:.1f}h
- Streak atual: {streak} dias consecutivos

📚 Matérias e tempo dedicado:
{subjects_summary}

Forneça:
1. 📈 **Análise geral** do ritmo de estudos
2. ⚖️ **Equilíbrio entre matérias** - alguma está sendo negligenciada?
3. 🎯 **Sugestão de foco** para a próxima semana
4. 💪 **Motivação** personalizada

Seja breve, prático e motivador. Use emojis.
"""
    return _call_ai(prompt)
