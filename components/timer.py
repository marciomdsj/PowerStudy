"""
PowerStudy - Componente de Timer (Pomodoro + Cronômetro)
Estado persistido em session_state para sobreviver re-renders do Streamlit.
"""
import streamlit as st
import streamlit.components.v1 as components
import time as pytime


def render_timer():
    """Renderiza o timer e retorna os minutos estudados."""

    # ─── Inicializar estado ────
    if "timer_state" not in st.session_state:
        st.session_state["timer_state"] = {
            "running": False,
            "start_epoch_ms": 0,
            "paused_accumulated_ms": 0,
            "mode": "countdown",  # countdown ou stopwatch
            "total_seconds": 1500,  # 25 min default
            "finished": False,
            "final_minutes": 0,
        }

    ts = st.session_state["timer_state"]

    st.markdown("### ⏱️ Timer de Estudo")

    # ─── Modo do timer ────
    if not ts["running"] and not ts["finished"]:
        mode = st.radio(
            "Modo",
            ["🍅 Pomodoro", "⏱️ Cronômetro Livre"],
            horizontal=True,
            key="timer_mode_radio",
        )
        ts["mode"] = "countdown" if mode == "🍅 Pomodoro" else "stopwatch"

        if ts["mode"] == "countdown":
            preset = st.radio(
                "Tempo de estudo:",
                ["25 min", "50 min", "90 min", "Personalizado"],
                horizontal=True,
                key="pomodoro_preset",
            )
            if preset == "Personalizado":
                ts["total_seconds"] = st.number_input(
                    "Minutos:", min_value=1, max_value=300, value=45, key="custom_timer_mins"
                ) * 60
            else:
                ts["total_seconds"] = int(preset.split()[0]) * 60

    # ─── Calcular tempo atual ────
    if ts["running"]:
        now_ms = int(pytime.time() * 1000)
        elapsed_ms = ts["paused_accumulated_ms"] + (now_ms - ts["start_epoch_ms"])
    elif ts["paused_accumulated_ms"] > 0:
        elapsed_ms = ts["paused_accumulated_ms"]
    else:
        elapsed_ms = 0

    elapsed_seconds = elapsed_ms // 1000

    # ─── Checar se countdown acabou ────
    if ts["mode"] == "countdown" and ts["running"] and elapsed_seconds >= ts["total_seconds"]:
        ts["running"] = False
        ts["finished"] = True
        ts["final_minutes"] = ts["total_seconds"] // 60
        elapsed_seconds = ts["total_seconds"]

    # ─── Renderizar display JS ────
    _render_display(ts, elapsed_seconds)

    # ─── Botões de controle (Streamlit, não JS) ────
    if ts["finished"]:
        st.success(f"✅ Timer finalizado! Você estudou **{ts['final_minutes']} minutos**.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Novo Timer", use_container_width=True, key="timer_reset"):
                _reset_timer()
                st.rerun()
        st.markdown("---")
        return ts["final_minutes"]

    elif ts["running"]:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏸ Pausar", use_container_width=True, key="timer_pause"):
                now_ms = int(pytime.time() * 1000)
                ts["paused_accumulated_ms"] += now_ms - ts["start_epoch_ms"]
                ts["running"] = False
                st.rerun()
        with col2:
            if st.button("⏹ Parar e Salvar", use_container_width=True, key="timer_stop"):
                now_ms = int(pytime.time() * 1000)
                total_ms = ts["paused_accumulated_ms"] + (now_ms - ts["start_epoch_ms"])
                total_min = max(1, round(total_ms / 60000))
                ts["running"] = False
                ts["finished"] = True
                ts["final_minutes"] = total_min
                st.rerun()

    elif ts["paused_accumulated_ms"] > 0:
        # Pausado
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("▶ Continuar", use_container_width=True, key="timer_resume"):
                ts["start_epoch_ms"] = int(pytime.time() * 1000)
                ts["running"] = True
                st.rerun()
        with col2:
            if st.button("⏹ Parar e Salvar", use_container_width=True, key="timer_stop_paused"):
                total_min = max(1, round(ts["paused_accumulated_ms"] / 60000))
                ts["finished"] = True
                ts["final_minutes"] = total_min
                st.rerun()
        with col3:
            if st.button("🔄 Resetar", use_container_width=True, key="timer_reset_paused"):
                _reset_timer()
                st.rerun()
    else:
        if st.button("▶ Iniciar", use_container_width=True, key="timer_start"):
            ts["start_epoch_ms"] = int(pytime.time() * 1000)
            ts["running"] = True
            st.rerun()

    st.markdown("---")

    # Se parado mas não finalizado, permitir preencher minutos manualmente
    if not ts["finished"]:
        recorded = st.number_input(
            "⏱️ Ou preencha os minutos manualmente:",
            min_value=0, max_value=1440, value=0,
            step=1, key="manual_minutes_timer",
        )
        return recorded

    return ts.get("final_minutes", 0)


def _reset_timer():
    st.session_state["timer_state"] = {
        "running": False,
        "start_epoch_ms": 0,
        "paused_accumulated_ms": 0,
        "mode": "countdown",
        "total_seconds": 1500,
        "finished": False,
        "final_minutes": 0,
    }


def _render_display(ts: dict, elapsed_seconds: int):
    """Renderiza o display visual do timer com JS auto-refresh."""
    if ts["mode"] == "countdown":
        display_seconds = max(0, ts["total_seconds"] - elapsed_seconds)
        label = "🍅 POMODORO"
    else:
        display_seconds = elapsed_seconds
        label = "⏱️ CRONÔMETRO LIVRE"

    is_running = ts["running"]

    # Para auto-refresh do display enquanto rodando
    start_epoch_ms = ts["start_epoch_ms"] if is_running else 0
    paused_ms = ts["paused_accumulated_ms"]
    total_seconds = ts["total_seconds"]
    mode = ts["mode"]

    html = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;700&display=swap');
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        .timer-container {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(145deg, #1a1a3e, #12122a);
            border: 1px solid rgba(108, 99, 255, 0.2);
            border-radius: 16px;
            padding: 28px;
            text-align: center;
        }}
        .timer-display {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 4rem;
            font-weight: 700;
            background: linear-gradient(135deg, #6C63FF, #9D4EDD, #E040FB);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 10px 0;
            letter-spacing: 2px;
        }}
        .timer-label {{
            color: #A0A0B8;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        .timer-info {{
            color: #A0A0B8;
            font-size: 0.8rem;
            margin-top: 12px;
        }}
        .running {{ animation: pulse 2s ease-in-out infinite; }}
        @keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.75; }} }}
        .hourly-badge {{
            display: inline-block;
            background: rgba(224, 64, 251, 0.15);
            color: #E040FB;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-top: 8px;
        }}
    </style>
    <div class="timer-container">
        <div class="timer-label">{label}{' — PAUSADO' if not is_running and paused_ms > 0 else ''}</div>
        <div class="timer-display {'running' if is_running else ''}" id="display">
            {_format_time(display_seconds)}
        </div>
        <div id="hourlyInfo"></div>
        <div class="timer-info" id="info">
            {'Estudando...' if is_running else
             'Tempo definido: ' + str(total_seconds // 60) + ' minutos' if mode == 'countdown' and paused_ms == 0 and not ts['finished']
             else 'Clique Iniciar — 🔔 toca a cada hora' if mode == 'stopwatch' and paused_ms == 0 and not ts['finished']
             else ''}
        </div>
    </div>
    <script>
        const IS_RUNNING = {'true' if is_running else 'false'};
        const START_EPOCH_MS = {start_epoch_ms};
        const PAUSED_MS = {paused_ms};
        const TOTAL_SECS = {total_seconds};
        const MODE = '{mode}';
        let lastHourNotified = 0;

        function fmt(s) {{
            const h = Math.floor(s/3600), m = Math.floor((s%3600)/60), sec = s%60;
            return String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(sec).padStart(2,'0');
        }}

        function playBell() {{
            try {{
                const ctx = new (window.AudioContext||window.webkitAudioContext)();
                [830,1046,1318].forEach((f,i) => {{
                    const o=ctx.createOscillator(), g=ctx.createGain();
                    o.connect(g); g.connect(ctx.destination);
                    o.type='sine'; o.frequency.value=f;
                    g.gain.setValueAtTime(0.3,ctx.currentTime+i*0.15);
                    g.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+i*0.15+0.3);
                    o.start(ctx.currentTime+i*0.15);
                    o.stop(ctx.currentTime+i*0.15+0.35);
                }});
            }} catch(e) {{}}
        }}

        if (IS_RUNNING) {{
            setInterval(() => {{
                const now = Date.now();
                const totalElapsed = Math.floor((PAUSED_MS + (now - START_EPOCH_MS)) / 1000);
                const disp = document.getElementById('display');
                if (MODE === 'countdown') {{
                    const rem = Math.max(0, TOTAL_SECS - totalElapsed);
                    disp.textContent = fmt(rem);
                    if (rem <= 0) {{ playBell(); }}
                }} else {{
                    disp.textContent = fmt(totalElapsed);
                    const hr = Math.floor(totalElapsed / 3600);
                    if (hr > lastHourNotified) {{
                        lastHourNotified = hr;
                        playBell();
                        document.getElementById('hourlyInfo').innerHTML =
                            '<span class="hourly-badge">🔔 '+hr+'h de estudo!</span>';
                    }}
                }}
            }}, 500);
        }}
    </script>
    """
    components.html(html, height=200)


def _format_time(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"
