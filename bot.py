import os
import json
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

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

# ---------- эмоции ----------
def update_mood(user, mood_change):
    if user not in memory:
        memory[user] = {"mood": "neutral", "trust": 0}

    moods = ["scared", "sad", "neutral", "shy", "calm"]

    current = memory[user]["mood"]
    trust = memory[user]["trust"]

    # простая логика смены эмоций
    if mood_change == "bad":
        trust -= 1
    elif mood_change == "good":
        trust += 1

    if trust < -3:
        memory[user]["mood"] = "scared"
    elif trust < 0:
        memory[user]["mood"] = "sad"
    elif trust < 3:
        memory[user]["mood"] = "neutral"
    else:
        memory[user]["mood"] = "shy"

    memory[user]["trust"] = trust

# ---------- мозг персонажа ----------
def brain(text, user):
    t = text.lower()

    if user not in memory:
        memory[user] = {"mood": "neutral", "trust": 0}

    mood = memory[user]["mood"]

    # ---------- СОФИ ----------
    if "софи" in t:
        update_mood(user, "neutral")
        return "…Софи… я не хочу об этом много говорить."

    # ---------- ПРИВЕТ ----------
    if any(w in t for w in ["привет", "хай", "hello", "здарова"]):
        update_mood(user, "good")
        return random.choice([
            "…привет.",
            "…ты снова здесь.",
            "…я слушаю."
        ])

    # ---------- ЖЁСТКИЕ ОСКОРБЛЕНИЯ ----------
    if any(w in t for w in ["скотина", "мразь", "тварь", "урод", "нелюдь"]):
        update_mood(user, "bad")
        return random.choice([
            "…почему ты так говоришь?..",
            "…мне страшно.",
            "…не надо так."
        ])

    # ---------- ЛЁГКИЕ ОСКОРБЛЕНИЯ ----------
    if any(w in t for w in ["дурак", "тупой", "идиот", "глупый"]):
        update_mood(user, "bad")
        return random.choice([
            "…я не хотел ничего плохого.",
            "…это обидно.",
            "…пожалуйста не говори так."
        ])

    # ---------- АГРЕССИЯ ----------
    if any(w in t for w in ["ненавижу", "заткнись", "отстань", "убью"]):
        update_mood(user, "bad")
        return "…я лучше замолчу."

    # ---------- ЛАСКА ----------
    if any(w in t for w in ["люблю", "нравишься", "молодец", "хороший"]):
        update_mood(user, "good")
        return random.choice([
            "…мне приятно.",
            "…спасибо…",
            "…это неожиданно."
        ])

    # ---------- СТРАХ ----------
    if any(w in t for w in ["страшно", "боюсь", "тревожно"]):
        return "…я рядом."

    # ---------- СТЫД ----------
    if any(w in t for w in ["прости", "извини", "виноват"]):
        return "…ничего."

    # ---------- ДЕФОЛТ ----------
    if mood == "scared":
        return "…не говори со мной так…"
    if mood == "shy":
        return "…я не знаю, что сказать…"

    return random.choice([
        "…я слушаю.",
        "…понял.",
        "…хорошо."
    ])

# ---------- текст ----------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = str(update.message.from_user.id)
    text = update.message.text

    reply = brain(text, user)

    save_memory(memory)
    await update.message.reply_text(reply)

# ---------- запуск ----------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("Bot running...")
app.run_polling()
