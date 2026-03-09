"""
PowerStudy - Calendário / Cronograma Semanal de Estudos
Grade visual interativa com horários por dia da semana.
"""
import streamlit as st
import streamlit.components.v1 as components
from database import db
import json


WEEKDAYS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
HOURS_RANGE = list(range(6, 24))  # 06:00 às 23:00


def render():
    st.markdown("## 📅 Cronograma Semanal")

    subjects = db.get_subjects()
    if not subjects:
        st.warning("⚠️ Cadastre matérias primeiro em **Matérias**!")
        return

    # ─── Adicionar evento ────
    tab_view, tab_add = st.tabs(["📅 Visualizar Cronograma", "➕ Adicionar Bloco de Estudo"])

    with tab_add:
        _render_add_event(subjects)

    with tab_view:
        _render_calendar(subjects)


def _render_add_event(subjects):
    """Formulário para adicionar um bloco de estudo ao cronograma."""
    with st.form("add_schedule_event", clear_on_submit=True):
        st.markdown("### ➕ Novo Bloco de Estudo")

        col1, col2 = st.columns(2)
        with col1:
            subject = st.selectbox(
                "📚 Matéria",
                options=subjects,
                format_func=lambda s: f"{s['name']} (Sem. {s['semester']})",
                key="sched_subject",
            )
        with col2:
            day = st.selectbox(
                "📅 Dia da semana",
                options=list(range(7)),
                format_func=lambda d: WEEKDAYS[d],
                key="sched_day",
            )

        col3, col4 = st.columns(2)
        with col3:
            start_time = st.time_input("⏰ Início", value=None, key="sched_start")
        with col4:
            end_time = st.time_input("⏰ Fim", value=None, key="sched_end")

        title = st.text_input("📝 Descrição (opcional)", placeholder="Ex: Revisão de provas, Exercícios cap. 3", key="sched_title")

        if st.form_submit_button("✅ Adicionar ao Cronograma", use_container_width=True):
            if start_time is None or end_time is None:
                st.error("❌ Selecione o horário de início e fim!")
            elif start_time >= end_time:
                st.error("❌ O horário de início deve ser antes do fim!")
            else:
                db.add_schedule_event(
                    subject_id=subject["id"],
                    day_of_week=day,
                    start_time=start_time.strftime("%H:%M"),
                    end_time=end_time.strftime("%H:%M"),
                    title=title,
                    color=subject["color"],
                )
                st.success(f"✅ Bloco adicionado: **{subject['name']}** — {WEEKDAYS[day]} {start_time.strftime('%H:%M')} às {end_time.strftime('%H:%M')}")
                st.rerun()


def _render_calendar(subjects):
    """Renderiza a grade visual do cronograma semanal."""
    events = db.get_schedule_events()

    if not events:
        st.info("📝 Nenhum bloco no cronograma ainda. Vá na aba **➕ Adicionar Bloco de Estudo** para criar!")
        return

    # Agrupar por total de horas
    total_hours = sum(
        (int(e["end_time"].split(":")[0]) * 60 + int(e["end_time"].split(":")[1])
         - int(e["start_time"].split(":")[0]) * 60 - int(e["start_time"].split(":")[1])) / 60
        for e in events
    )
    st.markdown(f"**📊 Total programado: {total_hours:.1f}h/semana** — {len(events)} blocos")

    # Preparar dados para o calendário JS
    events_json = json.dumps([
        {
            "id": e["id"],
            "day": e["day_of_week"],
            "start": e["start_time"],
            "end": e["end_time"],
            "subject": e["subject_name"],
            "title": e.get("title", ""),
            "color": e.get("subject_color", "#6C63FF"),
        }
        for e in events
    ])

    calendar_html = _build_calendar_html(events_json)
    components.html(calendar_html, height=680, scrolling=True)

    # ─── Gerenciar blocos ────
    st.markdown("---")
    st.markdown("### 🗂️ Gerenciar Blocos")

    for day_idx in range(7):
        day_events = [e for e in events if e["day_of_week"] == day_idx]
        if day_events:
            with st.expander(f"**{WEEKDAYS[day_idx]}** ({len(day_events)} blocos)"):
                for e in day_events:
                    col_info, col_del = st.columns([8, 2])
                    with col_info:
                        label = e.get("title", "")
                        st.markdown(
                            f"<span style='color:{e['subject_color']};font-weight:700'>{e['subject_name']}</span>"
                            f" — {e['start_time']} às {e['end_time']}"
                            f"{f' | {label}' if label else ''}",
                            unsafe_allow_html=True,
                        )
                    with col_del:
                        if st.button("🗑️", key=f"del_sched_{e['id']}"):
                            db.delete_schedule_event(e["id"])
                            st.rerun()


def _build_calendar_html(events_json: str) -> str:
    """Gera o HTML/CSS/JS do calendário semanal."""
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        .cal-container {{
            font-family: 'Inter', sans-serif;
            background: #0E0E1A;
            border: 1px solid rgba(108, 99, 255, 0.15);
            border-radius: 14px;
            overflow: hidden;
        }}

        .cal-grid {{
            display: grid;
            grid-template-columns: 60px repeat(7, 1fr);
            min-height: 600px;
        }}

        .cal-header {{
            background: linear-gradient(145deg, #1a1a3e, #12122a);
            color: #A0A0B8;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            text-align: center;
            padding: 12px 4px;
            border-bottom: 1px solid rgba(108, 99, 255, 0.2);
        }}

        .cal-header.today {{
            background: linear-gradient(145deg, #6C63FF33, #9D4EDD33);
            color: #E040FB;
        }}

        .cal-time-col {{
            background: rgba(108, 99, 255, 0.05);
            border-right: 1px solid rgba(108, 99, 255, 0.1);
        }}

        .cal-time-label {{
            height: 50px;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding-top: 2px;
            color: #606080;
            font-size: 0.65rem;
            font-weight: 600;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }}

        .cal-day-col {{
            position: relative;
            border-right: 1px solid rgba(255,255,255,0.03);
        }}

        .cal-hour-line {{
            height: 50px;
            border-bottom: 1px solid rgba(255,255,255,0.03);
        }}

        .cal-event {{
            position: absolute;
            left: 3px;
            right: 3px;
            border-radius: 6px;
            padding: 4px 6px;
            font-size: 0.7rem;
            font-weight: 600;
            overflow: hidden;
            cursor: default;
            border-left: 3px solid;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            z-index: 2;
        }}

        .cal-event:hover {{
            transform: scale(1.03);
            box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            z-index: 5;
        }}

        .cal-event-subject {{
            font-weight: 700;
            font-size: 0.7rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .cal-event-time {{
            font-size: 0.6rem;
            opacity: 0.8;
            margin-top: 1px;
        }}

        .cal-event-title {{
            font-size: 0.6rem;
            opacity: 0.7;
            margin-top: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
    </style>

    <div class="cal-container">
        <div class="cal-grid" id="calGrid">
            <!-- Built by JS -->
        </div>
    </div>

    <script>
        const events = {events_json};
        const days = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];
        const START_HOUR = 6;
        const END_HOUR = 24;
        const HOUR_HEIGHT = 50;
        const today = new Date().getDay();
        // JS: 0=Sun, convert to Mon=0 format
        const todayIdx = today === 0 ? 6 : today - 1;

        const grid = document.getElementById('calGrid');

        // Header row
        const cornerEl = document.createElement('div');
        cornerEl.className = 'cal-header';
        cornerEl.textContent = '⏰';
        grid.appendChild(cornerEl);

        for (let d = 0; d < 7; d++) {{
            const hdr = document.createElement('div');
            hdr.className = 'cal-header' + (d === todayIdx ? ' today' : '');
            hdr.textContent = days[d];
            grid.appendChild(hdr);
        }}

        // Time column
        const timeCol = document.createElement('div');
        timeCol.className = 'cal-time-col';
        for (let h = START_HOUR; h < END_HOUR; h++) {{
            const lbl = document.createElement('div');
            lbl.className = 'cal-time-label';
            lbl.textContent = String(h).padStart(2, '0') + ':00';
            timeCol.appendChild(lbl);
        }}
        grid.appendChild(timeCol);

        // Day columns
        for (let d = 0; d < 7; d++) {{
            const col = document.createElement('div');
            col.className = 'cal-day-col';

            // Hour lines
            for (let h = START_HOUR; h < END_HOUR; h++) {{
                const line = document.createElement('div');
                line.className = 'cal-hour-line';
                col.appendChild(line);
            }}

            // Events for this day
            const dayEvents = events.filter(e => e.day === d);
            dayEvents.forEach(ev => {{
                const [sh, sm] = ev.start.split(':').map(Number);
                const [eh, em] = ev.end.split(':').map(Number);

                const startMin = (sh - START_HOUR) * 60 + sm;
                const endMin = (eh - START_HOUR) * 60 + em;
                const top = (startMin / 60) * HOUR_HEIGHT;
                const height = Math.max(((endMin - startMin) / 60) * HOUR_HEIGHT, 20);

                const evEl = document.createElement('div');
                evEl.className = 'cal-event';
                evEl.style.top = top + 'px';
                evEl.style.height = height + 'px';
                evEl.style.backgroundColor = ev.color + '25';
                evEl.style.borderLeftColor = ev.color;
                evEl.style.color = '#E0E0F0';

                let html = '<div class="cal-event-subject">' + ev.subject + '</div>';
                html += '<div class="cal-event-time">' + ev.start + ' - ' + ev.end + '</div>';
                if (ev.title) {{
                    html += '<div class="cal-event-title">' + ev.title + '</div>';
                }}
                evEl.innerHTML = html;

                col.appendChild(evEl);
            }});

            grid.appendChild(col);
        }}
    </script>
    """
