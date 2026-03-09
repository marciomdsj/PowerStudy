"""
PowerStudy - Plano de Aula (Upload PDF + IA) — Suporta múltiplos planos por matéria
"""
import streamlit as st
from database import db
from services import pdf_parser, ai_recommender


def render():
    st.markdown("## 📄 Plano de Aula & Recomendações IA")

    subjects = db.get_subjects()
    if not subjects:
        st.warning("⚠️ Cadastre matérias primeiro em **Matérias**!")
        return

    has_ai = ai_recommender.is_configured()

    # ─── Selecionar Matéria ────
    subject = st.selectbox(
        "📚 Selecione a matéria",
        options=subjects,
        format_func=lambda s: f"{s['name']} (Sem. {s['semester']})",
    )

    syllabi = db.get_syllabi(subject["id"])

    # ─── Progresso geral da matéria ────
    overall_progress = db.get_syllabus_progress(subject_id=subject["id"])
    if overall_progress["total"] > 0:
        st.markdown(
            f"**Progresso geral:** {overall_progress['studied']}/{overall_progress['total']} "
            f"tópicos ({overall_progress['percentage']}%)"
        )
        st.progress(overall_progress["percentage"] / 100)

    st.markdown("---")

    # ─── Criar novo plano de aula ────
    col_title, col_btn = st.columns([4, 1])
    with col_title:
        st.markdown(f"### 📋 Planos de Aula ({len(syllabi)})")
    with col_btn:
        if st.button("➕ Novo Plano"):
            st.session_state[f"show_new_syllabus_{subject['id']}"] = True

    # Formulário para criar novo plano
    if st.session_state.get(f"show_new_syllabus_{subject['id']}", False):
        with st.form(f"new_syllabus_{subject['id']}", clear_on_submit=True):
            name = st.text_input("Nome do plano de aula", placeholder="Ex: Plano Semestre 2026.1")
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Criar", use_container_width=True):
                    if name.strip():
                        db.add_syllabus(subject["id"], name.strip())
                        st.session_state[f"show_new_syllabus_{subject['id']}"] = False
                        st.rerun()
                    else:
                        st.error("❌ Nome é obrigatório!")
            with col2:
                if st.form_submit_button("❌ Cancelar", use_container_width=True):
                    st.session_state[f"show_new_syllabus_{subject['id']}"] = False
                    st.rerun()

    if not syllabi:
        st.info("📝 Nenhum plano de aula criado. Clique em **➕ Novo Plano** para começar!")
        return

    # ─── Tabs para cada plano de aula ────
    tab_labels = [f"📄 {s['name']}" for s in syllabi]
    tabs = st.tabs(tab_labels)

    for tab, syl in zip(tabs, syllabi):
        with tab:
            _render_syllabus_tab(syl, subject, has_ai)


def _render_syllabus_tab(syl: dict, subject: dict, has_ai: bool):
    """Renderiza o conteúdo de uma tab de plano de aula."""
    syllabus_id = syl["id"]

    # Header com ações
    col_info, col_del = st.columns([8, 2])
    with col_info:
        st.caption(f"Criado em: {syl['created_at'][:10] if syl.get('created_at') else 'N/A'}")
    with col_del:
        if st.button("🗑️ Remover Plano", key=f"del_syl_{syllabus_id}"):
            db.delete_syllabus(syllabus_id)
            st.rerun()

    inner_tab1, inner_tab2, inner_tab3 = st.tabs(
        ["📤 Upload/Adicionar", "📋 Tópicos", "🤖 Recomendações IA"]
    )

    # ─── Upload / Adicionar tópicos ────
    with inner_tab1:
        st.markdown("#### 📤 Upload de PDF")
        uploaded_file = st.file_uploader(
            "Escolha o PDF do plano de aula",
            type=["pdf"],
            key=f"pdf_{syllabus_id}",
        )

        if uploaded_file:
            pdf_bytes = uploaded_file.read()
            with st.spinner("📖 Extraindo texto do PDF..."):
                text = pdf_parser.extract_text_from_pdf(pdf_bytes)

            if text:
                st.success("✅ Texto extraído com sucesso!")
                with st.expander("📄 Ver texto extraído"):
                    st.text(text[:3000] + ("..." if len(text) > 3000 else ""))

                method = st.radio(
                    "Método de extração:",
                    ["🤖 IA" if has_ai else "🤖 IA (requer config)", "📝 Automático (regex)"],
                    index=0 if has_ai else 1,
                    key=f"method_{syllabus_id}",
                )

                if st.button("🔍 Extrair Tópicos", key=f"extract_{syllabus_id}", use_container_width=True):
                    with st.spinner("Extraindo tópicos..."):
                        if method.startswith("🤖") and has_ai:
                            topics = ai_recommender.extract_topics_with_ai(text, subject["name"])
                        else:
                            topics = pdf_parser.extract_topics_from_text(text)

                    if topics:
                        st.session_state[f"extracted_topics_{syllabus_id}"] = topics
                        st.session_state[f"extracted_pdf_name_{syllabus_id}"] = uploaded_file.name
                        st.success(f"✅ {len(topics)} tópicos encontrados!")

                # Mostrar tópicos extraídos e botão salvar
                if f"extracted_topics_{syllabus_id}" in st.session_state:
                    topics = st.session_state[f"extracted_topics_{syllabus_id}"]
                    pdf_name = st.session_state.get(f"extracted_pdf_name_{syllabus_id}", "PDF")
                    st.markdown(f"**Fonte:** `{pdf_name}` — {len(topics)} tópicos")
                    for i, t in enumerate(topics, 1):
                        st.markdown(f"  {i}. {t}")
                    if st.button("💾 Adicionar Tópicos (acumula com existentes)", key=f"save_pdf_{syllabus_id}", use_container_width=True):
                        # Adiciona separador de seção + tópicos ao final
                        section_name = pdf_name.replace(".pdf", "").replace(".PDF", "")
                        section_topics = [f"── {section_name} ──"] + topics
                        db.append_syllabus_topics(syllabus_id, subject["id"], section_topics)
                        del st.session_state[f"extracted_topics_{syllabus_id}"]
                        st.session_state.pop(f"extracted_pdf_name_{syllabus_id}", None)
                        st.success(f"✅ {len(topics)} tópicos adicionados!")
                        st.rerun()
            else:
                st.error("❌ Não foi possível extrair texto deste PDF.")

        st.markdown("---")
        st.markdown("#### ✏️ Adicionar Tópicos Manualmente")
        with st.form(f"manual_{syllabus_id}", clear_on_submit=True):
            section_label = st.text_input(
                "📌 Nome da seção (opcional)",
                placeholder="Ex: Unidade 1, Módulo A",
                key=f"section_label_{syllabus_id}",
            )
            manual_topics = st.text_area(
                "Um tópico por linha:",
                height=120,
                placeholder="Introdução à Álgebra\nEquações Lineares\nMatrizes e Determinantes",
                key=f"manual_text_{syllabus_id}",
            )
            if st.form_submit_button("💾 Adicionar Tópicos", use_container_width=True):
                topics = [t.strip() for t in manual_topics.split("\n") if t.strip()]
                if topics:
                    to_add = []
                    if section_label.strip():
                        to_add.append(f"── {section_label.strip()} ──")
                    to_add.extend(topics)
                    db.append_syllabus_topics(syllabus_id, subject["id"], to_add)
                    st.success(f"✅ {len(topics)} tópicos adicionados!")
                    st.rerun()

    # ─── Checklist ────
    with inner_tab2:
        topics = db.get_syllabus_topics(syllabus_id=syllabus_id)
        if not topics:
            st.info("📝 Nenhum tópico cadastrado. Faça upload de um PDF ou adicione manualmente.")
            return

        progress = db.get_syllabus_progress(syllabus_id=syllabus_id)
        st.markdown(f"**Progresso: {progress['studied']}/{progress['total']} ({progress['percentage']}%)**")
        st.progress(progress["percentage"] / 100)
        st.markdown("---")

        for topic in topics:
            name = topic["topic_name"]
            # Separador de seção
            if name.startswith("──") and name.endswith("──"):
                st.markdown(f"\n**📌 {name.strip('── ').strip()}**")
                st.markdown("---")
                continue

            col_check, col_name = st.columns([1, 9])
            with col_check:
                st.checkbox(
                    "",
                    value=bool(topic["is_studied"]),
                    key=f"topic_{topic['id']}",
                    on_change=_toggle_topic,
                    args=(topic["id"],),
                )
            with col_name:
                if topic["is_studied"]:
                    st.markdown(f"~~{name}~~ ✅")
                else:
                    st.markdown(name)

    # ─── Recomendações IA ────
    with inner_tab3:
        if not has_ai:
            st.warning("⚠️ Configure a IA no sidebar para usar esta funcionalidade!")
            st.markdown("""
            **Recomendado: Groq (gratuito)**
            1. Acesse [console.groq.com](https://console.groq.com)
            2. Crie uma conta com Google
            3. Vá em API Keys → Create
            4. Cole no sidebar (seção 🤖 Configurar IA)
            """)
            return

        topics = db.get_syllabus_topics(syllabus_id=syllabus_id)
        if not topics:
            st.info("📝 Cadastre tópicos primeiro para receber recomendações!")
            return

        all_topics = [t["topic_name"] for t in topics]
        studied = [t["topic_name"] for t in topics if t["is_studied"]]
        hours = db.get_total_hours(subject_id=subject["id"])
        session_count = len(db.get_sessions(subject_id=subject["id"]))

        if st.button("🔮 Gerar Recomendações", key=f"rec_{syllabus_id}", use_container_width=True):
            with st.spinner("🤖 A IA está analisando seu progresso..."):
                recommendations = ai_recommender.get_study_recommendations(
                    subject_name=subject["name"],
                    all_topics=all_topics,
                    studied_topics=studied,
                    study_hours=hours,
                    total_sessions=session_count,
                )
            st.markdown("---")
            st.markdown(recommendations)


def _toggle_topic(topic_id: int):
    db.toggle_topic_studied(topic_id)
