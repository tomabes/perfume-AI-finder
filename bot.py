import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from anthropic import Anthropic
from dotenv import load_dotenv

from ga_utils import load_perfume_base
from prompt_templates import make_claude_prompt

# Загрузка переменных окружения
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Загрузка базы парфюмов
BASE = load_perfume_base()

# Создание клиента Claude
claude = Anthropic(api_key=ANTHROPIC_API_KEY)

# Контекст пользователей
user_context = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я парфюмерный консультант Золотого Яблока. Спрашивайте про парфюмерию — проконсультирую и помогу выбрать ваш аромат."
    )

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text.strip()

    # Инициализация контекста
    if user_id not in user_context:
        user_context[user_id] = {
            "messages": [],
            "base_loaded": False
        }

    base_loaded = user_context[user_id]["base_loaded"]

    # Генерация промпта с учётом статуса
    prompt = make_claude_prompt(
        user_input,
        context=str(BASE)[:100000] if base_loaded else None,
        base_loaded=base_loaded
    )

    # Добавление запроса
    user_context[user_id]["messages"].append({"role": "user", "content": prompt})
    user_context[user_id]["messages"] = user_context[user_id]["messages"][-10:]

    # Отправка Claude
    response = claude.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=1024,
        temperature=0.7,
        system="Ты профессиональный парфюмерный ассистент.",
        messages=user_context[user_id]["messages"]
    )
    reply = response.content[0].text
    user_context[user_id]["messages"].append({"role": "assistant", "content": reply})
    user_context[user_id]["messages"] = user_context[user_id]["messages"][-10:]

    # Проверка на запрос базы
    if "ЗАГРУЖАЮ БАЗУ АРОМАТОВ" in reply:
        user_context[user_id]["base_loaded"] = True  # 💡 вот здесь флаг
        base_prompt = make_claude_prompt(
            user_input,
            context=str(BASE)[:100000],
            base_loaded=True
        )
        user_context[user_id]["messages"].append({"role": "user", "content": base_prompt})
        user_context[user_id]["messages"] = user_context[user_id]["messages"][-10:]

        full_response = claude.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1024,
            temperature=0.7,
            system="Ты профессиональный парфюмерный ассистент.",
            messages=user_context[user_id]["messages"]
        )
        reply = full_response.content[0].text
        user_context[user_id]["messages"].append({"role": "assistant", "content": reply})
        user_context[user_id]["messages"] = user_context[user_id]["messages"][-10:]

    await update.message.reply_text(reply)

# Запуск
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
