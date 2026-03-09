"""
PowerStudy - Registrar Sessão de Estudo (com Timer integrado)
"""
import streamlit as st
from datetime import datetime, date
from database import db
from services import scoring
from components import timer


def render():
    st.markdown("## 📝 Registrar Estudo")

    subjects = db.get_subjects()
    if not subjects:
        st.warning("⚠️ Nenhuma matéria cadastrada! Vá em **Matérias** para adicionar.")
        return

    # ─── Duas formas de registrar ────
    tab_timer, tab_manual = st.tabs(["⏱️ Timer (Pomodoro / Cronômetro)", "✍️ Registro Manual"])

    # ─── Tab 1: Timer ────
    with tab_timer:
        col_subject, col_date = st.columns(2)
        with col_subject:
            timer_subject = st.selectbox(
                "📚 Matéria",
                options=subjects,
                format_func=lambda s: f"{s['name']} (Sem. {s['semester']})",
                key="timer_subject",
            )
        with col_date:
            timer_date = st.date_input("📅 Data", value=date.today(), key="timer_date")

        # Timer (retorna minutos estudados)
        timer_minutes = timer.render_timer()

        timer_topic = st.text_input("📖 Tópico estudado (opcional)", key="timer_topic")
        timer_notes = st.text_area("📝 Notas (opcional)", height=60, key="timer_notes")

        if st.button("✅ Registrar Sessão", use_container_width=True, key="submit_timer"):
            if timer_minutes <= 0:
                st.error("❌ Use o timer ou preencha os minutos antes de registrar!")
            else:
                db.add_session(
                    subject_id=timer_subject["id"],
                    date=timer_date.isoformat(),
                    duration_minutes=timer_minutes,
                    topic=timer_topic,
                    notes=timer_notes,
                )
                pts = scoring.calculate_session_points(timer_minutes)
                st.success(f"✅ Sessão de **{timer_minutes} min** registrada! **+{pts['total_points']} pontos**")
                if pts["bonuses"]:
                    for bonus in pts["bonuses"]:
                        st.info(bonus)
                # Reset timer
                if "timer_state" in st.session_state:
                    del st.session_state["timer_state"]
                st.balloons()

    # ─── Tab 2: Manual ────
    with tab_manual:
        with st.form("study_form", clear_on_submit=True):
            st.markdown("### Nova Sessão de Estudo")

            col1, col2 = st.columns(2)
            with col1:
                subject = st.selectbox(
                    "📚 Matéria",
                    options=subjects,
                    format_func=lambda s: f"{s['name']} (Sem. {s['semester']})",
                )
            with col2:
                study_date = st.date_input("📅 Data", value=date.today())

            col3, col4 = st.columns(2)
            with col3:
                hours = st.number_input("⏱️ Horas", min_value=0, max_value=24, value=1)
            with col4:
                minutes = st.number_input("⏱️ Minutos", min_value=0, max_value=59, value=0, step=5)

            topic = st.text_input("📖 Tópico estudado (opcional)")
            notes = st.text_area("📝 Notas (opcional)", height=80)

            submitted = st.form_submit_button("✅ Registrar Sessão", use_container_width=True)

            if submitted:
                total_minutes = hours * 60 + minutes
                if total_minutes <= 0:
                    st.error("❌ A duração deve ser maior que zero!")
                else:
                    db.add_session(
                        subject_id=subject["id"],
                        date=study_date.isoformat(),
                        duration_minutes=total_minutes,
                        topic=topic,
                        notes=notes,
                    )
                    pts = scoring.calculate_session_points(total_minutes)
                    st.success(f"✅ Sessão registrada! **+{pts['total_points']} pontos**")
                    if pts["bonuses"]:
                        for bonus in pts["bonuses"]:
                            st.info(bonus)
                    st.balloons()

    st.markdown("---")

    # ─── Histórico ────
    st.markdown("### 📋 Histórico de Sessões")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_subject = st.selectbox(
            "Filtrar por matéria",
            options=[None] + subjects,
            format_func=lambda s: "Todas" if s is None else s["name"],
            key="filter_subject",
        )
    with col_f2:
        semesters = sorted(set(s["semester"] for s in subjects))
        filter_semester = st.selectbox(
            "Filtrar por semestre",
            options=[None] + semesters,
            format_func=lambda s: "Todos" if s is None else f"Semestre {s}",
            key="filter_semester",
        )

    sessions = db.get_sessions(
        subject_id=filter_subject["id"] if filter_subject else None,
        semester=filter_semester,
    )

    if sessions:
        for s in sessions:
            hours_display = s["duration_minutes"] / 60
            col_s, col_del = st.columns([9, 1])
            with col_s:
                st.markdown(
                    f"<div class='session-card'>"
                    f"<span style='color:{s['subject_color']};font-weight:700'>"
                    f"{s['subject_name']}</span> "
                    f"— **{hours_display:.1f}h** "
                    f"{'| ' + s['topic'] if s['topic'] else ''} "
                    f"<span style='opacity:0.6'>({s['date']})</span>"
                    f"{'<br><small>' + s['notes'] + '</small>' if s['notes'] else ''}"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with col_del:
                if st.button("🗑️", key=f"del_session_{s['id']}"):
                    db.delete_session(s["id"])
                    st.rerun()
    else:
        st.info("📝 Nenhuma sessão encontrada com os filtros selecionados.")
