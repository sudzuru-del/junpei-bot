import os
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
HF_API = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"

HEADERS = {}

MEMORY_FILE = "memory.json"

# ---------- память ----------
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

memory = load_memory()

# ---------- локальный характер ----------
def local_brain(text, mood):
    t = text.lower()

    if "софи" in t:
        return "…Софи важна для меня. Я не хочу это обсуждать."

    if any(w in t for w in ["дурак", "ненавижу"]):
        return "…мне страшно… не говори так."

    if any(w in t for w in ["привет", "хай", "hello"]):
        return "…привет…"

    if mood == "shy":
        return "…я не знаю, что сказать…"

    return None

# ---------- бесплатный ИИ ----------
def hf_generate(text):
    try:
        r = requests.post(
            HF_API,
            headers=HEADERS,
            json={"inputs": text},
            timeout=10
        )
        data = r.json()

        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]

    except:
        pass

    return None

# ---------- ответ ----------
def get_reply(text, user_id):
    if user_id not in memory:
        memory[user_id] = {"mood": "neutral"}

    mood = memory[user_id]["mood"]

    # 1. локальный мозг
    local = local_brain(text, mood)
    if local:
        return local

    # 2. бесплатный AI
    ai = hf_generate(text)
    if ai:
        return ai[:300]

    # 3. fallback
    return "…я думаю об этом."

# ---------- обработка ----------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text

    reply = get_reply(text, user_id)

    await update.message.reply_text(reply)

# ---------- запуск ----------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot running...")
app.run_polling()
