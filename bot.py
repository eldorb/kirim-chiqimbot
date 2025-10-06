import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import pandas as pd
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from apscheduler.schedulers.background import BackgroundScheduler

# --- Config ---
BOT_TOKEN = "8096023469:AAGSeVbCR_OuIDwW3a4Ikzd0fu0qmgCwbOI"
OWNER_ID = 553899950   # faqat siz uchun

DATA_FILE = "data.csv"
LIMIT_FILE = "limit.txt"

logging.basicConfig(level=logging.INFO)

# --- Yordamchi funksiyalar ---
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["datetime", "type", "amount", "category", "note"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def categorize(note):
    note = note.lower()
    if any(w in note for w in ["osh", "kafe", "kofe", "ovqat"]):
        return "Ovqat"
    if any(w in note for w in ["benzin", "avtobus", "taksi", "yoqilg'i"]):
        return "Transport"
    if any(w in note for w in ["internet", "telefon", "telegram"]):
        return "Aloqa"
    if any(w in note for w in ["oylik", "maosh", "daromad", "ish"]):
        return "Daromad"
    return "Boshqa"

def add_record(amount, note, record_type):
    df = load_data()
    category = categorize(note)
    new_row = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "type": record_type,
        "amount": amount,
        "category": category,
        "note": note
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)

# --- Handlers ---
async def start(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text(
        "Salom! Bu bot faqat siz uchun ishlaydi.\n"
        "➕ Kirim uchun: +5000000 oylik tushdi\n"
        "➖ Chiqim uchun: -20000 kofe\n\n"
        "Buyruqlar:\n"
        "/today - bugungi hisob\n"
        "/7days - oxirgi 7 kun\n"
        "/month - joriy oy\n"
        "/3months - oxirgi 3 oy\n"
        "/balance - umumiy balans\n"
        "/export - Excel fayl\n"
        "/chart - grafik\n"
        "/limit 5000000 - limit qo'yish\n"
        "/top - eng katta 3 chiqim"
    )

async def add_entry(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        return

    text = update.message.text.strip()
    if text.startswith("+"):
        try:
            parts = text.split(" ", 1)
            amount = int(parts[0].replace("+", ""))
            note = parts[1] if len(parts) > 1 else "Kirim"
            add_record(amount, note, "Kirim")
            await update.message.reply_text(f"✅ {amount:,} so‘m kirim yozildi: {note}")
        except:
            await update.message.reply_text("❌ Format xato. Misol: +5000000 oylik tushdi")

    elif text.startswith("-"):
        try:
            parts = text.split(" ", 1)
            amount = int(parts[0].replace("-", ""))
            note = parts[1] if len(parts) > 1 else "Chiqim"
            add_record(-amount, note, "Chiqim")
            await update.message.reply_text(f"✅ {amount:,} so‘m chiqim yozildi: {note}")
        except:
            await update.message.reply_text("❌ Format xato. Misol: -20000 kofe")

    else:
        # avtomatik aniqlash
        words = text.split(" ")
        nums = [int("".join(filter(str.isdigit, w))) for w in words if any(ch.isdigit() for ch in w)]
        if nums:
            amount = nums[0]
            note = text
            if "oldim" in text or "sotib" in text or "chiqdim" in text:
                add_record(-amount, note, "Chiqim")
                await update.message.reply_text(f"✅ {amount:,} so‘m chiqim yozildi: {note}")
            else:
                add_record(amount, note, "Kirim")
                await update.message.reply_text(f"✅ {amount:,} so‘m kirim yozildi: {note}")
        else:
            await update.message.reply_text("❌ Formatni to‘g‘ri yozing.")

def filter_data(days=None, months=None):
    df = load_data()
    if df.empty:
        return pd.DataFrame()
    df["datetime"] = pd.to_datetime(df["datetime"])
    if days:
        since = datetime.now() - timedelta(days=days)
        return df[df["datetime"] >= since]
    if months:
        since = datetime.now() - timedelta(days=30*months)
        return df[df["datetime"] >= since]
    return df

async def report(update: Update, context: CallbackContext, df, title):
    if df.empty:
        await update.message.reply_text("Ma'lumot yo‘q.")
        return
    kirim = df[df["type"] == "Kirim"]["amount"].sum()
    chiqim = df[df["type"] == "Chiqim"]["amount"].sum()
    balance = kirim + chiqim
    await update.message.reply_text(
        f"📊 {title}\n"
        f"➕ Kirim: {kirim:,}\n"
        f"➖ Chiqim: {abs(chiqim):,}\n"
        f"💰 Balans: {balance:,}"
    )

async def today(update: Update, context: CallbackContext):
    df = load_data()
    if df.empty:
        await update.message.reply_text("Bugun yozuv yo‘q.")
        return
    df["datetime"] = pd.to_datetime(df["datetime"])
    today_data = df[df["datetime"].dt.date == datetime.now().date()]
    await report(update, context, today_data, "Bugungi hisob")

async def seven_days(update: Update, context: CallbackContext):
    df = filter_data(days=7)
    await report(update, context, df, "Oxirgi 7 kun")

async def month(update: Update, context: CallbackContext):
    df = filter_data(months=1)
    await report(update, context, df, "Joriy oy")

async def three_months(update: Update, context: CallbackContext):
    df = filter_data(months=3)
    await report(update, context, df, "Oxirgi 3 oy")

async def balance(update: Update, context: CallbackContext):
    df = load_data()
    if df.empty:
        await update.message.reply_text("Ma'lumot yo‘q.")
        return
    kirim = df[df["type"] == "Kirim"]["amount"].sum()
    chiqim = df[df["type"] == "Chiqim"]["amount"].sum()
    balance = kirim + chiqim
    await update.message.reply_text(
        f"💰 Umumiy balans:\n"
        f"Kirim: {kirim:,}\n"
        f"Chiqim: {abs(chiqim):,}\n"
        f"Balans: {balance:,}"
    )

async def export(update: Update, context: CallbackContext):
    df = load_data()
    if df.empty:
        await update.message.reply_text("Ma'lumot yo‘q.")
        return
    file_name = "hisobot.xlsx"
    df.to_excel(file_name, index=False)
    await update.message.reply_document(document=open(file_name, "rb"))

async def chart(update: Update, context: CallbackContext):
    df = load_data()
    if df.empty:
        await update.message.reply_text("Ma'lumot yo‘q.")
        return
    # Pie chart by category
    cat_sum = df.groupby("category")["amount"].sum()
    plt.figure(figsize=(5,5))
    cat_sum.plot.pie(autopct='%1.1f%%')
    plt.ylabel("")
    plt.title("Kategoriya bo‘yicha chiqim")
    plt.savefig("chart.png")
    plt.close()
    await update.message.reply_photo(photo=open("chart.png", "rb"))

async def set_limit(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("❌ Limitni kiriting. Masalan: /limit 5000000")
        return
    try:
        limit = int(context.args[0])
        with open(LIMIT_FILE, "w") as f:
            f.write(str(limit))
        await update.message.reply_text(f"✅ Limit {limit:,} so‘m qilib belgilandi.")
    except:
        await update.message.reply_text("❌ Limit xato kiritildi.")

async def top_expenses(update: Update, context: CallbackContext):
    df = load_data()
    if df.empty:
        await update.message.reply_text("Ma'lumot yo‘q.")
        return
    chiqimlar = df[df["type"] == "Chiqim"].sort_values(by="amount")
    top3 = chiqimlar.head(3)
    msg = "🔥 Eng katta 3 chiqim:\n"
    for i, row in enumerate(top3.itertuples(), 1):
        msg += f"{i}. {abs(row.amount):,} so‘m – {row.note}\n"
    await update.message.reply_text(msg)

# --- Scheduler ---
def reminder_job(app: Application):
    async def send_reminder():
        await app.bot.send_message(chat_id=OWNER_ID, text="⏰ Bugungi kirim-chiqimlarni yozishni unutmang!")
    return send_reminder

# --- Main ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_entry))

    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("7days", seven_days))
    app.add_handler(CommandHandler("month", month))
    app.add_handler(CommandHandler("3months", three_months))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(CommandHandler("chart", chart))
    app.add_handler(CommandHandler("limit", set_limit))
    app.add_handler(CommandHandler("top", top_expenses))

    # Scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(reminder_job(app), "cron", hour=21, minute=0)
    scheduler.start()

    app.run_polling()

if __name__ == "__main__":
    main()
