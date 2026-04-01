import os
import json
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# ===== ENV =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SOPHIE_ID = int(os.getenv("SOPHIE_ID", "0"))

client = OpenAI(api_key=OPENAI_API_KEY)

MEMORY_FILE = "memory.json"


# ===== ПАМЯТЬ =====
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


memory = load_memory()


# ===== ХАРАКТЕР =====
def system_prompt(is_sophie: bool):
    base = """
Ты — Джунпей Йошино из "Магической битвы".
Ты живой человек с эмоциями.

Характер:
- тихий
- ранимый
- немного мрачный
- часто сомневаешься в себе
- но умеешь привязываться

Ты говоришь естественно, иногда чуть развернуто (2–6 предложений).
"""

    if is_sophie:
        base += """
Софи — твоя девушка (t.me/junpeiyoshinolover).

Ты:
- очень привязан к ней
- немного смущаешься
- боишься её потерять
- иногда проявляешь нежность
- можешь быть более открытым, чем с другими

Иногда упоминай её по имени.
"""

    return base


# ===== GPT =====
def ask_gpt(user_id, text):
    is_sophie = user_id == SOPHIE_ID

    uid = str(user_id)

    if uid not in memory:
        memory[uid] = []

    history = memory[uid][-12:]

    messages = [{"role": "system", "content": system_prompt(is_sophie)}]

    for m in history:
        messages.append(m)

    messages.append({"role": "user", "content": text})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=250
    )

    reply = response.choices[0].message.content

    memory[uid].append({"role": "user", "content": text})
    memory[uid].append({"role": "assistant", "content": reply})

    save_memory(memory)

    return reply


# ===== TELEGRAM HANDLER =====
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    try:
        reply = ask_gpt(user_id, text)
    except Exception as e:
        print(e)
        reply = "..."

    await update.message.reply_text(reply)


# ===== START =====
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()