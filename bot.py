**bot.py**

```python
import logging
import re
import pandas as pd
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# === CONFIGURATION ===
BOT_TOKEN = "8096023469:AAGSeVbCR_OuIDwW3a4Ikzd0fu0qmgCwbOI"
OWNER_ID = 553899950
FILENAME = "data.xlsx"

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === HELPER FUNCTIONS ===
def parse_amount(text):
    text = text.lower().replace(",", ".").replace(" ", "")
    amount = 0
    match = re.search(r"([\d\.]+)", text)
    if match:
        amount = float(match.group(1))
        if "mln" in text or "million" in text:
            amount *= 1_000_000
        elif "ming" in text:
            amount *= 1_000
    return int(amount)

def read_data():
    try:
        return pd.read_excel(FILENAME)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Sana", "Turi", "Miqdor", "Izoh"])

def save_data(df):
    df.to_excel(FILENAME, index=False)

def add_record(turi, amount, comment):
    df = read_data()
    sana = datetime.now().strftime("%Y-%m-%d %H:%M")
    df.loc[len(df)] = [sana, turi, amount, comment]
    save_data(df)

def get_summary(days):
    df = read_data()
    if df.empty:
        return "📭 Ma'lumot yo‘q"
    start = datetime.now() - timedelta(days=days)
    df["Sana_dt"] = pd.to_datetime(df["Sana"])
    df = df[df["Sana_dt"] >= start]
    if df.empty:
        return "📭 Bu davrda ma'lumot yo‘q"
    kirim = df[df["Turi"] == "kirim"]["Miqdor"].sum()
    chiqim = df[df["Turi"] == "chiqim"]["Miqdor"].sum()
    balance = kirim - chiqim
    return f"📊 Oxirgi {days} kun:\n➕ Kirim: {kirim:,}\n➖ Chiqim: {chiqim:,}\n💰 Balans: {balance:,}"

def get_keyboard():
    buttons = [
        [InlineKeyboardButton("📅 Bugun", callback_data="1")],
        [InlineKeyboardButton("📆 3 kun", callback_data="3"),
         InlineKeyboardButton("🗓 7 kun", callback_data="7")],
        [InlineKeyboardButton("🗂 10 kun", callback_data="10"),
         InlineKeyboardButton("📈 Oy", callback_data="30")],
        [InlineKeyboardButton("📊 3 oy", callback_data="90"),
         InlineKeyboardButton("📤 Excel", callback_data="export")]
    ]
    return InlineKeyboardMarkup(buttons)

# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Siz bu botdan foydalana olmaysiz.")
    await update.message.reply_text(
        "👋 Salom! Bu bot kirim va chiqimlaringizni hisoblab boradi.\n"
        "Masalan:\n👉 2 mln ish oldim\n👉 10 ming kofe ichdim\n",
        reply_markup=get_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("❌ Siz bu botdan foydalana olmaysiz.")
    text = update.message.text.lower()
    amount = parse_amount(text)
    if amount == 0:
        return await update.message.reply_text("❌ Summani aniqlay olmadim. Masalan: 10 ming kofe yoki 2 mln topdim")
    if any(k in text for k in ["ish", "top", "oldim", "tushdi", "keldi", "berdi"]) and not "-" in text:
        turi = "kirim"
    else:
        turi = "chiqim"
    add_record(turi, amount, text)
    await update.message.reply_text(
        f"✅ {amount:,} so‘m {'kirim' if turi=='kirim' else 'chiqim'} yozildi: {text}",
        reply_markup=get_keyboard()
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "export":
        await query.edit_message_text("⏳ Fayl tayyorlanmoqda...")
        df = read_data()
        df.to_excel(FILENAME, index=False)
        await query.message.reply_document(open(FILENAME, "rb"))
        return
    days = int(data)
    summary = get_summary(days)
    await query.edit_message_text(summary, reply_markup=get_keyboard())

# === MAIN ===
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(MessageHandler(filters.COMMAND, start))
    app.add_handler(CommandHandler("summary", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.add_handler(CommandHandler("export", start))
    app.add_handler(MessageHandler(filters.StatusUpdate, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(CommandHandler("stats", start))
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.add_handler(MessageHandler(filters.UpdateType, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
