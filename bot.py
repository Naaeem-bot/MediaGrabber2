import os
import yt_dlp
import logging
from uuid import uuid4
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

logging.basicConfig(level=logging.INFO)

user_links = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت تحميل الفيديوهات\n"
        "أرسل رابط من YouTube / TikTok / Instagram"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    user_links[update.effective_user.id] = url

    keyboard = [
        [InlineKeyboardButton("🎬 فيديو", callback_data="video")],
        [InlineKeyboardButton("🎧 صوت MP3", callback_data="audio")]
    ]

    await update.message.reply_text(
        "اختر نوع التحميل:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = user_links.get(query.from_user.id)
    if not url:
        await query.message.reply_text("أرسل الرابط أولاً")
        return

    file_id = str(uuid4())

    try:
        if query.data == "video":
            filename = f"{file_id}.mp4"
            ydl_opts = {"format": "best", "outtmpl": filename}
        else:
            filename = f"{file_id}.mp3"
            ydl_opts = {
                "format": "bestaudio",
                "outtmpl": f"{file_id}.%(ext)s",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3"
                }]
            }

        await query.message.reply_text("⏳ جاري التحميل...")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if query.data == "video":
            await query.message.reply_video(video=open(filename, "rb"))
        else:
            await query.message.reply_audio(audio=open(filename, "rb"))

        os.remove(filename)

    except Exception as e:
        logging.error(e)
        await query.message.reply_text("❌ حدث خطأ أثناء التحميل")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
app.add_handler(CallbackQueryHandler(handle_choice))

app.run_polling()
