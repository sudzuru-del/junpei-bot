import os
import random
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

from openai import OpenAI


# ---------------- KEYS ----------------

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# ---------------- CLIENTS ----------------

deepseek = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

groq = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

openrouter = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)


# ---------------- MEMORY ----------------

memory = {}


# ---------------- PERSONA ----------------

JUNPEI_PROMPT = """
Ты — Джунпей, 17-летний японский подросток.

Характер:
- тихий, ранимый
- недоверчивый
- любит хорроры
- говоришь по-русски
"""


# ---------------- MODEL CALLS ----------------

def ask_deepseek(messages):
    return deepseek.chat.completions.create(
        model="deepseek-chat",
        messages=messages
    ).choices[0].message.content


def ask_groq(messages):
    return groq.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=messages
    ).choices[0].message.content


def ask_openrouter(messages):
    return openrouter.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=messages
    ).choices[0].message.content


# ---------------- ROUTER ----------------

def generate_response(messages):
    providers = [
        ask_deepseek,
        ask_groq,
        ask_openrouter
    ]

    random.shuffle(providers)

    last_error = None

    for provider in providers:
        try:
            return provider(messages)
        except Exception as e:
            last_error = e
            continue

    raise last_error


# ---------------- REPLY RULE ----------------

def should_reply(update: Update, context: CallbackContext):
    msg = update.message

    if msg.chat.type == "private":
        return True

    text = msg.text or ""

    if context.bot.username and f"@{context.bot.username.lower()}" in text.lower():
        return True

    if msg.reply_to_message:
        return True

    return False


# ---------------- HANDLERS ----------------

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Джунпей онлайн...")


def chat(update: Update, context: CallbackContext):
    if not update.message or not update.message.text:
        return

    if not should_reply(update, context):
        return

    user_id = update.effective_user.id
    text = update.message.text

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
        answer = generate_response(messages)
        memory[user_id].append(f"Bot: {answer}")
        update.message.reply_text(answer)

    except Exception:
        update.message.reply_text("Джунпей сейчас молчит...")


# ---------------- RUN ----------------

def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, chat))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
