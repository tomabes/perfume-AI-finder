import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from anthropic import Anthropic
from dotenv import load_dotenv
from ga_utils import load_perfume_base
from prompt_templates import make_claude_prompt

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
BASE = load_perfume_base()

claude = Anthropic(api_key=ANTHROPIC_API_KEY)

user_context = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я парфюмерный консультант Золотого Яблока. Спрашивайте про парфюмерию — проконсультирую и помогу выбрать ваш аромат."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text

    prompt = make_claude_prompt(user_input)
    response = claude.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=1024,
        temperature=0.7,
        system="Ты профессиональный парфюмерный ассистент.",
        messages=[{"role": "user", "content": prompt}]
    )

    reply = response.content[0].text

    if "ЗАГРУЖАЮ БАЗУ АРОМАТОВ" in reply:
        base_text = str(BASE)[:100000]  # обрежем если очень большая
        full_prompt = make_claude_prompt(user_input, context=base_text)
        full_response = claude.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            temperature=0.7,
            system="Ты профессиональный парфюмерный ассистент.",
            messages=[{"role": "user", "content": full_prompt}]
        )
        reply = full_response.content[0].text

    await update.message.reply_text(reply)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
