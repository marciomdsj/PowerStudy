"""
PowerStudy - Página Principal (Dashboard)
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from database import db
from services import scoring


def render():
    st.markdown("## 📊 Dashboard")

    # ─── KPIs ────
    level_info = scoring.get_current_level()
    streak = db.get_streak()
    total_hours = db.get_total_hours()
    sessions = db.get_sessions()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{total_hours:.1f}h</div>
            <div class="kpi-label">Horas Estudadas</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">🔥 {streak}</div>
            <div class="kpi-label">Dias de Streak</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{level_info['level']['emoji']} {level_info['level']['name']}</div>
            <div class="kpi-label">Nível Atual</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">⭐ {level_info['points']}</div>
            <div class="kpi-label">Pontos Totais</div>
        </div>
        """, unsafe_allow_html=True)

    # ─── Barra de Progresso do Nível ────
    if level_info["next_level"]:
        st.markdown(f"**Progresso para {level_info['next_level']['emoji']} {level_info['next_level']['name']}**")
        st.progress(level_info["progress"] / 100)
        st.caption(f"{level_info['points']:.0f} / {level_info['next_level']['min_points']} pts ({level_info['progress']}%)")
    else:
        st.markdown("🏆 **Nível máximo atingido!**")

    st.markdown("---")

    # ─── Gráficos ────
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### ⏱️ Horas por Matéria")
        hours_data = db.get_hours_by_subject()
        if hours_data:
            df = pd.DataFrame(hours_data)
            fig = px.bar(
                df, x="name", y="total_hours",
                color="name",
                color_discrete_map={d["name"]: d["color"] for d in hours_data},
                labels={"name": "Matéria", "total_hours": "Horas"},
            )
            fig.update_layout(
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#E0E0E0",
                xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                margin=dict(t=10, b=10, l=10, r=10),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📝 Registre sessões de estudo para ver os gráficos!")

    with col_right:
        st.markdown("### 📅 Horas por Dia da Semana")
        weekday_data = db.get_hours_by_weekday()
        if any(v > 0 for v in weekday_data.values()):
            days_pt = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
            fig = px.bar(
                x=days_pt,
                y=[weekday_data[i] for i in range(7)],
                labels={"x": "Dia", "y": "Horas"},
                color_discrete_sequence=["#6C63FF"],
            )
            fig.update_layout(
                showlegend=False,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#E0E0E0",
                xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                margin=dict(t=10, b=10, l=10, r=10),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📝 Registre sessões para ver a distribuição semanal!")

    # ─── Heatmap de Estudos ────
    st.markdown("### 🟩 Heatmap de Estudos")
    study_dates = db.get_study_dates()
    if study_dates:
        _render_heatmap(study_dates)
    else:
        st.info("📝 O heatmap aparecerá quando você registrar sessões de estudo!")

    # ─── Metas Semanais ────
    goals = db.get_goals()
    if goals:
        st.markdown("### 🎯 Metas Semanais")
        for goal in goals:
            weekly = db.get_weekly_hours(goal["subject_id"])
            target = goal["weekly_hours_target"]
            pct = min(weekly / target * 100, 100) if target > 0 else 0
            color = "#4CAF50" if pct >= 100 else "#FF9800" if pct >= 50 else "#F44336"
            st.markdown(f"**{goal['subject_name']}** — {weekly:.1f}h / {target:.1f}h")
            st.progress(pct / 100)

    # ─── Sessões Recentes ────
    st.markdown("### 📝 Sessões Recentes")
    recent = db.get_sessions(limit=5)
    if recent:
        for s in recent:
            hours = s["duration_minutes"] / 60
            st.markdown(
                f"<div class='session-card'>"
                f"<span style='color:{s['subject_color']};font-weight:700'>{s['subject_name']}</span> "
                f"— {hours:.1f}h "
                f"{'| ' + s['topic'] if s['topic'] else ''} "
                f"<span style='opacity:0.6'>({s['date']})</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("📝 Nenhuma sessão registrada ainda. Vá em **Registrar Estudo** para começar!")


def _render_heatmap(study_dates):
    """Renderiza um heatmap estilo GitHub contributions."""
    if not study_dates:
        return

    # Criar DataFrame com os últimos 365 dias
    today = datetime.now().date()
    start = today - timedelta(days=364)
    date_range = pd.date_range(start, today)

    date_minutes = {d["date"]: d["total_minutes"] for d in study_dates}
    data = []
    for d in date_range:
        ds = d.strftime("%Y-%m-%d")
        data.append({
            "date": d,
            "week": (d - date_range[0]).days // 7,
            "weekday": d.weekday(),
            "minutes": date_minutes.get(ds, 0),
        })

    df = pd.DataFrame(data)
    fig = go.Figure(data=go.Heatmap(
        x=df["week"],
        y=df["weekday"],
        z=df["minutes"],
        colorscale=[
            [0, "#1a1a2e"],
            [0.01, "#16213e"],
            [0.25, "#0f3460"],
            [0.5, "#6C63FF"],
            [0.75, "#9D4EDD"],
            [1, "#E040FB"],
        ],
        showscale=False,
        hovertemplate="Semana %{x}<br>%{z} min estudados<extra></extra>",
    ))
    fig.update_layout(
        yaxis=dict(
            tickvals=[0, 1, 2, 3, 4, 5, 6],
            ticktext=["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"],
            gridcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(showticklabels=False, gridcolor="rgba(0,0,0,0)"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#E0E0E0",
        height=200,
        margin=dict(t=10, b=10, l=50, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)
