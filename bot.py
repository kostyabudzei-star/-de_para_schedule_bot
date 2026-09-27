# -*- coding: utf-8 -*-
"""
bot.py
======
Telegram-бот для студентів: показує поточну/наступну пару та розклад
на сьогодні / завтра / тиждень. Побудований на aiogram 3.x.

Запуск:
    python bot.py

Токен бота береться зі змінної середовища BOT_TOKEN (файл .env).
"""

import asyncio
import logging
import os
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    BotCommand,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from dotenv import load_dotenv

from schedule_data import (
    PAIR_TIMES,
    WEEKDAY_NAMES_UA,
    find_next_pair_state,
    get_pairs_for_date,
    get_week_parity_ua,
)

# ---------------------------------------------------------------------------
# Налаштування
# ---------------------------------------------------------------------------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "Не знайдено BOT_TOKEN. Створи файл .env на основі .env.example "
        "і встав туди токен, отриманий у @BotFather."
    )

TIMEZONE = ZoneInfo("Europe/Kyiv")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()

BTN_NOW = "⏱ Зараз"
BTN_TODAY = "📅 На сьогодні"
BTN_TOMORROW = "📆 На завтра"
BTN_WEEK = "🗓 На тиждень"


# ---------------------------------------------------------------------------
# Клавіатура
# ---------------------------------------------------------------------------
def main_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=BTN_NOW), KeyboardButton(text=BTN_TODAY)],
        [KeyboardButton(text=BTN_TOMORROW), KeyboardButton(text=BTN_WEEK)],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


# ---------------------------------------------------------------------------
# Форматування
# ---------------------------------------------------------------------------
def format_timedelta(td: timedelta) -> str:
    total_minutes = max(0, int(td.total_seconds() // 60))
    hours, minutes = divmod(total_minutes, 60)
    parts = []
    if hours:
        parts.append(f"{hours} год")
    parts.append(f"{minutes} хв")
    return " ".join(parts)


def format_pair_block(pair: dict) -> str:
    start, end = PAIR_TIMES[pair["pair"]]
    pair_type = pair.get("type", "")
    type_str = f" ({pair_type})" if pair_type else ""
    return (
        f"🔹 <b>{pair['pair']} пара</b> | 🕐 {start}–{end}\n"
        f"📘 {pair['subject']}{type_str}\n"
        f"🏢 {pair['building']}, ауд. {pair['room']}"
    )


def build_day_text(d: date, title: str) -> str:
    pairs = get_pairs_for_date(d)
    parity_ua = get_week_parity_ua(d)
    header = (
        f"📅 <b>{title}</b> — {d.strftime('%d.%m.%Y')}\n"
        f"🔁 Тиждень: <b>{parity_ua}</b>\n\n"
    )
    if not pairs:
        return header + "🎉 Пар немає, можна відпочивати!"

    blocks = [format_pair_block(p) for p in pairs]
    return header + "\n\n".join(blocks)


def build_week_text(today: date) -> str:
    monday = today - timedelta(days=today.weekday())
    parity_ua = get_week_parity_ua(monday)

    lines = [f"🗓 <b>Розклад на тиждень</b>\n🔁 Тиждень: <b>{parity_ua}</b>\n"]

    for offset in range(7):
        d = monday + timedelta(days=offset)
        weekday_key = list(WEEKDAY_NAMES_UA.keys())[offset]
        day_name = WEEKDAY_NAMES_UA[weekday_key]
        pairs = get_pairs_for_date(d)

        marker = " 👈" if d == today else ""
        lines.append(f"\n📌 <b>{day_name}</b> ({d.strftime('%d.%m')}){marker}")

        if not pairs:
            lines.append("   — пар немає")
        else:
            for p in pairs:
                start, end = PAIR_TIMES[p["pair"]]
                pair_type = f" ({p.get('type')})" if p.get("type") else ""
                lines.append(
                    f"   {p['pair']} пара {start}–{end}: {p['subject']}{pair_type} "
                    f"— {p['building']}, ауд. {p['room']}"
                )

    return "\n".join(lines)


def build_now_text() -> str:
    now = date_time_now()
    status, pair, start_dt, end_dt, pairs_of_that_day = find_next_pair_state(now, TIMEZONE)

    if status is None:
        return "🤷 Не вдалося знайти жодної пари в найближчі два тижні. Перевір розклад."

    if status == "ongoing":
        remaining = end_dt - now
        return (
            "🔔 <b>Зараз триває пара</b>\n\n"
            f"{format_pair_block(pair)}\n\n"
            f"⏳ До кінця пари: <b>{format_timedelta(remaining)}</b>"
        )

    if status == "upcoming_today":
        remaining = start_dt - now
        is_first_pair_of_day = pairs_of_that_day and pair == pairs_of_that_day[0]
        title = (
            "⏳ <b>Пари ще не почались</b>\nДо початку першої пари сьогодні:"
            if is_first_pair_of_day
            else "☕ <b>Перерва</b>\nНаступна пара:"
        )
        return (
            f"{title}\n\n"
            f"{format_pair_block(pair)}\n\n"
            f"⏳ До початку: <b>{format_timedelta(remaining)}</b>"
        )

    # status == "upcoming_future"
    remaining = start_dt - now
    pair_date = start_dt.date()
    if pair_date == now.date() + timedelta(days=1):
        when = "завтра"
    else:
        when = pair_date.strftime("%d.%m.%Y")

    return (
        "🌙 <b>На сьогодні пар більше немає</b>\n\n"
        f"Наступна пара {when}:\n\n"
        f"{format_pair_block(pair)}\n\n"
        f"⏳ Залишилось: <b>{format_timedelta(remaining)}</b>"
    )


def date_time_now():
    from datetime import datetime

    return datetime.now(TIMEZONE)


# ---------------------------------------------------------------------------
# Хендлери
# ---------------------------------------------------------------------------
@router.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "👋 Привіт! Я бот-розклад занять.\n\n"
        "Ось що я вмію:\n"
        f"{BTN_NOW} — що зараз відбувається (пара / перерва)\n"
        f"{BTN_TODAY} — розклад на сьогодні\n"
        f"{BTN_TOMORROW} — розклад на завтра\n"
        f"{BTN_WEEK} — розклад на весь тиждень\n\n"
        "Обери кнопку внизу або скористайся командами /now, /today, /tomorrow, /week."
    )
    await message.answer(text, reply_markup=main_keyboard())


@router.message(Command("now"))
@router.message(F.text == BTN_NOW)
async def cmd_now(message: Message):
    await message.answer(build_now_text(), reply_markup=main_keyboard())


@router.message(Command("today"))
@router.message(F.text == BTN_TODAY)
async def cmd_today(message: Message):
    today = date_time_now().date()
    await message.answer(build_day_text(today, "Розклад на сьогодні"), reply_markup=main_keyboard())


@router.message(Command("tomorrow"))
@router.message(F.text == BTN_TOMORROW)
async def cmd_tomorrow(message: Message):
    tomorrow = date_time_now().date() + timedelta(days=1)
    await message.answer(build_day_text(tomorrow, "Розклад на завтра"), reply_markup=main_keyboard())


@router.message(Command("week"))
@router.message(F.text == BTN_WEEK)
async def cmd_week(message: Message):
    today = date_time_now().date()
    await message.answer(build_week_text(today), reply_markup=main_keyboard())


# ---------------------------------------------------------------------------
# Точка входу
# ---------------------------------------------------------------------------
async def set_commands(bot: Bot):
    await bot.set_my_commands(
        [
            BotCommand(command="now", description="Що зараз (пара/перерва)"),
            BotCommand(command="today", description="Розклад на сьогодні"),
            BotCommand(command="tomorrow", description="Розклад на завтра"),
            BotCommand(command="week", description="Розклад на тиждень"),
        ]
    )


async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    await set_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Бот запущено. Очікую повідомлення...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
