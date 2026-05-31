import os
import logging
import yt_dlp
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "8619218353:AAExgO9HKfzeae9UiAy8GHKy7PKRk2-a_38")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Merhaba! Ben Twitter/X video indirici botuyum.\n\n"
        "📎 Bana bir Twitter/X linki gönder, videoyu indirip sana göndereyim!\n\n"
        "Örnek: https://twitter.com/kullanici/status/123456789"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *Nasıl Kullanılır?*\n\n"
        "1. Twitter veya X'ten bir video paylaşımının linkini kopyala\n"
        "2. Bu bota gönder\n"
        "3. Videoyu indirip sana göndereceğim!\n\n"
        "⚠️ Sadece herkese açık (public) hesapların videoları indirilebilir.",
        parse_mode="Markdown"
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # Twitter/X link kontrolü
    if not any(domain in url for domain in ["twitter.com", "x.com", "t.co"]):
        await update.message.reply_text(
            "❌ Bu bir Twitter/X linki değil gibi görünüyor.\n"
            "Lütfen geçerli bir Twitter veya X linki gönder."
        )
        return

    wait_msg = await update.message.reply_text("⏳ Video indiriliyor, lütfen bekle...")

    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': '/tmp/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
            video_title = info.get('title', 'Twitter Videosu')

        # Dosya boyutu kontrolü (Telegram 50MB limiti)
        file_size = os.path.getsize(video_path)
        if file_size > 50 * 1024 * 1024:
            await wait_msg.edit_text("❌ Video çok büyük (50MB üzeri). Telegram bu boyutu kabul etmiyor.")
            os.remove(video_path)
            return

        await wait_msg.edit_text("📤 Video gönderiliyor...")

        with open(video_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=f"🎬 {video_title}\n\n🔗 {url}",
                supports_streaming=True
            )

        await wait_msg.delete()
        os.remove(video_path)

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {e}")
        await wait_msg.edit_text(
            "❌ Video indirilemedi.\n\n"
            "Olası sebepler:\n"
            "• Hesap gizli (private) olabilir\n"
            "• Video silinmiş olabilir\n"
            "• Link hatalı olabilir"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await wait_msg.edit_text("❌ Beklenmedik bir hata oluştu. Lütfen tekrar dene.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    logger.info("Bot başlatılıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()
