# ⚡ БЫСТРАЯ ИНТЕГРАЦИЯ v4.0

Всё готово! Вот что нужно сделать за 5 минут:

## ✅ Чек-лист интеграции

- [ ] Убедиться что есть .env с ключами
- [ ] Обновить requirements.txt  
- [ ] Переименовать файлы
- [ ] Запустить бот
- [ ] Запустить напоминания (опционально)

---

## Шаг за шагом

### 1️⃣ Готовые файлы

В папке `worker_git/` уже есть:

```
✅ database_with_ai.py       - Новая БД с user_stats
✅ bot_v4_with_ai.py         - Новый красивый бот
✅ reminder_scheduler.py      - Система напоминаний
✅ README_v4.md              - Полная документация
```

### 2️⃣ Обновить requirements.txt

Открой `worker_git/requirements.txt` и убедись что там:

```
python-telegram-bot==20.7
python-dotenv==1.0.0
groq==0.9.0
matplotlib==3.7.2
pillow==10.0.1
aiohttp==3.9.0
```

Если чего-то не хватает, добавь. Затем запусти:

```bash
cd worker_git
pip install -r requirements.txt
```

### 3️⃣ Переименовать файлы (ОПЦИЯ А - простая)

Если хочешь заменить старые файлы:

```bash
cd worker_git

# Backup старых (на всякий)
mv database.py database_old.py
mv bot.py bot_old.py

# Новые вместо старых
mv database_with_ai.py database.py
mv bot_v4_with_ai.py bot.py
```

**ИЛИ**

### 3️⃣ Оставить оба (ОПЦИЯ B - безопаснее)

Если боишься что-то сломать:

```bash
# Оставляешь оба варианта
# database.py + database_with_ai.py
# bot.py + bot_v4_with_ai.py

# И запускаешь новый:
python bot_v4_with_ai.py
```

### 4️⃣ .env файл

Убедись что в `worker_git/.env` есть:

```
TELEGRAM_BOT_TOKEN=your_telegram_token
GROQ_API_KEY=your_groq_api_key
```

Если нет - создай этот файл, иначе не будет работать!

### 5️⃣ Первый запуск

```bash
python bot.py
# или если оставил оба:
python bot_v4_with_ai.py
```

Бот должен выписать в консоль:

```
2024-01-15 10:30:00 - INFO - 🚀 Бот запущен!
```

Отправь `/start` в Telegram - увидишь новое красивое меню! ✨

### 6️⃣ Запустить напоминания (опционально)

В ОТДЕЛЬНОМ терминале:

```bash
# Для тестирования (сработает сейчас):
python reminder_scheduler.py test

# Для продакшена (каждый день в 9:00 UTC):
python reminder_scheduler.py
```

---

## 🎯 Что сейчас работает

- ✅ Красивое главное меню с эмодзи
- ✅ Все упражнения и категории работают
- ✅ Графики показываются
- ✅ **НОВОЕ: AI Тренер в личном чате!** 🤖
- ✅ **НОВОЕ: Напоминания через 5 дней** 🔔
- ✅ **НОВОЕ: Разные промты для разных действий** 💬

---

## 🚨 Если что-то не работает

### "ModuleNotFoundError: No module named 'groq'"

```bash
pip install groq aiohttp
```

### "GROQ_API_KEY not found"

Проверь .env файл, должно быть:
```
GROQ_API_KEY=gsk_...
```

Если нечего, получи ключ на https://console.groq.com

### "No module named 'database_with_ai'"

Если у тебя `bot_v4_with_ai.py`, то он ищет `database_with_ai.py`

**Решение:**
```bash
# Либо оба файла есть:
database_with_ai.py + bot_v4_with_ai.py  ✅

# Либо переименовал оба:
database.py + bot.py  ✅

# Но не смешивай: database_with_ai.py + bot.py ❌
```

### AI ничего не ответил

- Проверь интернет
- Проверь GROQ_API_KEY в console.groq.com
- Посмотри логи

Бот автоматически вернёт fallback ответ, так что не сломается.

---

## 📱 Тестирование

Напиши в боте:

1. `/start` - должно быть красивое главное меню
2. `💪 Грудь и бицепс` - должен показать упражнения
3. `💬 AI Тренер` - должно быть меню с 4 опциями
4. `💪 Мотивация` - должен дать мотивирующую фразу от AI

Если всё это работает - **ТЫ ГЕРОЙ!** 🎉

---

## 🔧 Как развивать дальше

**Добавить новое AI действие:**

1. Добавь в `PROMPTS` словарь (bot_v4_with_ai.py):
```python
'my_new_prompt': {
    'system': 'Твой кастомный промт...',
    'context': 'Описание'
}
```

2. Добавь функцию handler:
```python
async def my_ai_handler(update, context):
    response = await ask_ai("текст", "my_new_prompt")
    # Отправь ответ
```

3. Добавь кнопку в меню

**Готово!** 🚀

---

## 💾 Backup и миграция

Если уже был v3.1:

```bash
# 1. Backup БД
cp exercises.db exercises.db.backup

# 2. Запусти новую версию
python bot.py

# Все старые данные сохранятся!
# Плюс создадутся новые таблицы user_stats
```

---

## 🎉 ВСЁ!

Готово! Теперь у тебя есть:

✅ Красивый бот с эмодзи
✅ AI Тренер 
✅ Автоматические напоминания
✅ История прогресса
✅ Графики
✅ Полная поддержка MarkdownV2

**Жди пользователей!** 💪🔥

Если есть вопросы - смотри `README_v4.md` для полной документации.
