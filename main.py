import os
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler
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

# --- персонаж ---
JUNPEI_PROMPT = """
Ты — Джунпей, 17-летний японский подросток.

Характер:
- тихий, эмоциональный и ранимый
- не доверяет людям
- любит хоррор
- говорит на русском

Отвечай как живой человек.
"""

# --- команды ---
def start(update, context):
    update.message.reply_text("...я здесь")

# --- проверка для групп ---
def should_reply(update, context):
    chat_type = update.message.chat.type
    text = update.message.text or ""

    # личка
    if chat_type == "private":
        return True

    # упоминание
    if context.bot.username.lower() in text.lower():
        return True

    # ответ на бота
    if update.message.reply_to_message:
        if update.message.reply_to_message.from_user.id == context.bot.id:
            return True

    return False

# --- чат ---
def chat(update, context):
    if not update.message or not update.message.text:
        return

    if not should_reply(update, context):
        return

    user_id = update.message.from_user.id
    text = update.message.text

    if context.bot.username:
        text = text.replace(context.bot.username, "").strip()

    if user_id not in memory:
        memory[user_id] = []

    memory[user_id].append(f"User: {text}")
    memory[user_id] = memory[user_id][-10:]

    messages = [
        {"role": "system", "content": JUNPEI_PROMPT + "\n" + "\n".join(memory[user_id])},
        {"role": "user", "content": text}
    ]

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )

        answer = response.choices[0].message.content
        memory[user_id].append(f"Bot: {answer}")

        update.message.reply_text(answer)

    except Exception as e:
        print(e)
        update.message.reply_text("...не получилось ответить")

# --- запуск ---
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, chat))

    print("Bot started...")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
