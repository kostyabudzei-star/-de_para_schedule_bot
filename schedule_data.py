# -*- coding: utf-8 -*-
"""
schedule_data.py
=================
Тут зберігається весь розклад занять та допоміжні функції для роботи з ним.
Просто відредагуй словник SCHEDULE нижче під свій розклад.

Формат одного заняття:
{
    "pair": 1,                 # номер пари (див. PAIR_TIMES нижче)
    "subject": "Назва предмета",
    "type": "Лекція",          # Лекція / Практика / Лабораторна і т.д. (не обов'язково)
    "building": "Корпус 1",
    "room": "301",
    "week": "any",             # "any" - щотижня, "odd" - лише чисельник, "even" - лише знаменник
}
"""

from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------
# 1. ЧАС ПАР
# ---------------------------------------------------------------------------
# Номер пари -> (початок, кінець) у форматі "HH:MM"
PAIR_TIMES = {
    1: ("08:30", "10:05"),
    2: ("10:20", "11:55"),
    3: ("12:10", "13:45"),
    4: ("14:00", "15:35"),
    5: ("15:50", "17:25"),
    6: ("17:35", "19:10"),
}

# ---------------------------------------------------------------------------
# 2. РОЗКЛАД ЗАНЯТЬ (відредагуй під себе)
# ---------------------------------------------------------------------------
SCHEDULE = {
    "monday": [
        {"pair": 1, "subject": "Вища математика", "type": "Лекція",
         "building": "Корпус 1", "room": "301", "week": "any"},
        {"pair": 2, "subject": "Основи програмування", "type": "Практика",
         "building": "Корпус 2", "room": "105", "week": "any"},
        {"pair": 3, "subject": "Фізика", "type": "Лекція",
         "building": "Корпус 1", "room": "210", "week": "odd"},
        {"pair": 3, "subject": "Англійська мова", "type": "Практика",
         "building": "Корпус 3", "room": "12", "week": "even"},
    ],
    "tuesday": [
        {"pair": 2, "subject": "Дискретна математика", "type": "Лекція",
         "building": "Корпус 1", "room": "215", "week": "any"},
        {"pair": 3, "subject": "Бази даних", "type": "Лабораторна",
         "building": "Корпус 2", "room": "310", "week": "any"},
        {"pair": 4, "subject": "Фізичне виховання", "type": "Практика",
         "building": "Спорткомплекс", "room": "Зал 1", "week": "any"},
    ],
    "wednesday": [
        {"pair": 1, "subject": "Англійська мова", "type": "Практика",
         "building": "Корпус 3", "room": "12", "week": "odd"},
        {"pair": 2, "subject": "Алгоритми та структури даних", "type": "Лекція",
         "building": "Корпус 2", "room": "104", "week": "any"},
        {"pair": 3, "subject": "Алгоритми та структури даних", "type": "Практика",
         "building": "Корпус 2", "room": "104", "week": "any"},
    ],
    "thursday": [
        {"pair": 1, "subject": "Web-технології", "type": "Лекція",
         "building": "Корпус 2", "room": "201", "week": "any"},
        {"pair": 2, "subject": "Web-технології", "type": "Лабораторна",
         "building": "Корпус 2", "room": "201", "week": "any"},
        {"pair": 4, "subject": "Філософія", "type": "Лекція",
         "building": "Корпус 1", "room": "101", "week": "even"},
    ],
    "friday": [
        {"pair": 1, "subject": "Операційні системи", "type": "Лекція",
         "building": "Корпус 1", "room": "305", "week": "any"},
        {"pair": 2, "subject": "Операційні системи", "type": "Лабораторна",
         "building": "Корпус 1", "room": "305", "week": "any"},
    ],
    "saturday": [],
    "sunday": [],
}

# ---------------------------------------------------------------------------
# 3. ДОПОМІЖНІ СЛОВНИКИ
# ---------------------------------------------------------------------------
WEEKDAY_NAMES_UA = {
    "monday": "Понеділок",
    "tuesday": "Вівторок",
    "wednesday": "Середа",
    "thursday": "Четвер",
    "friday": "П'ятниця",
    "saturday": "Субота",
    "sunday": "Неділя",
}

WEEKDAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

PYTHON_WEEKDAY_TO_KEY = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}

# ---------------------------------------------------------------------------
# 4. ЛОГІКА ЧИСЕЛЬНИК / ЗНАМЕННИК
# ---------------------------------------------------------------------------
# Дата понеділка будь-якого тижня, який ти вважаєш ЧИСЕЛЬНИКОМ (odd).
# Зміни цю дату на реальний початок навчального семестру / чисельника у твоєму ВНЗ.
WEEK_PARITY_REFERENCE = date(2025, 9, 1)  # понеділок = чисельник


def get_week_parity(d: date) -> str:
    """Повертає 'odd' (чисельник) або 'even' (знаменник) для заданої дати."""
    days_diff = (d - WEEK_PARITY_REFERENCE).days
    week_index = days_diff // 7
    return "odd" if week_index % 2 == 0 else "even"


def get_week_parity_ua(d: date) -> str:
    parity = get_week_parity(d)
    return "Чисельник" if parity == "odd" else "Знаменник"


def get_pairs_for_date(d: date):
    """Повертає відсортований список пар для конкретної дати з урахуванням чисельника/знаменника."""
    key = PYTHON_WEEKDAY_TO_KEY[d.weekday()]
    day_pairs = SCHEDULE.get(key, [])
    parity = get_week_parity(d)
    filtered = [p for p in day_pairs if p.get("week", "any") in ("any", parity)]
    filtered.sort(key=lambda p: PAIR_TIMES[p["pair"]][0])
    return filtered


def parse_time_on_date(time_str: str, d: date, tz):
    """Перетворює 'HH:MM' + дату на datetime з таймзоною."""
    hours, minutes = map(int, time_str.split(":"))
    return datetime(d.year, d.month, d.day, hours, minutes, tzinfo=tz)


def find_next_pair_state(now: datetime, tz, max_days_ahead: int = 14):
    """
    Визначає поточний стан розкладу відносно моменту `now`.

    Повертає кортеж (status, pair, start_dt, end_dt, day_pairs):
      status == "ongoing"          -> зараз триває пара `pair`
      status == "upcoming_today"   -> сьогодні буде пара `pair` (перерва або ще не почались пари)
      status == "upcoming_future"  -> сьогодні пар більше немає, наступна пара `pair` в інший день
      status is None                -> найближчих пар не знайдено взагалі (малоймовірно)
    """
    today = now.date()
    pairs_today = get_pairs_for_date(today)

    for p in pairs_today:
        start_t, end_t = PAIR_TIMES[p["pair"]]
        start_dt = parse_time_on_date(start_t, today, tz)
        end_dt = parse_time_on_date(end_t, today, tz)
        if start_dt <= now < end_dt:
            return "ongoing", p, start_dt, end_dt, pairs_today
        if now < start_dt:
            return "upcoming_today", p, start_dt, end_dt, pairs_today

    # Сьогодні пар для проведення більше немає (або взагалі не було) -> шукаємо далі
    for offset in range(1, max_days_ahead + 1):
        future_date = today + timedelta(days=offset)
        pairs = get_pairs_for_date(future_date)
        if pairs:
            p = pairs[0]
            start_t, end_t = PAIR_TIMES[p["pair"]]
            start_dt = parse_time_on_date(start_t, future_date, tz)
            end_dt = parse_time_on_date(end_t, future_date, tz)
            return "upcoming_future", p, start_dt, end_dt, pairs

    return None, None, None, None, []
