"""
PowerStudy - Gamificação (Pontuação, Níveis, Badges)
"""
import streamlit as st
from database import db
from services import scoring


def render():
    st.markdown("## 🏆 Gamificação")

    level_info = scoring.get_current_level()
    streak = db.get_streak()

    # ─── Nível Atual ────
    st.markdown("### 🎮 Seu Perfil")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="kpi-card" style="text-align:center">
            <div style="font-size:3rem">{level_info['level']['emoji']}</div>
            <div class="kpi-value">{level_info['level']['name']}</div>
            <div class="kpi-label">Nível Atual</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card" style="text-align:center">
            <div style="font-size:3rem">⭐</div>
            <div class="kpi-value">{level_info['points']}</div>
            <div class="kpi-label">Pontos Totais</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card" style="text-align:center">
            <div style="font-size:3rem">🔥</div>
            <div class="kpi-value">{streak}</div>
            <div class="kpi-label">Dias de Streak</div>
        </div>
        """, unsafe_allow_html=True)

    # Progresso para próximo nível
    if level_info["next_level"]:
        st.markdown(f"### ⬆️ Próximo Nível: {level_info['next_level']['emoji']} {level_info['next_level']['name']}")
        st.progress(level_info["progress"] / 100)
        st.caption(
            f"{level_info['points']:.0f} / {level_info['next_level']['min_points']} pts "
            f"({level_info['progress']}%) — "
            f"Faltam {level_info['next_level']['min_points'] - level_info['points']:.0f} pts"
        )
    else:
        st.markdown("### 🏆 NÍVEL MÁXIMO ATINGIDO!")
        st.balloons()

    st.markdown("---")

    # ─── Todos os Níveis ────
    st.markdown("### 📊 Todos os Níveis")
    for lvl in scoring.LEVELS:
        is_current = lvl["name"] == level_info["level"]["name"]
        is_achieved = level_info["points"] >= lvl["min_points"]
        style = "opacity:1;font-weight:700" if is_current else ("opacity:0.8" if is_achieved else "opacity:0.4")
        marker = " ← Você está aqui!" if is_current else (" ✅" if is_achieved else "")
        st.markdown(
            f"<div style='{style}'>"
            f"{lvl['emoji']} **{lvl['name']}** — {lvl['min_points']} pts{marker}"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ─── Badges por Matéria ────
    st.markdown("### 🏅 Badges por Matéria")

    subjects = db.get_subjects()
    if not subjects:
        st.info("📝 Cadastre matérias para ver os badges!")
        return

    for sub in subjects:
        badge_info = scoring.get_subject_badge(sub["id"])
        col_name, col_badge, col_progress = st.columns([3, 2, 5])

        with col_name:
            st.markdown(
                f"<span style='color:{sub['color']};font-weight:700'>{sub['name']}</span>",
                unsafe_allow_html=True,
            )
        with col_badge:
            if badge_info["badge"]:
                st.markdown(f"{badge_info['badge']['emoji']} **{badge_info['badge']['name']}**")
            else:
                st.markdown("🏁 Iniciante")
        with col_progress:
            if badge_info["next_badge"]:
                target = badge_info["next_badge"]["min_hours"]
                pct = min(badge_info["hours"] / target * 100, 100)
                st.progress(pct / 100)
                st.caption(
                    f"{badge_info['hours']}h / {target}h para "
                    f"{badge_info['next_badge']['emoji']} {badge_info['next_badge']['name']}"
                )
            else:
                st.progress(1.0)
                st.caption("🏆 Badge máximo!")

    st.markdown("---")

    # ─── Como funciona a pontuação ────
    with st.expander("ℹ️ Como funciona a pontuação?"):
        st.markdown(f"""
        **Pontos Base:** {scoring.POINTS_PER_HOUR} pontos por hora de estudo

        **Bônus de Streak:**
        - 🔥 3+ dias consecutivos: multiplicador **x{scoring.STREAK_BONUS_3}**
        - 🔥🔥 7+ dias consecutivos: multiplicador **x{scoring.STREAK_BONUS_7}**

        **Bônus de Variedade:**
        - 📚 3+ matérias diferentes na semana: multiplicador **x{scoring.VARIETY_BONUS}**

        **Badges por Matéria:**
        """)
        for badge in scoring.SUBJECT_BADGES:
            st.markdown(f"  - {badge['emoji']} **{badge['name']}**: {badge['min_hours']}h de estudo")
