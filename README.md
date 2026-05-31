# 🚀 StarCasino — Telegram Bot + Mini App

## Структура проекта

```
telegram-casino/
├── bot/
│   └── bot.py          ← Telegram-бот (Python)
└── miniapp/
    └── index.html      ← Mini App (фронтенд)
```

---

## 🤖 Настройка бота

### 1. Установка зависимостей
```bash
pip install pyTelegramBotAPI
```

### 2. Создай бота
- Открой @BotFather в Telegram
- Напиши `/newbot` и следуй инструкциям
- Скопируй токен и вставь в `BOT_TOKEN` в `bot.py`

### 3. Включи Telegram Stars
- В @BotFather: `/mybots` → выбери бота → `Payments`
- Выбери **Telegram Stars** (бесплатно, без provider token)
- `PROVIDER_TOKEN` оставь пустым `""`

### 4. Настрой Mini App
- Разместите `index.html` на хостинге с HTTPS (Vercel, Netlify, GitHub Pages)
- В @BotFather: `/mybots` → `Bot Settings` → `Menu Button` → укажи URL
- Вставь URL в переменную `MINI_APP_URL` в `bot.py`

### 5. Запуск
```bash
python bot.py
```

---

## 🎮 Mini App — функции

### 🚀 Ракета
- Минимальная ставка: **50 ⭐**
- Перед запуском: **5-секундный отсчёт**
- Во время игры: множитель растёт от ×1.00
- Кнопка **"ЗАБРАТЬ"** — зафиксировать выигрыш
- Ракета случайно взрывается (дом имеет преимущество)

**Шансы краша:**
| Диапазон | Вероятность |
|----------|-------------|
| ×1.0–1.5 | 40% |
| ×1.5–2.0 | 25% |
| ×2.0–3.0 | 15% |
| ×3.0–5.0 | 10% |
| ×5.0–10  | 7% |
| ×10–25   | 3% |

### 🎁 Кейсы
| Кейс | Стоимость |
|------|-----------|
| Базовый | 100 ⭐ |
| Синий | 250 ⭐ |
| Фиолетовый | 300 ⭐ |
| Легенда | 999 ⭐ |

Призы от 10 до 1000 ⭐ с разными шансами (дом всегда в плюсе).

### 🎡 Колесо удачи
- Стоимость: **50 ⭐**
- Призы: 5, 10, 30, 50, 100, 200, 500 ⭐
- Анимация вращения + фейерверк при выигрыше

---

## ⚠️ Важные замечания

1. **Безопасность**: В production-версии ОБЯЗАТЕЛЬНО валидируй `initData` от Telegram на сервере (HMAC-SHA256), чтобы пользователи не могли подделать баланс.

2. **Баланс**: Сейчас Mini App передаёт баланс через `tg.sendData()`. В реальном проекте нужен бэкенд-сервер (Flask/FastAPI) с API-эндпоинтами.

3. **Telegram Stars**: В `currency` указан `"XTR"` — это валюта Stars. `PROVIDER_TOKEN` должен быть пустой строкой `""`.

4. **Хостинг Mini App**: Обязательно HTTPS. Telegram не откроет Mini App по HTTP.

---

## 🛠 Рекомендуемый стек для production

```
Backend:  Python FastAPI + PostgreSQL
Frontend: index.html на Vercel/Cloudflare Pages  
Bot:      python-telegram-bot или aiogram
Auth:     Валидация Telegram initData
```
