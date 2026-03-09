"""
PowerStudy - Camada de acesso ao banco de dados SQLite
Cada usuário tem seu próprio banco: data/{username}.db
"""
import sqlite3
import os
from datetime import datetime, timedelta
from database.models import SCHEMA

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Usuário atual (definido pelo app.py via set_current_user)
_current_user = "default"


def set_current_user(username: str):
    """Define o usuário atual. Cada usuário tem seu próprio banco."""
    global _current_user
    _current_user = username.strip().lower().replace(" ", "_")


def get_current_user() -> str:
    return _current_user


def _get_db_path() -> str:
    return os.path.join(DATA_DIR, f"{_current_user}.db")


def get_connection():
    """Retorna uma conexão com o banco SQLite do usuário atual."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Inicializa o banco de dados criando as tabelas."""
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


# ──────────────────────── SUBJECTS ────────────────────────

def add_subject(name: str, semester: int, color: str = "#6C63FF"):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO subjects (name, semester, color) VALUES (?, ?, ?)",
            (name, semester, color),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_subjects():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM subjects ORDER BY semester, name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_subject_by_id(subject_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_subject(subject_id: int, name: str, semester: int, color: str):
    conn = get_connection()
    conn.execute(
        "UPDATE subjects SET name=?, semester=?, color=? WHERE id=?",
        (name, semester, color, subject_id),
    )
    conn.commit()
    conn.close()


def delete_subject(subject_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
    conn.commit()
    conn.close()


# ──────────────────────── STUDY SESSIONS ────────────────────────

def add_session(subject_id: int, date: str, duration_minutes: int, topic: str = "", notes: str = ""):
    conn = get_connection()
    conn.execute(
        "INSERT INTO study_sessions (subject_id, date, duration_minutes, topic, notes) VALUES (?, ?, ?, ?, ?)",
        (subject_id, date, duration_minutes, topic, notes),
    )
    conn.commit()
    conn.close()


def get_sessions(subject_id: int = None, semester: int = None, limit: int = None):
    conn = get_connection()
    query = """
        SELECT ss.*, s.name as subject_name, s.color as subject_color, s.semester
        FROM study_sessions ss
        JOIN subjects s ON ss.subject_id = s.id
        WHERE 1=1
    """
    params = []
    if subject_id:
        query += " AND ss.subject_id = ?"
        params.append(subject_id)
    if semester:
        query += " AND s.semester = ?"
        params.append(semester)
    query += " ORDER BY ss.date DESC, ss.created_at DESC"
    if limit:
        query += " LIMIT ?"
        params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_session(session_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM study_sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()


def get_total_hours(subject_id: int = None, semester: int = None):
    conn = get_connection()
    query = """
        SELECT COALESCE(SUM(ss.duration_minutes), 0) / 60.0 as total_hours
        FROM study_sessions ss
        JOIN subjects s ON ss.subject_id = s.id
        WHERE 1=1
    """
    params = []
    if subject_id:
        query += " AND ss.subject_id = ?"
        params.append(subject_id)
    if semester:
        query += " AND s.semester = ?"
        params.append(semester)
    row = conn.execute(query, params).fetchone()
    conn.close()
    return row["total_hours"] if row else 0.0


def get_hours_by_subject(semester: int = None):
    conn = get_connection()
    query = """
        SELECT s.id, s.name, s.color, s.semester,
               COALESCE(SUM(ss.duration_minutes), 0) / 60.0 as total_hours,
               COUNT(ss.id) as session_count
        FROM subjects s
        LEFT JOIN study_sessions ss ON s.id = ss.subject_id
        WHERE 1=1
    """
    params = []
    if semester:
        query += " AND s.semester = ?"
        params.append(semester)
    query += " GROUP BY s.id ORDER BY total_hours DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_study_dates():
    """Retorna todas as datas com sessões de estudo e total de minutos."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT date, SUM(duration_minutes) as total_minutes
        FROM study_sessions
        GROUP BY date
        ORDER BY date
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_streak():
    """Calcula o streak atual (dias consecutivos de estudo)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT DISTINCT date FROM study_sessions ORDER BY date DESC
    """).fetchall()
    conn.close()

    if not rows:
        return 0

    dates = [datetime.strptime(r["date"], "%Y-%m-%d").date() for r in rows]
    today = datetime.now().date()

    # Streak conta a partir de hoje ou ontem
    if dates[0] != today and dates[0] != today - timedelta(days=1):
        return 0

    streak = 1
    for i in range(1, len(dates)):
        if dates[i - 1] - dates[i] == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


def get_unique_subjects_studied_this_week():
    """Conta quantas matérias diferentes foram estudadas esta semana."""
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    conn = get_connection()
    row = conn.execute("""
        SELECT COUNT(DISTINCT subject_id) as count
        FROM study_sessions
        WHERE date >= ?
    """, (start_of_week.isoformat(),)).fetchone()
    conn.close()
    return row["count"] if row else 0


def get_hours_by_weekday():
    conn = get_connection()
    rows = conn.execute("""
        SELECT date, SUM(duration_minutes)/60.0 as hours
        FROM study_sessions GROUP BY date
    """).fetchall()
    conn.close()
    weekday_hours = {i: 0.0 for i in range(7)}
    for r in rows:
        dt = datetime.strptime(r["date"], "%Y-%m-%d")
        weekday_hours[dt.weekday()] += r["hours"]
    return weekday_hours


# ──────────────────────── SYLLABUS ────────────────────────

def get_syllabi(subject_id: int):
    """Retorna todos os planos de aula de uma matéria."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM syllabi WHERE subject_id = ? ORDER BY created_at",
        (subject_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_syllabus(subject_id: int, name: str) -> int:
    """Cria um novo plano de aula. Retorna o id."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO syllabi (subject_id, name) VALUES (?, ?)",
        (subject_id, name),
    )
    conn.commit()
    syllabus_id = cursor.lastrowid
    conn.close()
    return syllabus_id


def delete_syllabus(syllabus_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM syllabus_topics WHERE syllabus_id = ?", (syllabus_id,))
    conn.execute("DELETE FROM syllabi WHERE id = ?", (syllabus_id,))
    conn.commit()
    conn.close()


def add_syllabus_topics(syllabus_id: int, subject_id: int, topics: list):
    """Substitui TODOS os tópicos de um plano (usado ao definir manualmente a lista completa)."""
    conn = get_connection()
    conn.execute("DELETE FROM syllabus_topics WHERE syllabus_id = ?", (syllabus_id,))
    for i, topic in enumerate(topics):
        conn.execute(
            "INSERT INTO syllabus_topics (syllabus_id, subject_id, topic_name, order_index) VALUES (?, ?, ?, ?)",
            (syllabus_id, subject_id, topic, i),
        )
    conn.commit()
    conn.close()


def append_syllabus_topics(syllabus_id: int, subject_id: int, topics: list):
    """Adiciona tópicos ao final dos existentes (não apaga nada)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(MAX(order_index), -1) as max_idx FROM syllabus_topics WHERE syllabus_id = ?",
        (syllabus_id,),
    ).fetchone()
    start_idx = row["max_idx"] + 1
    for i, topic in enumerate(topics):
        conn.execute(
            "INSERT INTO syllabus_topics (syllabus_id, subject_id, topic_name, order_index) VALUES (?, ?, ?, ?)",
            (syllabus_id, subject_id, topic, start_idx + i),
        )
    conn.commit()
    conn.close()


def get_syllabus_topics(subject_id: int = None, syllabus_id: int = None):
    conn = get_connection()
    if syllabus_id:
        rows = conn.execute(
            "SELECT * FROM syllabus_topics WHERE syllabus_id = ? ORDER BY order_index",
            (syllabus_id,),
        ).fetchall()
    elif subject_id:
        rows = conn.execute(
            "SELECT * FROM syllabus_topics WHERE subject_id = ? ORDER BY syllabus_id, order_index",
            (subject_id,),
        ).fetchall()
    else:
        rows = []
    conn.close()
    return [dict(r) for r in rows]


def toggle_topic_studied(topic_id: int):
    conn = get_connection()
    conn.execute(
        "UPDATE syllabus_topics SET is_studied = NOT is_studied WHERE id = ?",
        (topic_id,),
    )
    conn.commit()
    conn.close()


def get_syllabus_progress(subject_id: int = None, syllabus_id: int = None):
    conn = get_connection()
    if syllabus_id:
        row = conn.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN is_studied = 1 THEN 1 ELSE 0 END) as studied
            FROM syllabus_topics WHERE syllabus_id = ?
        """, (syllabus_id,)).fetchone()
    elif subject_id:
        row = conn.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN is_studied = 1 THEN 1 ELSE 0 END) as studied
            FROM syllabus_topics WHERE subject_id = ?
        """, (subject_id,)).fetchone()
    else:
        conn.close()
        return {"total": 0, "studied": 0, "percentage": 0.0}
    conn.close()
    if row and row["total"] > 0:
        return {"total": row["total"], "studied": row["studied"],
                "percentage": round(row["studied"] / row["total"] * 100, 1)}
    return {"total": 0, "studied": 0, "percentage": 0.0}


# ──────────────────────── GOALS ────────────────────────

def set_goal(subject_id: int, weekly_hours: float, semester: int):
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM goals WHERE subject_id = ? AND semester = ?",
        (subject_id, semester),
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE goals SET weekly_hours_target = ? WHERE id = ?",
            (weekly_hours, existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO goals (subject_id, weekly_hours_target, semester) VALUES (?, ?, ?)",
            (subject_id, weekly_hours, semester),
        )
    conn.commit()
    conn.close()


def get_goals(semester: int = None):
    conn = get_connection()
    query = """
        SELECT g.*, s.name as subject_name, s.color as subject_color
        FROM goals g
        JOIN subjects s ON g.subject_id = s.id
        WHERE 1=1
    """
    params = []
    if semester:
        query += " AND g.semester = ?"
        params.append(semester)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_weekly_hours(subject_id: int):
    """Retorna horas estudadas esta semana para uma matéria."""
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    conn = get_connection()
    row = conn.execute("""
        SELECT COALESCE(SUM(duration_minutes), 0) / 60.0 as hours
        FROM study_sessions
        WHERE subject_id = ? AND date >= ?
    """, (subject_id, start_of_week.isoformat())).fetchone()
    conn.close()
    return row["hours"] if row else 0.0


# ──────────────────────── SCHEDULE ────────────────────────

WEEKDAYS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def add_schedule_event(subject_id: int, day_of_week: int, start_time: str,
                       end_time: str, title: str = "", notes: str = "", color: str = ""):
    conn = get_connection()
    conn.execute(
        """INSERT INTO schedule_events (subject_id, day_of_week, start_time, end_time, title, notes, color)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (subject_id, day_of_week, start_time, end_time, title, notes, color),
    )
    conn.commit()
    conn.close()


def get_schedule_events(day_of_week: int = None):
    conn = get_connection()
    if day_of_week is not None:
        rows = conn.execute("""
            SELECT se.*, s.name as subject_name, s.color as subject_color, s.semester
            FROM schedule_events se
            JOIN subjects s ON se.subject_id = s.id
            WHERE se.day_of_week = ?
            ORDER BY se.start_time
        """, (day_of_week,)).fetchall()
    else:
        rows = conn.execute("""
            SELECT se.*, s.name as subject_name, s.color as subject_color, s.semester
            FROM schedule_events se
            JOIN subjects s ON se.subject_id = s.id
            ORDER BY se.day_of_week, se.start_time
        """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_schedule_event(event_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM schedule_events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

