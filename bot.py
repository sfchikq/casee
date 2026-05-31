"""
StarCasino Telegram Bot
Требования: pip install pyTelegramBotAPI
"""

import telebot
from telebot import types
from telebot.types import LabeledPrice, ShippingAddress
import sqlite3
import json
import os
from datetime import datetime

# ========================
# КОНФИГ
# ========================
BOT_TOKEN = "YOUR_BOT_TOKEN"          # токен от @BotFather
MINI_APP_URL = "https://your-domain.com/miniapp"  # URL вашего Mini App
PROVIDER_TOKEN = ""  # Для Telegram Stars оставить пустым!

bot = telebot.TeleBot(BOT_TOKEN)

# ========================
# БД
# ========================
def init_db():
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 0,
            total_deposited INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            amount INTEGER,
            payload TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def create_user(user_id, username, first_name):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name, balance, created_at) VALUES (?,?,?,0,?)",
        (user_id, username, first_name, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def add_balance(user_id, amount):
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance=balance+?, total_deposited=total_deposited+? WHERE user_id=?",
              (amount, amount, user_id))
    conn.commit()
    conn.close()

def log_tx(user_id, type_, amount, payload=""):
    conn = sqlite3.connect("casino.db")
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
    user = message.from_user
    create_user(user.id, user.username or "", user.first_name or "")

    balance = get_balance(user.id)

    text = (
        f"🌟 *Добро пожаловать в StarCasino!*\n\n"
        f"Привет, *{user.first_name}*! Ты попал в лучшее крипто-казино на Telegram.\n\n"
        f"💫 Здесь тебя ждут:\n"
        f"  🚀 *Ракета* — поймай нужный икс\n"
        f"  🎁 *Кейсы* — испытай удачу\n"
        f"  🎡 *Колесо* — крути и выигрывай\n\n"
        f"⭐ Твой баланс: *{balance} звёзд*\n\n"
        f"_Пополни баланс и начни играть прямо сейчас!_"
    )

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🎮 ИГРАТЬ", web_app=types.WebAppInfo(url=f"{MINI_APP_URL}?balance={balance}&user_id={user.id}")),
        types.InlineKeyboardButton("⭐ ПОПОЛНИТЬ", callback_data="deposit"),
    )
    keyboard.add(
        types.InlineKeyboardButton("💰 МОЙ БАЛАНС", callback_data="balance"),
        types.InlineKeyboardButton("📊 ИСТОРИЯ", callback_data="history"),
    )

    bot.send_message(
        message.chat.id, text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ========================
# БАЛАНС
# ========================
@bot.callback_query_handler(func=lambda c: c.data == "balance")
def show_balance(call):
    balance = get_balance(call.from_user.id)
    bot.answer_callback_query(call.id)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⭐ Пополнить", callback_data="deposit"))
    keyboard.add(types.InlineKeyboardButton("🎮 Играть", web_app=types.WebAppInfo(url=f"{MINI_APP_URL}?balance={balance}&user_id={call.from_user.id}")))
    bot.send_message(
        call.message.chat.id,
        f"💰 *Твой баланс:* `{balance} ⭐`",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ========================
# ПОПОЛНЕНИЕ
# ========================
@bot.callback_query_handler(func=lambda c: c.data == "deposit")
def deposit_menu(call):
    bot.answer_callback_query(call.id)

    keyboard = types.InlineKeyboardMarkup(row_width=3)
    # Номиналы
    keyboard.add(
        types.InlineKeyboardButton("100 ⭐", callback_data="pay_100"),
        types.InlineKeyboardButton("300 ⭐", callback_data="pay_300"),
        types.InlineKeyboardButton("500 ⭐", callback_data="pay_500"),
    )
    keyboard.add(
        types.InlineKeyboardButton("1000 ⭐", callback_data="pay_1000"),
        types.InlineKeyboardButton("2500 ⭐", callback_data="pay_2500"),
        types.InlineKeyboardButton("5000 ⭐", callback_data="pay_5000"),
    )
    keyboard.add(types.InlineKeyboardButton("✏️ Другая сумма", callback_data="pay_custom"))
    keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="back_start"))

    bot.send_message(
        call.message.chat.id,
        "⭐ *Пополнение баланса*\n\nВыбери сумму или введи свою:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("pay_"))
def handle_pay(call):
    bot.answer_callback_query(call.id)
    amount_str = call.data.replace("pay_", "")

    if amount_str == "custom":
        msg = bot.send_message(
            call.message.chat.id,
            "✏️ Введи сумму в звёздах (минимум 50):",
        )
        bot.register_next_step_handler(msg, process_custom_amount)
        return

    amount = int(amount_str)
    send_invoice(call.message.chat.id, call.from_user.id, amount)

def process_custom_amount(message):
    try:
        amount = int(message.text.strip())
        if amount < 50:
            bot.send_message(message.chat.id, "❌ Минимальная сумма — 50 ⭐")
            return
        if amount > 10000:
            bot.send_message(message.chat.id, "❌ Максимальная сумма — 10000 ⭐")
            return
        send_invoice(message.chat.id, message.from_user.id, amount)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введи число!")

def send_invoice(chat_id, user_id, amount):
    """Отправляет инвойс Telegram Stars"""
    try:
        bot.send_invoice(
            chat_id=chat_id,
            title=f"Пополнение {amount} ⭐",
            description=f"Пополнение баланса StarCasino на {amount} Telegram Stars",
            payload=f"deposit_{user_id}_{amount}",
            provider_token=PROVIDER_TOKEN,   # пустая строка для Stars
            currency="XTR",                  # XTR = Telegram Stars
            prices=[LabeledPrice(f"{amount} Stars", amount)],  # 1 XTR = 1 Star
            photo_url="https://i.imgur.com/example.jpg",  # опционально
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка создания платежа: {e}")

# ========================
# PRE-CHECKOUT (обязательно!)
# ========================
@bot.pre_checkout_query_handler(func=lambda q: True)
def pre_checkout(query):
    """Telegram требует подтвердить перед оплатой"""
    bot.answer_pre_checkout_query(query.id, ok=True)

# ========================
# УСПЕШНАЯ ОПЛАТА
# ========================
@bot.message_handler(content_types=['successful_payment'])
def payment_success(message):
    payment = message.successful_payment
    payload = payment.invoice_payload  # "deposit_USERID_AMOUNT"

    parts = payload.split("_")
    user_id = int(parts[1])
    amount = int(parts[2])

    # Зачисляем Stars на баланс
    add_balance(user_id, amount)
    log_tx(user_id, "deposit", amount, payload)

    new_balance = get_balance(user_id)

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            "🎮 ИГРАТЬ",
            web_app=types.WebAppInfo(url=f"{MINI_APP_URL}?balance={new_balance}&user_id={user_id}")
        )
    )

    bot.send_message(
        message.chat.id,
        f"✅ *Оплата прошла успешно!*\n\n"
        f"💫 Зачислено: *+{amount} ⭐*\n"
        f"💰 Новый баланс: *{new_balance} ⭐*\n\n"
        f"_Удачи в игре!_ 🚀",
        parse_mode="Markdown",
        reply_markup=keyboard
    )

# ========================
# ИСТОРИЯ
# ========================
@bot.callback_query_handler(func=lambda c: c.data == "history")
def show_history(call):
    bot.answer_callback_query(call.id)
    conn = sqlite3.connect("casino.db")
    c = conn.cursor()
    c.execute(
        "SELECT type, amount, created_at FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT 10",
        (call.from_user.id,)
    )
    rows = c.fetchall()
    conn.close()

    if not rows:
        bot.send_message(call.message.chat.id, "📊 Транзакций пока нет.")
        return

    text = "📊 *Последние транзакции:*\n\n"
    for row in rows:
        type_, amount, date = row
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
# WEB APP DATA (баланс из Mini App)
# ========================
@bot.message_handler(content_types=['web_app_data'])
def web_app_data(message):
    """Получаем данные из Mini App"""
    try:
        data = json.loads(message.web_app_data.data)
        if data.get('action') == 'update_balance':
            # Обновляем баланс в БД (осторожно — валидируй на сервере!)
            new_balance = int(data.get('balance', 0))
            conn = sqlite3.connect("casino.db")
            c = conn.cursor()
            c.execute("UPDATE users SET balance=? WHERE user_id=?", (new_balance, message.from_user.id))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"Web app data error: {e}")

# ========================
# ЗАПУСК
# ========================
if __name__ == "__main__":
    init_db()
    print("🚀 StarCasino Bot запущен!")
    bot.infinity_polling(skip_pending=True)
