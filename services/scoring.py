"""
PowerStudy - Sistema de Pontuação e Gamificação
"""
from database import db
from datetime import datetime

# ──────────── Configuração de Pontuação ────────────
POINTS_PER_HOUR = 10
STREAK_BONUS_3 = 1.5   # 3+ dias consecutivos
STREAK_BONUS_7 = 2.0   # 7+ dias consecutivos
VARIETY_BONUS = 1.2     # 3+ matérias diferentes na semana

# ──────────── Níveis ────────────
LEVELS = [
    {"name": "Calouro", "emoji": "🌱", "min_points": 0},
    {"name": "Estudante", "emoji": "📖", "min_points": 50},
    {"name": "Dedicado", "emoji": "⚡", "min_points": 150},
    {"name": "Focado", "emoji": "🎯", "min_points": 350},
    {"name": "Avançado", "emoji": "🔥", "min_points": 600},
    {"name": "Expert", "emoji": "💎", "min_points": 1000},
    {"name": "Mestre", "emoji": "👑", "min_points": 1800},
    {"name": "Lenda", "emoji": "🏆", "min_points": 3000},
]

# ──────────── Badges por matéria ────────────
SUBJECT_BADGES = [
    {"name": "Bronze", "emoji": "🥉", "min_hours": 5},
    {"name": "Prata", "emoji": "🥈", "min_hours": 15},
    {"name": "Ouro", "emoji": "🥇", "min_hours": 30},
    {"name": "Diamante", "emoji": "💎", "min_hours": 60},
]


def calculate_session_points(duration_minutes: int) -> dict:
    """Calcula pontos para uma sessão de estudo."""
    base_points = (duration_minutes / 60.0) * POINTS_PER_HOUR
    streak = db.get_streak()
    variety = db.get_unique_subjects_studied_this_week()

    multiplier = 1.0
    bonuses = []

    if streak >= 7:
        multiplier = STREAK_BONUS_7
        bonuses.append(f"🔥 Streak {streak} dias (x{STREAK_BONUS_7})")
    elif streak >= 3:
        multiplier = STREAK_BONUS_3
        bonuses.append(f"⚡ Streak {streak} dias (x{STREAK_BONUS_3})")

    if variety >= 3:
        multiplier *= VARIETY_BONUS
        bonuses.append(f"📚 Variedade ({variety} matérias) (x{VARIETY_BONUS})")

    total = round(base_points * multiplier, 1)
    return {
        "base_points": round(base_points, 1),
        "multiplier": multiplier,
        "total_points": total,
        "bonuses": bonuses,
    }


def get_total_points() -> float:
    """Calcula o total de pontos acumulados."""
    sessions = db.get_sessions()
    total = 0
    for s in sessions:
        pts = (s["duration_minutes"] / 60.0) * POINTS_PER_HOUR
        total += pts
    # Adiciona bônus de streak simplificado (baseado no streak atual)
    streak = db.get_streak()
    if streak >= 7:
        total *= 1.1  # 10% bônus por streak longo
    elif streak >= 3:
        total *= 1.05
    return round(total, 1)


def get_current_level() -> dict:
    """Retorna o nível atual baseado nos pontos totais."""
    points = get_total_points()
    current = LEVELS[0]
    next_level = LEVELS[1] if len(LEVELS) > 1 else None

    for i, level in enumerate(LEVELS):
        if points >= level["min_points"]:
            current = level
            next_level = LEVELS[i + 1] if i + 1 < len(LEVELS) else None
        else:
            break

    progress = 0
    if next_level:
        range_pts = next_level["min_points"] - current["min_points"]
        earned = points - current["min_points"]
        progress = min(earned / range_pts * 100, 100) if range_pts > 0 else 100

    return {
        "level": current,
        "next_level": next_level,
        "points": points,
        "progress": round(progress, 1),
    }


def get_subject_badge(subject_id: int) -> dict:
    """Retorna o badge atual de uma matéria."""
    hours = db.get_total_hours(subject_id=subject_id)
    current = None
    next_badge = SUBJECT_BADGES[0] if SUBJECT_BADGES else None

    for i, badge in enumerate(SUBJECT_BADGES):
        if hours >= badge["min_hours"]:
            current = badge
            next_badge = SUBJECT_BADGES[i + 1] if i + 1 < len(SUBJECT_BADGES) else None
        else:
            if current is None:
                next_badge = badge
            break

    return {
        "badge": current,
        "next_badge": next_badge,
        "hours": round(hours, 1),
    }
