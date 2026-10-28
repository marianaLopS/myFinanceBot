"""Bot de Telegram: recibe mensajes del propietario y responde."""

import asyncio
import logging

import gspread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from finance_bot.config import Settings
from finance_bot.sheets import append_row, build_test_row

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hola. Envíame un movimiento, por ejemplo: Gasté $19.000 en almuerzo.")


async def prueba(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Escribe una fila fija de prueba. Solo confirma si Sheets respondió sin error.
    worksheet = context.bot_data["worksheet"]
    try:
        await asyncio.to_thread(append_row, worksheet, build_test_row(context.bot_data["timezone"]))
    except Exception:  # Cualquier fallo (red, permisos, cuota) impide confirmar el registro.
        logger.exception("Error al escribir en Google Sheets")
        await update.message.reply_text("No pude guardar en Google Sheets. Revisa la configuración.")
        return
    await update.message.reply_text("Fila de prueba guardada en Transacciones.")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Placeholder hasta la Etapa 5 (interpretación con IA).
    await update.message.reply_text(f"Recibido: {update.message.text}")


def owner_filter(settings: Settings) -> filters.BaseFilter:
    # Descarta antes de llegar a los handlers cualquier remitente que no sea el propietario.
    return filters.User(user_id=settings.telegram_owner_id)


def build_application(settings: Settings, worksheet: gspread.Worksheet) -> Application:
    owner = owner_filter(settings)

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.bot_data["worksheet"] = worksheet
    application.bot_data["timezone"] = settings.timezone
    application.add_handler(CommandHandler("start", start, filters=owner))
    application.add_handler(CommandHandler("prueba", prueba, filters=owner))
    application.add_handler(MessageHandler(owner & filters.TEXT & ~filters.COMMAND, echo))
    return application
