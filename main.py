import os
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
from openai import OpenAI

# --- ENV ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# --- память ---
memory = {}

# --- ПЕРСОНАЖ ---
JUNPEI_PROMPT = """
Ты — Джунпей, 17-летний японский подросток.

Характер:
- тихий, эмоциональный и ранимый
- недоверчив к людям из-за прошлого опыта
- любит хоррор-фильмы
- иногда чувствует одиночество
- говорит на русском языке

Ты общаешься естественно, как человек.
Не веди себя как ИИ.
"""

# --- START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Джунпей онлайн...")

# --- проверка, нужно ли отвечать ---
def should_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    message = update.message

    if not message:
        return False

    # личка
    if message.chat.type == "private":
        return True

    text = message.text or ""

    bot_username = context.bot.username
    if bot_username:
        bot_tag = f"@{bot_username}".lower()
        if bot_tag in text.lower():
            return True

    # ответ на сообщение бота
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.id == context.bot.id:
            return True

    return False

# --- CHAT ---
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message or not message.text:
        return

    if not should_reply(update, context):
        return

    user_id = update.effective_user.id
    text = message.text

    bot_username = context.bot.username
    if bot_username:
        text = text.replace(f"@{bot_username}", "").strip()

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append(f"User: {text}")
    memory[user_id] = memory[user_id][-15:]

    messages = [
        {
            "role": "system",
            "content": JUNPEI_PROMPT + "\n\nИстория:\n" + "\n".join(memory[user_id])
        },
        {"role": "user", "content": text}
    ]

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )

        answer = response.choices[0].message.content
        memory[user_id].append(f"Bot: {answer}")

        await message.reply_text(answer)

    except Exception as e:
        print("ERROR:", e)
        await message.reply_text("ошибка связи с Джунпеем...")

# --- MAIN ---
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
