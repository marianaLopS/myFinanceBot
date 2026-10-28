"""Bot de Telegram: recibe mensajes del propietario y responde."""

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from finance_bot.catalog import read_catalog
from finance_bot.config import Settings
from finance_bot.interpreter import format_movement, interpret_message
from finance_bot.providers import LLMProvider
from finance_bot.sheets import TRANSACTIONS_TAB, append_row, build_test_row

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hola. Envíame un movimiento, por ejemplo: Gasté $19.000 en almuerzo.")


async def prueba(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Escribe una fila fija de prueba. Solo confirma si Sheets respondió sin error.
    try:
        worksheet = await asyncio.to_thread(context.bot_data["spreadsheet"].worksheet, TRANSACTIONS_TAB)
        await asyncio.to_thread(append_row, worksheet, build_test_row(context.bot_data["timezone"]))
    except Exception:  # Cualquier fallo (red, permisos, cuota) impide confirmar el registro.
        logger.exception("Error al escribir en Google Sheets")
        await update.message.reply_text("No pude guardar en Google Sheets. Revisa la configuración.")
        return
    await update.message.reply_text("Fila de prueba guardada en Transacciones.")


async def interpret(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Interpreta el mensaje con la IA y muestra el resultado. Todavía no escribe en la hoja (Etapa 6).
    timezone = ZoneInfo(context.bot_data["timezone"])
    today = datetime.now(timezone).date().isoformat()
    try:
        catalog = await asyncio.to_thread(read_catalog, context.bot_data["spreadsheet"])
        movement = await asyncio.to_thread(
            interpret_message, context.bot_data["provider"], update.message.text, catalog, today
        )
    except Exception:  # Respuesta de la IA mal formada, cuota agotada, red, etc.
        logger.exception("Error al interpretar el mensaje")
        await update.message.reply_text("No pude interpretar el mensaje. Intenta de nuevo.")
        return
    await update.message.reply_text(format_movement(movement))


def owner_filter(settings: Settings) -> filters.BaseFilter:
    # Descarta antes de llegar a los handlers cualquier remitente que no sea el propietario.
    return filters.User(user_id=settings.telegram_owner_id)


def build_application(settings: Settings, spreadsheet: gspread.Spreadsheet, provider: LLMProvider) -> Application:
    owner = owner_filter(settings)

    application = Application.builder().token(settings.telegram_bot_token).build()
    application.bot_data["spreadsheet"] = spreadsheet
    application.bot_data["provider"] = provider
    application.bot_data["timezone"] = settings.timezone
    application.add_handler(CommandHandler("start", start, filters=owner))
    application.add_handler(CommandHandler("prueba", prueba, filters=owner))
    application.add_handler(MessageHandler(owner & filters.TEXT & ~filters.COMMAND, interpret))
    return application
