"""
StarCasino Telegram Bot
Требования: pip install pyTelegramBotAPI
"""

import telebot
from telebot import types
from telebot.types import LabeledPrice
import sqlite3
import json
import os
import sys
import signal
import atexit
from datetime import datetime
from pathlib import Path

# ========================
# КОНФИГ
# ========================
BOT_TOKEN   = "8501183606:AAH4t33WHe209h0Bvhth6S0bsEVUb4R-UPs"
MINI_APP_URL = "https://6a1bfa11ab821419078411de--cheery-tarsier-79c890.netlify.app/"
PROVIDER_TOKEN = ""  # пусто для Telegram Stars

# Куда сохранять отчёт при выходе
DESKTOP = Path.home() / "Desktop"
REPORT_PATH = DESKTOP / f"StarCasino_report_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"

bot = telebot.TeleBot(BOT_TOKEN)

# ========================
# ЦВЕТА ДЛЯ КОНСОЛИ
# ========================
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    RED    = "\033[91m"
    PURPLE = "\033[95m"
    BLUE   = "\033[94m"
    GREY   = "\033[90m"
    WHITE  = "\033[97m"

def fmt_user(user_id, username, first_name=""):
    u = f"@{username}" if username else f"id:{user_id}"
    name = f" ({first_name})" if first_name else ""
    return f"{C.CYAN}{u}{name}{C.RESET} {C.GREY}[{user_id}]{C.RESET}"

def log(icon, color, label, user_id, username, first_name, detail=""):
    now = datetime.now().strftime("%H:%M:%S")
    user_str = fmt_user(user_id, username, first_name)
    det = f"  {C.GREY}→ {detail}{C.RESET}" if detail else ""
    line = f"{C.GREY}[{now}]{C.RESET} {color}{icon} {label:<18}{C.RESET}  {user_str}{det}"
    print(line)

# ========================
# БД
# ========================
def get_conn():
    return sqlite3.connect("casino.db")

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY,
            username      TEXT,
            first_name    TEXT,
            balance       INTEGER DEFAULT 0,
            total_deposited INTEGER DEFAULT 0,
            games_played  INTEGER DEFAULT 0,
            created_at    TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            username    TEXT,
            first_name  TEXT,
            action      TEXT,
            detail      TEXT,
            amount      INTEGER DEFAULT 0,
            balance_after INTEGER DEFAULT 0,
            created_at  TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            type        TEXT,
            amount      INTEGER,
            payload     TEXT,
            created_at  TEXT
        )
    """)
    conn.commit()
    conn.close()

def db_log(user_id, username, first_name, action, detail="", amount=0, balance_after=0):
    """Записывает действие пользователя в БД"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO activity_log (user_id, username, first_name, action, detail, amount, balance_after, created_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (user_id, username or "", first_name or "", action, detail, amount, balance_after, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def create_user(user_id, username, first_name):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name, balance, created_at) VALUES (?,?,?,0,?)",
        (user_id, username, first_name, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def add_balance(user_id, amount):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET balance=balance+?, total_deposited=total_deposited+? WHERE user_id=?",
        (amount, amount, user_id)
    )
    conn.commit()
    conn.close()

def log_tx(user_id, type_, amount, payload=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO transactions (user_id, type, amount, payload, created_at) VALUES (?,?,?,?,?)",
        (user_id, type_, amount, payload, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

# ========================
# /START
# ========================
@bot.message_handler(commands=['start'])
def start(message):
    u = message.from_user
    create_user(u.id, u.username or "", u.first_name or "")
    balance = get_balance(u.id)

    # Консоль
    log("👤", C.GREEN, "ВОШЁЛ В БОТ", u.id, u.username, u.first_name,
        f"баланс: {balance}⭐")
    # БД лог
    db_log(u.id, u.username, u.first_name, "START", "Открыл бота", balance_after=balance)

    text = (
        f"🌟 *Добро пожаловать в StarCasino!*\n\n"
        f"Привет, *{u.first_name}*! Ты попал в лучшее крипто-казино на Telegram.\n\n"
        f"💫 Здесь тебя ждут:\n"
        f"  🚀 *Ракета* — поймай нужный икс\n"
        f"  🎁 *Кейсы* — испытай удачу\n"
        f"  🎡 *Колесо* — крути и выигрывай\n\n"
        f"⭐ Твой баланс: *{balance} звёзд*\n\n"
        f"_Пополни баланс и начни играть прямо сейчас!_"
    )

    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🎮 ИГРАТЬ", web_app=types.WebAppInfo(
            url=f"{MINI_APP_URL}?balance={balance}&user_id={u.id}")),
        types.InlineKeyboardButton("⭐ ПОПОЛНИТЬ", callback_data="deposit"),
    )
    kb.add(
        types.InlineKeyboardButton("💰 МОЙ БАЛАНС", callback_data="balance"),
        types.InlineKeyboardButton("📊 ИСТОРИЯ", callback_data="history"),
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=kb)

# ========================
# БАЛАНС
# ========================
@bot.callback_query_handler(func=lambda c: c.data == "balance")
def show_balance(call):
    u = call.from_user
    balance = get_balance(u.id)
    bot.answer_callback_query(call.id)

    log("💰", C.YELLOW, "ЗАПРОС БАЛАНСА", u.id, u.username, u.first_name,
        f"баланс: {balance}⭐")
    db_log(u.id, u.username, u.first_name, "CHECK_BALANCE", f"Баланс: {balance}⭐", balance_after=balance)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⭐ Пополнить", callback_data="deposit"))
    kb.add(types.InlineKeyboardButton("🎮 Играть", web_app=types.WebAppInfo(
        url=f"{MINI_APP_URL}?balance={balance}&user_id={u.id}")))
    bot.send_message(call.message.chat.id, f"💰 *Твой баланс:* `{balance} ⭐`",
                     parse_mode="Markdown", reply_markup=kb)

# ========================
# ПОПОЛНЕНИЕ
# ========================
@bot.callback_query_handler(func=lambda c: c.data == "deposit")
def deposit_menu(call):
    u = call.from_user
    bot.answer_callback_query(call.id)

    log("⭐", C.BLUE, "ОТКРЫЛ ПОПОЛНЕНИЕ", u.id, u.username, u.first_name)
    db_log(u.id, u.username, u.first_name, "OPEN_DEPOSIT", "Открыл меню пополнения")

    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("100 ⭐",  callback_data="pay_100"),
        types.InlineKeyboardButton("300 ⭐",  callback_data="pay_300"),
        types.InlineKeyboardButton("500 ⭐",  callback_data="pay_500"),
    )
    kb.add(
        types.InlineKeyboardButton("1000 ⭐", callback_data="pay_1000"),
        types.InlineKeyboardButton("2500 ⭐", callback_data="pay_2500"),
        types.InlineKeyboardButton("5000 ⭐", callback_data="pay_5000"),
    )
    kb.add(types.InlineKeyboardButton("✏️ Другая сумма", callback_data="pay_custom"))
    kb.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back_start"))

    bot.send_message(call.message.chat.id,
                     "⭐ *Пополнение баланса*\n\nВыбери сумму или введи свою:",
                     parse_mode="Markdown", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("pay_"))
def handle_pay(call):
    u = call.from_user
    bot.answer_callback_query(call.id)
    amount_str = call.data.replace("pay_", "")

    if amount_str == "custom":
        log("✏️", C.BLUE, "ВВОД СУММЫ", u.id, u.username, u.first_name, "своя сумма")
        db_log(u.id, u.username, u.first_name, "DEPOSIT_CUSTOM_INPUT", "Выбрал ввод своей суммы")
        msg = bot.send_message(call.message.chat.id, "✏️ Введи сумму в звёздах (минимум 50):")
        bot.register_next_step_handler(msg, process_custom_amount)
        return

    amount = int(amount_str)
    log("💳", C.BLUE, "ВЫБРАЛ СУММУ", u.id, u.username, u.first_name, f"{amount}⭐")
    db_log(u.id, u.username, u.first_name, "DEPOSIT_SELECT", f"Выбрал сумму {amount}⭐", amount=amount)
    send_invoice(call.message.chat.id, u.id, u.username or "", u.first_name or "", amount)

def process_custom_amount(message):
    u = message.from_user
    try:
        amount = int(message.text.strip())
        if amount < 50:
            bot.send_message(message.chat.id, "❌ Минимальная сумма — 50 ⭐")
            log("❌", C.RED, "СУММА МАЛА", u.id, u.username, u.first_name, f"ввёл {message.text}")
            return
        if amount > 10000:
            bot.send_message(message.chat.id, "❌ Максимальная сумма — 10000 ⭐")
            log("❌", C.RED, "СУММА ВЕЛИКА", u.id, u.username, u.first_name, f"ввёл {message.text}")
            return
        log("💳", C.BLUE, "СВОЯ СУММА", u.id, u.username, u.first_name, f"{amount}⭐")
        db_log(u.id, u.username, u.first_name, "DEPOSIT_CUSTOM", f"Своя сумма: {amount}⭐", amount=amount)
        send_invoice(message.chat.id, u.id, u.username or "", u.first_name or "", amount)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введи число!")
        log("❌", C.RED, "НЕВЕРНЫЙ ВВОД", u.id, u.username, u.first_name, f"ввёл: '{message.text}'")

def send_invoice(chat_id, user_id, username, first_name, amount):
    try:
        bot.send_invoice(
            chat_id=chat_id,
            title=f"Пополнение {amount} ⭐",
            description=f"Пополнение баланса StarCasino на {amount} Telegram Stars",
            invoice_payload=f"deposit_{user_id}_{amount}",
            provider_token=PROVIDER_TOKEN,
            currency="XTR",
            prices=[LabeledPrice(f"{amount} Stars", amount)],
        )
        log("📨", C.BLUE, "ИНВОЙС ОТПРАВЛЕН", user_id, username, first_name, f"{amount}⭐")
        db_log(user_id, username, first_name, "INVOICE_SENT", f"Инвойс на {amount}⭐", amount=amount)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка создания платежа: {e}")
        log("❌", C.RED, "ОШИБКА ИНВОЙСА", user_id, username, first_name, str(e))

# ========================
# PRE-CHECKOUT
# ========================
@bot.pre_checkout_query_handler(func=lambda q: True)
def pre_checkout(query):
    u = query.from_user
    log("🔄", C.PURPLE, "PRE-CHECKOUT", u.id, u.username, u.first_name,
        f"payload: {query.invoice_payload}")
    db_log(u.id, u.username, u.first_name, "PRE_CHECKOUT", query.invoice_payload)
    bot.answer_pre_checkout_query(query.id, ok=True)

# ========================
# УСПЕШНАЯ ОПЛАТА
# ========================
@bot.message_handler(content_types=['successful_payment'])
def payment_success(message):
    u = message.from_user
    payment = message.successful_payment
    payload = payment.invoice_payload   # "deposit_USERID_AMOUNT"

    parts = payload.split("_")
    user_id = int(parts[1])
    amount  = int(parts[2])

    add_balance(user_id, amount)
    log_tx(user_id, "deposit", amount, payload)
    new_balance = get_balance(user_id)

    log("✅", C.GREEN, "ОПЛАТА ПРОШЛА", u.id, u.username, u.first_name,
        f"+{amount}⭐  →  баланс: {new_balance}⭐")
    db_log(u.id, u.username, u.first_name, "PAYMENT_SUCCESS",
           f"Оплачено {amount}⭐, новый баланс {new_balance}⭐",
           amount=amount, balance_after=new_balance)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        "🎮 ИГРАТЬ",
        web_app=types.WebAppInfo(url=f"{MINI_APP_URL}?balance={new_balance}&user_id={user_id}")
    ))
    bot.send_message(
        message.chat.id,
        f"✅ *Оплата прошла успешно!*\n\n"
        f"💫 Зачислено: *+{amount} ⭐*\n"
        f"💰 Новый баланс: *{new_balance} ⭐*\n\n"
        f"_Удачи в игре!_ 🚀",
        parse_mode="Markdown", reply_markup=kb
    )

# ========================
# ИСТОРИЯ
# ========================
@bot.callback_query_handler(func=lambda c: c.data == "history")
def show_history(call):
    u = call.from_user
    bot.answer_callback_query(call.id)

    log("📊", C.YELLOW, "ЗАПРОС ИСТОРИИ", u.id, u.username, u.first_name)
    db_log(u.id, u.username, u.first_name, "VIEW_HISTORY", "Открыл историю транзакций")

    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT type, amount, created_at FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 10",
              (u.id,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        bot.send_message(call.message.chat.id, "📊 Транзакций пока нет.")
        return

    text = "📊 *Последние транзакции:*\n\n"
    for type_, amount, date in rows:
        dt = date[:10] if date else ""
        text += f"• {type_} | *+{amount} ⭐* | {dt}\n"
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

# ========================
# НАЗАД
# ========================
@bot.callback_query_handler(func=lambda c: c.data == "back_start")
def back_start(call):
    bot.answer_callback_query(call.id)
    start(call.message)

# ========================
# WEB APP DATA (из Mini App)
# ========================
@bot.message_handler(content_types=['web_app_data'])
def web_app_data(message):
    u = message.from_user
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get('action', '')

        if action == 'update_balance':
            new_balance = int(data.get('balance', 0))
            conn = get_conn()
            c = conn.cursor()
            c.execute("UPDATE users SET balance=? WHERE user_id=?", (new_balance, u.id))
            conn.commit()
            conn.close()
            log("🔄", C.CYAN, "БАЛАНС ОБНОВЛЁН", u.id, u.username, u.first_name,
                f"новый баланс: {new_balance}⭐")
            db_log(u.id, u.username, u.first_name, "BALANCE_SYNC",
                   f"Mini App обновил баланс: {new_balance}⭐", balance_after=new_balance)

        elif action == 'game_result':
            game      = data.get('game', 'unknown')
            result    = data.get('result', '')
            amount    = int(data.get('amount', 0))
            balance   = int(data.get('balance', 0))
            color     = C.GREEN if amount >= 0 else C.RED
            sign      = "+" if amount >= 0 else ""
            log("🎮", color, f"ИГРА: {game.upper()}", u.id, u.username, u.first_name,
                f"результат: {result}  {sign}{amount}⭐  баланс: {balance}⭐")
            db_log(u.id, u.username, u.first_name, f"GAME_{game.upper()}",
                   f"Результат: {result}, изменение: {sign}{amount}⭐",
                   amount=amount, balance_after=balance)

    except Exception as e:
        print(f"{C.RED}[Web app data error]{C.RESET} {e}")

# ========================
# ЭКСПОРТ ОТЧЁТА
# ========================
def export_report():
    """Вызывается при завершении бота — сохраняет структурированный отчёт на рабочий стол"""
    print(f"\n{C.YELLOW}📄 Сохраняю отчёт...{C.RESET}")
    try:
        conn = get_conn()
        c = conn.cursor()

        # Все пользователи
        c.execute("""
            SELECT user_id, username, first_name, balance, total_deposited, games_played, created_at
            FROM users ORDER BY created_at
        """)
        users = c.fetchall()

        # Все события (activity_log) сгруппированные по пользователю
        c.execute("""
            SELECT user_id, username, first_name, action, detail, amount, balance_after, created_at
            FROM activity_log ORDER BY user_id, created_at
        """)
        logs = c.fetchall()
        conn.close()

        now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        lines = []
        lines.append("=" * 70)
        lines.append(f"  StarCasino — Отчёт активности")
        lines.append(f"  Сформирован: {now_str}")
        lines.append("=" * 70)
        lines.append(f"  Всего пользователей: {len(users)}")
        lines.append(f"  Всего событий:       {len(logs)}")
        lines.append("=" * 70)

        # Группируем логи по user_id
        from collections import defaultdict
        user_logs = defaultdict(list)
        for row in logs:
            user_logs[row[0]].append(row)

        for usr in users:
            uid, uname, fname, balance, total_dep, games, created = usr
            uname_str = f"@{uname}" if uname else f"id:{uid}"
            lines.append("")
            lines.append("─" * 70)
            lines.append(f"  👤 ПОЛЬЗОВАТЕЛЬ: {fname or 'Без имени'}  ({uname_str})")
            lines.append(f"     ID:              {uid}")
            lines.append(f"     Username:        @{uname or '—'}")
            lines.append(f"     Имя:             {fname or '—'}")
            lines.append(f"     Текущий баланс:  {balance} ⭐")
            lines.append(f"     Всего пополнено: {total_dep} ⭐")
            lines.append(f"     Зарегистрирован: {created[:19] if created else '—'}")
            lines.append("")
            lines.append("  📋 ИСТОРИЯ ДЕЙСТВИЙ:")
            lines.append("  " + "-" * 66)

            ul = user_logs.get(uid, [])
            if not ul:
                lines.append("     (нет записей)")
            else:
                for row in ul:
                    _, _, _, action, detail, amount, bal_after, created_at = row
                    ts = created_at[:19] if created_at else "—"
                    amt_str = f"  [{'+' if amount >= 0 else ''}{amount}⭐]" if amount != 0 else ""
                    bal_str = f"  → баланс: {bal_after}⭐" if bal_after else ""
                    lines.append(f"     [{ts}]  {action:<22} {detail}{amt_str}{bal_str}")

            lines.append("  " + "-" * 66)

        lines.append("")
        lines.append("=" * 70)
        lines.append("  Конец отчёта")
        lines.append("=" * 70)

        DESKTOP.mkdir(parents=True, exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        print(f"{C.GREEN}✅ Отчёт сохранён:{C.RESET} {REPORT_PATH}")
    except Exception as e:
        print(f"{C.RED}❌ Ошибка при сохранении отчёта: {e}{C.RESET}")

def on_exit(*args):
    export_report()
    sys.exit(0)

# ========================
# ЗАПУСК
# ========================
if __name__ == "__main__":
    init_db()

    # Регистрируем экспорт при выходе
    atexit.register(export_report)
    signal.signal(signal.SIGINT,  on_exit)
    signal.signal(signal.SIGTERM, on_exit)

    # Шапка консоли
    print(f"\n{C.BOLD}{C.YELLOW}{'═'*60}{C.RESET}")
    print(f"{C.BOLD}{C.YELLOW}   🚀 StarCasino Bot  —  Мониторинг активности{C.RESET}")
    print(f"{C.BOLD}{C.YELLOW}{'═'*60}{C.RESET}")
    print(f"{C.GREY}   Отчёт при выходе → {REPORT_PATH}{C.RESET}")
    print(f"{C.YELLOW}{'─'*60}{C.RESET}\n")

    print(f"{C.GREY}  Иконки событий:{C.RESET}")
    print(f"  {C.GREEN}👤 Вошёл в бот{C.RESET}   {C.YELLOW}💰 Баланс{C.RESET}   {C.BLUE}⭐ Пополнение{C.RESET}")
    print(f"  {C.GREEN}✅ Оплата{C.RESET}         {C.CYAN}🔄 Синхронизация{C.RESET}   {C.PURPLE}📊 История{C.RESET}")
    print(f"  {C.GREEN}🎮 Игра выиграна{C.RESET}  {C.RED}🎮 Игра проиграна{C.RESET}\n")
    print(f"{C.YELLOW}{'─'*60}{C.RESET}\n")

    bot.infinity_polling(skip_pending=True)