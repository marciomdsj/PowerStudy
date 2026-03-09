"""
PowerStudy - Gerenciamento de Matérias
"""
import streamlit as st
from database import db

# Paleta de cores sugeridas
COLOR_PALETTE = [
    "#6C63FF",  # Roxo
    "#FF6B6B",  # Vermelho
    "#4ECDC4",  # Turquesa
    "#45B7D1",  # Azul
    "#96CEB4",  # Verde
    "#FFEAA7",  # Amarelo
    "#DDA0DD",  # Lilás
    "#FF8A5C",  # Laranja
    "#A8E6CF",  # Verde claro
    "#FF85A1",  # Rosa
    "#7EC8E3",  # Azul claro
    "#C9B1FF",  # Lavanda
]


def render():
    st.markdown("## 📚 Gerenciar Matérias")

    # ─── Adicionar nova matéria ────
    with st.form("add_subject_form", clear_on_submit=True):
        st.markdown("### ➕ Adicionar Matéria")
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            name = st.text_input("Nome da matéria")
        with col2:
            semester = st.number_input("Semestre", min_value=1, max_value=12, value=1)
        with col3:
            color = st.color_picker("Cor", value="#6C63FF")

        # Sugestões de cores
        st.markdown("**Cores sugeridas:**")
        color_cols = st.columns(len(COLOR_PALETTE))
        for i, c in enumerate(COLOR_PALETTE):
            with color_cols[i]:
                st.markdown(
                    f"<div style='width:20px;height:20px;border-radius:50%;background:{c};margin:auto'></div>",
                    unsafe_allow_html=True,
                )

        submitted = st.form_submit_button("✅ Adicionar", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("❌ Nome da matéria é obrigatório!")
            else:
                success = db.add_subject(name.strip(), semester, color)
                if success:
                    st.success(f"✅ **{name}** adicionada ao semestre {semester}!")
                    st.rerun()
                else:
                    st.error("❌ Matéria com esse nome já existe!")

    st.markdown("---")

    # ─── Lista de matérias ────
    st.markdown("### 📋 Matérias Cadastradas")
    subjects = db.get_subjects()

    if not subjects:
        st.info("📝 Nenhuma matéria cadastrada ainda. Adicione acima!")
        return

    # Agrupar por semestre
    semesters = sorted(set(s["semester"] for s in subjects))
    for sem in semesters:
        st.markdown(f"#### 🎓 Semestre {sem}")
        sem_subjects = [s for s in subjects if s["semester"] == sem]

        for sub in sem_subjects:
            col_info, col_hours, col_badge, col_actions = st.columns([4, 2, 2, 2])

            with col_info:
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:10px'>"
                    f"<div style='width:16px;height:16px;border-radius:50%;background:{sub['color']}'></div>"
                    f"<strong>{sub['name']}</strong>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col_hours:
                hours = db.get_total_hours(subject_id=sub["id"])
                st.markdown(f"⏱️ **{hours:.1f}h**")

            with col_badge:
                from services.scoring import get_subject_badge
                badge_info = get_subject_badge(sub["id"])
                if badge_info["badge"]:
                    st.markdown(f"{badge_info['badge']['emoji']} {badge_info['badge']['name']}")
                else:
                    st.markdown("🏁 Iniciante")

            with col_actions:
                if st.button("🗑️ Remover", key=f"del_sub_{sub['id']}"):
                    db.delete_subject(sub["id"])
                    st.rerun()

    # ─── Definir Metas ────
    st.markdown("---")
    st.markdown("### 🎯 Definir Metas Semanais")

    with st.form("goals_form"):
        for sub in subjects:
            current_goals = db.get_goals(semester=sub["semester"])
            current_target = 5.0
            for g in current_goals:
                if g["subject_id"] == sub["id"]:
                    current_target = g["weekly_hours_target"]
                    break

            col_name, col_target = st.columns([3, 2])
            with col_name:
                st.markdown(f"**{sub['name']}** (Sem. {sub['semester']})")
            with col_target:
                target = st.number_input(
                    f"Horas/semana",
                    min_value=0.5, max_value=40.0, value=current_target, step=0.5,
                    key=f"goal_{sub['id']}",
                )

        if st.form_submit_button("💾 Salvar Metas", use_container_width=True):
            for sub in subjects:
                target = st.session_state.get(f"goal_{sub['id']}", 5.0)
                db.set_goal(sub["id"], target, sub["semester"])
            st.success("✅ Metas atualizadas!")
            st.rerun()
