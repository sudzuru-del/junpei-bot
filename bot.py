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

# --- старт ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Джунпей онлайн...")

# --- проверка: нужно ли отвечать в группе ---
def should_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # личка → всегда отвечаем
    if message.chat.type == "private":
        return True

    text = message.text or ""

    # если упомянули бота (@botname)
    if context.bot.username and f"@{context.bot.username.lower()}" in text.lower():
        return True

    # если ответили на сообщение бота
    if message.reply_to_message:
        return True

    return False


# --- чат ---
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    if not should_reply(update, context):
        return

    user_id = update.effective_user.id
    text = update.message.text

    # убираем упоминание бота из текста
    if context.bot.username:
        text = text.replace(f"@{context.bot.username}", "").strip()

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

        await update.message.reply_text(answer)

    except Exception as e:
        await update.message.reply_text("ошибка связи с Джунпеем...")


# --- запуск ---
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    app.run_polling()


if __name__ == "__main__":
    main()
