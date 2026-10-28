"""Bot de Telegram: recibe mensajes del propietario y responde."""

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from finance_bot.config import Settings

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hola. Envíame un movimiento, por ejemplo: Gasté $19.000 en almuerzo.")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder hasta la Etapa 5 (interpretación con IA).
    await update.message.reply_text(f"Recibido: {update.message.text}")


def owner_filter(settings: Settings) -> filters.BaseFilter:
    # Descarta antes de llegar a los handlers cualquier remitente que no sea el propietario.
    return filters.User(user_id=settings.telegram_owner_id)


def build_application(settings: Settings) -> Application:
    owner = owner_filter(settings)

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start, filters=owner))
    application.add_handler(MessageHandler(owner & filters.TEXT & ~filters.COMMAND, echo))
    return application
