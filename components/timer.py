"""
PowerStudy - Componente de Timer (Pomodoro + Cronômetro)
Usa JavaScript injetado via st.components.html para timer client-side.
"""
import streamlit as st
import streamlit.components.v1 as components


def render_timer():
    """Renderiza o timer e retorna os minutos estudados quando o timer para."""

    # Inicializar estado
    if "timer_minutes" not in st.session_state:
        st.session_state["timer_minutes"] = 0

    st.markdown("### ⏱️ Timer de Estudo")

    # Modo do timer
    mode = st.radio(
        "Modo",
        ["🍅 Pomodoro", "⏱️ Cronômetro Livre"],
        horizontal=True,
        key="timer_mode",
    )

    if mode == "🍅 Pomodoro":
        preset = st.radio(
            "Tempo de estudo:",
            ["25 min", "50 min", "90 min", "Personalizado"],
            horizontal=True,
            key="pomodoro_preset",
        )
        if preset == "Personalizado":
            timer_seconds = st.number_input("Minutos:", min_value=1, max_value=300, value=45, key="custom_mins") * 60
        else:
            timer_seconds = int(preset.split()[0]) * 60
        timer_type = "countdown"
    else:
        timer_seconds = 0
        timer_type = "stopwatch"

    # Renderizar o timer HTML/JS
    timer_html = _build_timer_html(timer_type, timer_seconds)
    components.html(timer_html, height=320)

    # Campo para receber minutos do timer
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        recorded = st.number_input(
            "⏱️ Minutos estudados (preencha ou use o timer acima):",
            min_value=0, max_value=1440, value=st.session_state.get("timer_minutes", 0),
            step=1, key="recorded_minutes",
            help="Quando o timer parar, copie o tempo total aqui",
        )
    with col2:
        st.markdown("")
        st.markdown("")
        if st.button("🔄 Resetar", key="reset_timer"):
            st.session_state["timer_minutes"] = 0
            st.rerun()

    return recorded


def _build_timer_html(timer_type: str, total_seconds: int) -> str:
    """Gera o HTML/CSS/JS do timer."""
    return f"""
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
            box-shadow: 0 0 30px rgba(108, 99, 255, 0.1);
        }}

        .timer-display {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 4rem;
            font-weight: 700;
            background: linear-gradient(135deg, #6C63FF, #9D4EDD, #E040FB);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 16px 0;
            letter-spacing: 2px;
            transition: all 0.3s ease;
        }}

        .timer-display.running {{
            animation: pulse 2s ease-in-out infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
        }}

        .timer-label {{
            color: #A0A0B8;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 8px;
        }}

        .timer-buttons {{
            display: flex;
            gap: 12px;
            justify-content: center;
            margin-top: 20px;
        }}

        .timer-btn {{
            font-family: 'Inter', sans-serif;
            padding: 12px 32px;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            letter-spacing: 0.5px;
        }}

        .btn-start {{
            background: linear-gradient(135deg, #6C63FF, #9D4EDD);
            color: white;
            box-shadow: 0 4px 15px rgba(108, 99, 255, 0.4);
        }}
        .btn-start:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(108, 99, 255, 0.5);
        }}

        .btn-pause {{
            background: linear-gradient(135deg, #FF9800, #FF5722);
            color: white;
            box-shadow: 0 4px 15px rgba(255, 152, 0, 0.3);
        }}

        .btn-stop {{
            background: linear-gradient(135deg, #F44336, #D32F2F);
            color: white;
            box-shadow: 0 4px 15px rgba(244, 67, 54, 0.3);
        }}

        .btn-reset {{
            background: rgba(255,255,255,0.1);
            color: #A0A0B8;
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .timer-info {{
            color: #A0A0B8;
            font-size: 0.8rem;
            margin-top: 14px;
        }}

        .timer-total {{
            color: #E040FB;
            font-weight: 700;
            font-size: 1.1rem;
        }}

        .hourly-badge {{
            display: inline-block;
            background: rgba(224, 64, 251, 0.15);
            color: #E040FB;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-top: 8px;
        }}
    </style>

    <div class="timer-container">
        <div class="timer-label" id="timerLabel">
            {'🍅 Pomodoro' if timer_type == 'countdown' else '⏱️ Cronômetro Livre'}
        </div>
        <div class="timer-display" id="timerDisplay">00:00:00</div>
        <div id="hourlyInfo"></div>
        <div class="timer-buttons">
            <button class="timer-btn btn-start" id="btnStart" onclick="startTimer()">▶ Iniciar</button>
            <button class="timer-btn btn-pause" id="btnPause" onclick="pauseTimer()" style="display:none">⏸ Pausar</button>
            <button class="timer-btn btn-stop" id="btnStop" onclick="stopTimer()" style="display:none">⏹ Parar</button>
            <button class="timer-btn btn-reset" id="btnReset" onclick="resetTimer()" style="display:none">🔄 Reset</button>
        </div>
        <div class="timer-info" id="timerInfo">
            {'Tempo definido: ' + str(total_seconds // 60) + ' minutos' if timer_type == 'countdown' else 'Clique em Iniciar para começar — 🔔 toca a cada hora'}
        </div>
        <div class="timer-info" id="totalStudied" style="display:none">
            Total estudado: <span class="timer-total" id="totalMinutes">0</span> minutos
        </div>
    </div>

    <script>
        const TIMER_TYPE = '{timer_type}';
        const TOTAL_SECONDS = {total_seconds};

        let interval = null;
        let elapsed = 0;       // seconds elapsed
        let remaining = TOTAL_SECONDS;
        let isRunning = false;
        let isPaused = false;
        let lastHourNotified = 0;

        // Audio context for bell sound
        function playBell() {{
            try {{
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                // Bell note 1
                playNote(ctx, 830, 0, 0.3);
                // Bell note 2
                playNote(ctx, 1046, 0.15, 0.3);
                // Bell note 3
                playNote(ctx, 1318, 0.3, 0.4);
            }} catch(e) {{
                console.log('Audio not available');
            }}
        }}

        function playNote(ctx, freq, startTime, duration) {{
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.type = 'sine';
            osc.frequency.value = freq;
            gain.gain.setValueAtTime(0.3, ctx.currentTime + startTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + startTime + duration);
            osc.start(ctx.currentTime + startTime);
            osc.stop(ctx.currentTime + startTime + duration);
        }}

        function formatTime(seconds) {{
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = seconds % 60;
            return String(h).padStart(2,'0') + ':' + String(m).padStart(2,'0') + ':' + String(s).padStart(2,'0');
        }}

        function updateDisplay() {{
            const display = document.getElementById('timerDisplay');
            if (TIMER_TYPE === 'countdown') {{
                display.textContent = formatTime(remaining);
            }} else {{
                display.textContent = formatTime(elapsed);
            }}
        }}

        function tick() {{
            elapsed++;
            if (TIMER_TYPE === 'countdown') {{
                remaining--;
                if (remaining <= 0) {{
                    remaining = 0;
                    stopTimer();
                    playBell();
                    document.getElementById('timerLabel').textContent = '🍅 Tempo esgotado!';
                    return;
                }}
            }} else {{
                // Stopwatch: bell every hour
                const currentHour = Math.floor(elapsed / 3600);
                if (currentHour > lastHourNotified) {{
                    lastHourNotified = currentHour;
                    playBell();
                    const info = document.getElementById('hourlyInfo');
                    info.innerHTML = '<span class="hourly-badge">🔔 ' + currentHour + 'h de estudo!</span>';
                }}
            }}
            updateDisplay();
        }}

        function startTimer() {{
            if (isRunning && !isPaused) return;

            if (isPaused) {{
                // Resume
                isPaused = false;
            }}
            isRunning = true;
            interval = setInterval(tick, 1000);

            document.getElementById('btnStart').style.display = 'none';
            document.getElementById('btnPause').style.display = 'inline-block';
            document.getElementById('btnStop').style.display = 'inline-block';
            document.getElementById('btnReset').style.display = 'none';
            document.getElementById('timerDisplay').classList.add('running');
            document.getElementById('timerLabel').textContent =
                TIMER_TYPE === 'countdown' ? '🍅 Estudando...' : '⏱️ Estudando...';
        }}

        function pauseTimer() {{
            if (!isRunning) return;
            clearInterval(interval);
            isPaused = true;

            document.getElementById('btnStart').style.display = 'inline-block';
            document.getElementById('btnStart').textContent = '▶ Continuar';
            document.getElementById('btnPause').style.display = 'none';
            document.getElementById('btnStop').style.display = 'inline-block';
            document.getElementById('btnReset').style.display = 'inline-block';
            document.getElementById('timerDisplay').classList.remove('running');
            document.getElementById('timerLabel').textContent = '⏸ Pausado';
        }}

        function stopTimer() {{
            clearInterval(interval);
            isRunning = false;
            isPaused = false;

            const totalMin = Math.ceil(elapsed / 60);

            document.getElementById('btnStart').style.display = 'inline-block';
            document.getElementById('btnStart').textContent = '▶ Iniciar';
            document.getElementById('btnPause').style.display = 'none';
            document.getElementById('btnStop').style.display = 'none';
            document.getElementById('btnReset').style.display = 'inline-block';
            document.getElementById('timerDisplay').classList.remove('running');

            document.getElementById('totalStudied').style.display = 'block';
            document.getElementById('totalMinutes').textContent = totalMin;
            document.getElementById('timerInfo').textContent = '✅ Preencha ' + totalMin + ' minutos no campo abaixo e registre a sessão!';

            playBell();
        }}

        function resetTimer() {{
            clearInterval(interval);
            elapsed = 0;
            remaining = TOTAL_SECONDS;
            isRunning = false;
            isPaused = false;
            lastHourNotified = 0;

            updateDisplay();

            document.getElementById('btnStart').style.display = 'inline-block';
            document.getElementById('btnStart').textContent = '▶ Iniciar';
            document.getElementById('btnPause').style.display = 'none';
            document.getElementById('btnStop').style.display = 'none';
            document.getElementById('btnReset').style.display = 'none';
            document.getElementById('totalStudied').style.display = 'none';
            document.getElementById('hourlyInfo').innerHTML = '';
            document.getElementById('timerDisplay').classList.remove('running');
            document.getElementById('timerLabel').textContent =
                TIMER_TYPE === 'countdown' ? '🍅 Pomodoro' : '⏱️ Cronômetro Livre';
            document.getElementById('timerInfo').textContent =
                TIMER_TYPE === 'countdown'
                ? 'Tempo definido: ' + Math.floor(TOTAL_SECONDS/60) + ' minutos'
                : 'Clique em Iniciar para começar — 🔔 toca a cada hora';
        }}

        // Initialize display
        updateDisplay();
    </script>
    """
