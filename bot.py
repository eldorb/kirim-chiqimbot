# bot.py — Yangilangan: Excel export BytesIO bilan, diagnostika komandalar, va 'ming' / 'mln' qo'llab-quvvatlash
import logging
import os
import re
from io import BytesIO
from datetime import datetime, timedelta

import pandas as pd
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ---------- SOZLAMALAR ----------
# TOKENni Railway Variables -> KEY: TOKEN qilib qo'ying
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN muhit o'zgaruvchisi aniqlanmadi. Railway yoki lokalda TOKEN o'rnatishingiz kerak.")

# Excel fayl nomlarini tekshirish (avvalgi nomlarni ham qamrab oladi)
POSSIBLE_FILES = ["expenses.xlsx", "finance.xlsx", "data.xlsx", "hisobot.xlsx"]
DEFAULT_FILE = "expenses.xlsx"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def get_file_name():
    for f in POSSIBLE_FILES:
        if os.path.exists(f):
            return f
    return DEFAULT_FILE


def init_excel():
    fname = get_file_name()
    if not os.path.exists(fname):
        df = pd.DataFrame(columns=["date", "amount", "description", "type"])
        df.to_excel(fname, index=False)
        logger.info("Yangi Excel fayl yaratildi: %s", fname)
    else:
        logger.info("Mavjud Excel fayl topildi: %s", fname)


def add_record(amount: int, description: str, typ: str):
    fname = get_file_name()
    try:
        df = pd.read_excel(fname)
    except Exception:
        df = pd.DataFrame(columns=["date", "amount", "description", "type"])

    new_row = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "amount": int(amount),
        "description": description,
        "type": typ,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_excel(fname, index=False)
    logger.info("Record qo'shildi: %s -> %s (%s) fayl: %s", typ, amount, description, fname)


def get_summary(days=None, months=None):
    fname = get_file_name()
    try:
        df = pd.read_excel(fname)
    except Exception:
        return None, None, None, fname

    if df.empty:
        return 0, 0, 0, fname

    df["date"] = pd.to_datetime(df["date"])
    now = datetime.now()

    if days is not None:
        start = now - timedelta(days=days)
        df = df[df["date"] >= start]
    if months is not None:
        start = now - timedelta(days=months * 30)
        df = df[df["date"] >= start]

    if df.empty:
        return 0, 0, 0, fname

    # to'g'ri tip va summalash
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    total_income = int(df[df["type"] == "income"]["amount"].sum())
    total_expense = int(df[df["type"] == "expense"]["amount"].sum())
    balance = total_income - total_expense
    return total_income, total_expense, balance, fname


# ---------- BOT HANDLERLARI ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Bu bot kirim va chiqimlaringizni hisoblab boradi.\n\n"
        "👉 Kirim uchun: +5000000 oylik tushdi  (yoki +5000 mln kabi)\n"
        "👉 Chiqim uchun: -20000 kofe  yoki 8 minga salfetka oldim (belgisiz yozsangiz CHIQIM deb olinadi)\n\n"
        "Buyruqlar:\n"
        "/3days - oxirgi 3 kun\n"
        "/7days - oxirgi 7 kun\n"
        "/10days - oxirgi 10 kun\n"
        "/month - joriy oy\n"
        "/3months - oxirgi 3 oy\n"
        "/export - Excel faylni yuklab olish\n"
        "/count - mavjud yozuvlar soni va ishlatilayotgan fayl"
    )


def parse_amount_and_type(text: str):
    """
    Qabul qilingan textdan raqam va izohni chiqaradi.
    Qo'llab-quvvatlanadi: +, - belgilar, ming/ minga / mln / million so'zlari.
    Agar belgi ko'rsatilmasa => default: chiqim.
    """
    orig = text.strip()
    # ruxsat beramiz: optional sign, then number (digits, spaces, commas, dots), then rest
    m = re.match(r"^\s*([+-])?\s*([\d\.,\s]+)\s*(.*)$", orig)
    if not m:
        return None  # noto'g'ri format

    sign, amount_part, rest = m.groups()
    # tozalash: faqat raqamlarni olish
    digits = re.sub(r"[^\d]", "", amount_part)
    if digits == "":
        return None

    amount = int(digits)
    rest = rest.strip() if rest else ""

    # multiplier orqali 'ming' yoki 'mln' so'zlarini aniqlaymiz (matnning istalgan joyida)
    low = orig.lower()
    multiplier = 1
    if re.search(r"\b(minga|ming)\b", low):
        multiplier = 1000
        # agar rest boshida 'minga' bo'lsa, o'chirish
        rest = re.sub(r"^\s*(minga|ming)\b\s*", "", rest, flags=re.I)
    if re.search(r"\b(mln|million|milyon|миллион)\b", low):
        multiplier = 1_000_000

    amount = amount * multiplier

    if sign == "+":
        typ = "income"
    elif sign == "-":
        typ = "expense"
    else:
        # agar belgisi ko'rsatilmagan bo'lsa, default — chiqim (siz xohlasangiz bu o'zgartirilishi mumkin)
        typ = "expense"

    return amount, rest, typ


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    parsed = parse_amount_and_type(text)
    if not parsed:
        await update.message.reply_text("❌ Format noto‘g‘ri. Misol: +5000000 oylik yoki -20000 kofe yoki 8 minga salfetka")
        return

    amount, desc, typ = parsed
    add_record(amount, desc, typ)
    typ_text = "KIRIM" if typ == "income" else "CHIQIM"
    await update.message.reply_text(f"✅ {amount:,} so‘m {typ_text} yozildi: {desc}")


# Summary commands
async def cmd_3days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    i, e, b, fname = get_summary(days=3)
    await update.message.reply_text(f"📊 Oxirgi 3 kun\nKirim: {i:,}\nChiqim: {e:,}\nBalans: {b:,}\nFayl: {fname}")


async def cmd_7days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    i, e, b, fname = get_summary(days=7)
    await update.message.reply_text(f"📊 Oxirgi 7 kun\nKirim: {i:,}\nChiqim: {e:,}\nBalans: {b:,}\nFayl: {fname}")


async def cmd_10days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    i, e, b, fname = get_summary(days=10)
    await update.message.reply_text(f"📊 Oxirgi 10 kun\nKirim: {i:,}\nChiqim: {e:,}\nBalans: {b:,}\nFayl: {fname}")


async def cmd_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    i, e, b, fname = get_summary(months=1)
    await update.message.reply_text(f"📊 Oxirgi 1 oy\nKirim: {i:,}\nChiqim: {e:,}\nBalans: {b:,}\nFayl: {fname}")


async def cmd_3months(update: Update, context: ContextTypes.DEFAULT_TYPE):
    i, e, b, fname = get_summary(months=3)
    await update.message.reply_text(f"📊 Oxirgi 3 oy\nKirim: {i:,}\nChiqim: {e:,}\nBalans: {b:,}\nFayl: {fname}")


# Excel eksport — BytesIO bilan to'g'ri nom bilan yuboradi
async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fname = get_file_name()
    try:
        df = pd.read_excel(fname)
    except Exception:
        await update.message.reply_text("📂 Excel fayl ochilmadi yoki mavjud emas.")
        return

    if df.empty:
        await update.message.reply_text("📂 Ma'lumot topilmadi — hali hech narsa yozilmagan.")
        return

    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    await update.message.reply_document(InputFile(output, filename="hisobot.xlsx"), caption="📊 Sizning hisobot faylingiz")


# Diagnostika komandasi
async def cmd_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fname = get_file_name()
    try:
        df = pd.read_excel(fname)
        n = len(df)
    except Exception:
        n = 0
    await update.message.reply_text(f"Fayl: {fname}\nYozuvlar soni: {n}")


# Main
def main():
    init_excel()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("3days", cmd_3days))
    app.add_handler(CommandHandler("7days", cmd_7days))
    app.add_handler(CommandHandler("10days", cmd_10days))
    app.add_handler(CommandHandler("month", cmd_month))
    app.add_handler(CommandHandler("3months", cmd_3months))
    app.add_handler(CommandHandler("export", cmd_export))
    app.add_handler(CommandHandler("count", cmd_count))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot ishga tushmoqda...")
    app.run_polling()


if __name__ == "__main__":
    main()
