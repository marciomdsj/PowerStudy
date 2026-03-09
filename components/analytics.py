"""
PowerStudy - Analytics e Gráficos
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from database import db


def render():
    st.markdown("## 📈 Analytics")

    subjects = db.get_subjects()
    if not subjects:
        st.info("📝 Cadastre matérias e registre sessões para ver as análises!")
        return

    # ─── Filtros ────
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        semesters = sorted(set(s["semester"] for s in subjects))
        filter_semester = st.selectbox(
            "📅 Semestre",
            options=[None] + semesters,
            format_func=lambda s: "Todos" if s is None else f"Semestre {s}",
        )
    with col_f2:
        filter_subject = st.selectbox(
            "📚 Matéria",
            options=[None] + subjects,
            format_func=lambda s: "Todas" if s is None else s["name"],
        )

    sessions = db.get_sessions(
        subject_id=filter_subject["id"] if filter_subject else None,
        semester=filter_semester,
    )

    if not sessions:
        st.info("📝 Nenhuma sessão encontrada com os filtros selecionados.")
        return

    df = pd.DataFrame(sessions)
    df["date"] = pd.to_datetime(df["date"])
    df["hours"] = df["duration_minutes"] / 60.0

    st.markdown("---")

    # ─── Evolução Temporal ────
    st.markdown("### 📈 Evolução Temporal")
    daily = df.groupby([df["date"].dt.date, "subject_name", "subject_color"]).agg(
        hours=("hours", "sum")
    ).reset_index()
    daily.columns = ["date", "subject_name", "subject_color", "hours"]

    color_map = {row["subject_name"]: row["subject_color"] for _, row in daily.iterrows()}

    fig = px.area(
        daily, x="date", y="hours", color="subject_name",
        color_discrete_map=color_map,
        labels={"date": "Data", "hours": "Horas", "subject_name": "Matéria"},
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#E0E0E0",
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=350,
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ─── Distribuição ────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🥧 Distribuição por Matéria")
        subj_hours = df.groupby(["subject_name", "subject_color"])["hours"].sum().reset_index()
        fig = px.pie(
            subj_hours, values="hours", names="subject_name",
            color="subject_name",
            color_discrete_map={row["subject_name"]: row["subject_color"] for _, row in subj_hours.iterrows()},
            hole=0.4,
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#E0E0E0",
            height=300,
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 📊 Sessões por Matéria")
        session_count = df.groupby(["subject_name", "subject_color"]).size().reset_index(name="count")
        fig = px.bar(
            session_count, x="subject_name", y="count",
            color="subject_name",
            color_discrete_map={row["subject_name"]: row["subject_color"] for _, row in session_count.iterrows()},
            labels={"subject_name": "Matéria", "count": "Sessões"},
        )
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#E0E0E0",
            xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            height=300,
            margin=dict(t=10, b=10, l=10, r=10),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ─── Horas por Semana ────
    st.markdown("### 📅 Horas por Semana")
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["year"] = df["date"].dt.year
    weekly = df.groupby(["year", "week"])["hours"].sum().reset_index()
    weekly["label"] = weekly.apply(lambda r: f"{r['year']}-S{r['week']:02d}", axis=1)

    fig = px.line(
        weekly, x="label", y="hours",
        markers=True,
        labels={"label": "Semana", "hours": "Horas"},
        color_discrete_sequence=["#6C63FF"],
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#E0E0E0",
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        height=300,
        margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ─── Estatísticas Gerais ────
    st.markdown("### 📊 Estatísticas")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("Total de Horas", f"{df['hours'].sum():.1f}h")
    with col_s2:
        st.metric("Sessões", len(df))
    with col_s3:
        if len(df) > 0:
            avg = df["hours"].mean()
            st.metric("Média por Sessão", f"{avg:.1f}h")
        else:
            st.metric("Média por Sessão", "0h")
    with col_s4:
        days_active = df["date"].dt.date.nunique()
        st.metric("Dias Ativos", days_active)
