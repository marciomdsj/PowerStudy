"""
⚡ PowerStudy — Dashboard de Estudos Universitários
Rastreie seu tempo, ganhe pontos, e deixe a IA guiar seus estudos.
"""
import streamlit as st
from database import db
from services import ai_recommender

# ──────────── Configuração da Página ────────────
st.set_page_config(
    page_title="⚡ PowerStudy",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────── CSS Customizado ────────────
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ──────────── Inicializar Banco de Dados ────────────
db.init_db()

# ──────────── Sidebar ────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 0">
        <div style="font-size:2.5rem">⚡</div>
        <h1 style="margin:0;font-size:1.8rem;
            background:linear-gradient(135deg,#6C63FF,#E040FB);
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent">
            PowerStudy
        </h1>
        <p style="opacity:0.6;margin-top:5px;font-size:0.85rem">
            Dashboard de Estudos
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Navegação
    page = st.radio(
        "📍 Navegação",
        options=[
            "📊 Dashboard",
            "📝 Registrar Estudo",
            "📚 Matérias",
            "📈 Analytics",
            "📄 Plano de Aula",
            "🏆 Gamificação",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Configuração da IA
    with st.expander("🤖 Configurar IA", expanded=not ai_recommender.is_configured()):
        provider = st.radio(
            "Provedor de IA",
            options=["🦙 Groq (Llama 3 — Recomendado)", "✨ Google Gemini"],
            help="Groq é gratuito e generoso. Gemini tem tier gratuito mais restrito.",
        )

        if provider.startswith("🦙"):
            api_key = st.text_input(
                "Groq API Key",
                type="password",
                value=st.session_state.get("groq_api_key", ""),
                help="Gratuita! Obtenha em console.groq.com",
            )
            if api_key:
                st.session_state["groq_api_key"] = api_key
                ai_recommender.configure_groq(api_key)
                st.success("✅ Groq (Llama 3) configurado!")
            else:
                st.session_state.pop("groq_api_key", None)
            st.markdown(
                "**Como obter (grátis):**\n"
                "1. Acesse [console.groq.com](https://console.groq.com)\n"
                "2. Crie uma conta com Google\n"
                "3. Vá em API Keys → Create\n"
                "4. Cole a key acima"
            )
        else:
            api_key = st.text_input(
                "Google Gemini API Key",
                type="password",
                value=st.session_state.get("gemini_api_key", ""),
                help="Obtenha em aistudio.google.com",
            )
            if api_key:
                st.session_state["gemini_api_key"] = api_key
                ai_recommender.configure_gemini(api_key)
                st.success("✅ Gemini configurado!")
            else:
                st.session_state.pop("gemini_api_key", None)

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;opacity:0.4;font-size:0.75rem'>"
        "PowerStudy v1.0 • Feito com ❤️ e Streamlit"
        "</div>",
        unsafe_allow_html=True,
    )

# ──────────── Roteamento de Páginas ────────────
if page == "📊 Dashboard":
    from components import dashboard
    dashboard.render()

elif page == "📝 Registrar Estudo":
    from components import study_session
    study_session.render()

elif page == "📚 Matérias":
    from components import subjects
    subjects.render()

elif page == "📈 Analytics":
    from components import analytics
    analytics.render()

elif page == "📄 Plano de Aula":
    from components import syllabus
    syllabus.render()

elif page == "🏆 Gamificação":
    from components import gamification
    gamification.render()
