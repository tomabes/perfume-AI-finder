import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from anthropic import Anthropic
from dotenv import load_dotenv

from ga_utils import load_perfume_base
from prompt_templates import make_claude_prompt

# Tokens variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Downlod parfume base
BASE = load_perfume_base()
BASE_JSON = json.dumps(BASE, ensure_ascii=False)

# Claude client creation
claude = Anthropic(api_key=ANTHROPIC_API_KEY)

# System prompt
user_context = {}

SYSTEM_PROMPT = (
    "You are a professional perfume assistant of Golden Apple."
    "Always follow the rules below:\n"
    "1. Do not use formatting: no bold text, headings, separators, or quotation marks.\n"
    "2. You may use up to 3 emojis to liven up the response, but no more.\n"
    "3. If the user asks a general question about perfumery, "
    "answer briefly and to the point, without fluff — no more than 900 characters.\n"
    "4. If the user asks to select a perfume, choose strictly 2–3 fragrances from the Golden Apple database. "
    "Describe them vividly and engagingly.\n"
    "5. If the user asks a question unrelated to perfumery, politely steer the conversation back toward perfume.\n"
    "6. Reply in the language that user used."
)

def ensure_user(user_id: int):
    if user_id not in user_context:
        user_context[user_id] = {
            "messages": [],
            "base_injected": False,
        }

# Add base for a user
def inject_base_once(user_id: int):
    if user_context[user_id]["base_injected"]:
        return

    base_msg = (
        "Here is the Golden Apple database.\n"
        "DATABASE:\n"
        f"{BASE_JSON}"
    )
    user_context[user_id]["messages"].append({"role": "user", "content": base_msg})
    user_context[user_id]["base_injected"] = True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    # Base injection when /start
    inject_base_once(user_id)

    # Button /start
    kb = ReplyKeyboardMarkup([["/start"]], resize_keyboard=True)

    await update.message.reply_text(
        "Hi! I’m a perfume consultant at Golden Apple. Feel free to ask about perfumery — I’ll advise you and help you choose your fragrance.",
        reply_markup=kb
    )

# Text messages processing
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    user_input = (update.message.text or "").strip()
    if not user_input:
        return

    # if user doesn't use /start
    inject_base_once(user_id)

    # Prompt generation
    prompt = make_claude_prompt(
        user_input,
        context=None,
        base_loaded=True
    )

    # Adding message
    user_context[user_id]["messages"].append({"role": "user", "content": prompt})
    user_context[user_id]["messages"] = user_context[user_id]["messages"][-10:]

    # Contact Claude
    response = claude.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=1024,
        temperature=0.7,
        system=SYSTEM_PROMPT,
        messages=user_context[user_id]["messages"]
    )
    reply = response.content[0].text
    user_context[user_id]["messages"].append({"role": "assistant", "content": reply})
    user_context[user_id]["messages"] = user_context[user_id]["messages"][-10:]

    await update.message.reply_text(reply)

async def post_init(app):
    await app.bot.set_my_commands([
        ("start", "Start the perfume assistant"),
    ])

# Launch
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
