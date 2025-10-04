import logging
import os
import re
import pandas as pd
from datetime import datetime, timedelta
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# TOKENNI shu yerga qo'ying
TOKEN = "8096023469:AAGSeVbCR_OuIDwW3a4Ikzd0fu0qmgCwbOI"
FILE_NAME = "expenses.xlsx"

# Log sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Excel faylni tayyorlab qo'yish
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["date", "amount", "description", "type"])
    df.to_excel(FILE_NAME, index=False)

def add_record(amount, description, typ):
    df = pd.read_excel(FILE_NAME)
    new_row = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "amount": amount,
        "description": description,
        "type": typ
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(FILE_NAME, index=False)

def get_summary(days=None, months=None):
    df = pd.read_excel(FILE_NAME)
    if df.empty:
        return "Hali hech narsa kiritilmagan."

    df["date"] = pd.to_datetime(df["date"])
    now = datetime.now()

    if days:
        start = now - timedelta(days=days)
        df = df[df["date"] >= start]
    if months:
        start = now - timedelta(days=months * 30)
        df = df[df["date"] >= start]

    if df.empty:
        return "Ko‘rsatilgan davr uchun yozuv yo‘q."

    total_income = df[df["type"] == "income"]["amount"].sum()
    total_expense = df[df["type"] == "expense"]["amount"].sum()
    balance = total_income - total_expense

    return (f"📊 Hisobot:\n"
            f"Kirim: {total_income:,} so‘m\n"
            f"Chiqim: {total_expense:,} so‘m\n"
            f"Qoldiq: {balance:,} so‘m")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = ("Salom! Bu bot kirim va chiqimlaringizni hisoblab boradi.\n"
            "👉 Kirim uchun: +5000000 oylik tushdi\n"
            "👉 Chiqim uchun: -20000 kofe\n\n"
            "Buyruqlar:\n"
            "/3days - oxirgi 3 kun\n"
            "/7days - oxirgi 7 kun\n"
            "/10days - oxirgi 10 kun\n"
            "/month - joriy oy\n"
            "/3months - oxirgi 3 oy\n"
            "/export - Excel faylni yuklab olish")
    await update.message.reply_text(text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    match = re.match(r"^([+-])\s*(\d+)\s*(.*)", text)

    if not match:
        await update.message.reply_text("❌ Format noto‘g‘ri. Misol: +5000000 oylik tushdi yoki -20000 kofe")
        return

    sign, amount, desc = match.groups()
    amount = int(amount)
    if sign == "+":
        add_record(amount, desc, "income")
        await update.message.reply_text(f"✅ {amount:,} so‘m kirim yozildi: {desc}")
    else:
        add_record(amount, desc, "expense")
        await update.message.reply_text(f"✅ {amount:,} so‘m chiqim yozildi: {desc}")

async def summary_3days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_summary(days=3))

async def summary_7days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_summary(days=7))

async def summary_10days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_summary(days=10))

async def summary_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_summary(months=1))

async def summary_3months(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_summary(months=3))

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(FILE_NAME):
        await update.message.reply_text("Fayl topilmadi.")
        return
    await update.message.reply_document(InputFile(FILE_NAME))

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("3days", summary_3days))
    app.add_handler(CommandHandler("7days", summary_7days))
    app.add_handler(CommandHandler("10days", summary_10days))
    app.add_handler(CommandHandler("month", summary_month))
    app.add_handler(CommandHandler("3months", summary_3months))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
