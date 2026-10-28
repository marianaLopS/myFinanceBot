"""Bot de Telegram: recibe mensajes del propietario, aclara lo que falta y registra en Sheets."""

import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from finance_bot.catalog import read_catalog
from finance_bot.config import Settings
from finance_bot.flow import Ask, Outcome, Reply, Save, answer, start
from finance_bot.interpreter import interpret_message
from finance_bot.providers import LLMProvider
from finance_bot.sheets import TRANSACTIONS_TAB, append_row, build_test_row
from finance_bot.state import BotState

logger = logging.getLogger(__name__)

SAVE_ERROR = "No pude completar el registro. No se guardó nada; intenta de nuevo."


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state: BotState = context.bot_data["state"]
    update_id = update.update_id
    chat_id = update.effective_chat.id
    text = update.message.text

    # Telegram reintenta entregas sin confirmar; un update ya atendido no se procesa de nuevo.
    if await asyncio.to_thread(state.is_processed, update_id):
        return

    spreadsheet = context.bot_data["spreadsheet"]
    today = datetime.now(ZoneInfo(context.bot_data["timezone"])).date().isoformat()
    try:
        catalog = await asyncio.to_thread(read_catalog, spreadsheet)
        draft = await asyncio.to_thread(state.get_draft, chat_id)
        if draft is not None:
            # Hay una pregunta pendiente: el mensaje es la respuesta.
            outcome = answer(draft, text, catalog)
        else:
            movement = await asyncio.to_thread(interpret_message, context.bot_data["provider"], text, catalog, today)
            outcome = start(movement, catalog, today, text)
        if isinstance(outcome, Save):
            worksheet = await asyncio.to_thread(spreadsheet.worksheet, TRANSACTIONS_TAB)
            # Solo se confirma si Sheets respondió sin error.
            await asyncio.to_thread(append_row, worksheet, outcome.row)
    except Exception:  # IA, Sheets o lectura del catálogo: nada se confirma.
        logger.exception("Error al procesar el mensaje")
        await update.message.reply_text(SAVE_ERROR)
        return

    try:
        await asyncio.to_thread(_update_state, state, chat_id, update_id, outcome)
    except Exception:
        logger.exception("No se pudo actualizar el estado local")

    await update.message.reply_text(_reply_text(outcome))


def _update_state(state: BotState, chat_id: int, update_id: int, outcome: Outcome) -> None:
    if isinstance(outcome, Ask):
        state.save_draft(chat_id, outcome.draft)
    elif isinstance(outcome, Save) or outcome.clear_draft:
        state.clear_draft(chat_id)
    state.mark_processed(update_id)


def _reply_text(outcome: Outcome) -> str:
    if isinstance(outcome, Save):
        return outcome.summary
    return outcome.text


def owner_filter(settings: Settings) -> filters.BaseFilter:
    # Descarta antes de llegar a los handlers cualquier remitente que no sea el propietario.
    return filters.User(user_id=settings.telegram_owner_id)


def build_application(settings: Settings, spreadsheet: gspread.Spreadsheet, provider: LLMProvider) -> Application:
    owner = owner_filter(settings)

    # concurrent_updates=False: los mensajes se procesan en orden, así el borrador pendiente es confiable.
    application = Application.builder().token(settings.telegram_bot_token).concurrent_updates(False).build()
    application.bot_data["spreadsheet"] = spreadsheet
    application.bot_data["provider"] = provider
    application.bot_data["state"] = BotState(settings.database_path)
    application.bot_data["timezone"] = settings.timezone
    application.add_handler(CommandHandler("start", start_command, filters=owner))
    application.add_handler(CommandHandler("prueba", prueba, filters=owner))
    application.add_handler(MessageHandler(owner & filters.TEXT & ~filters.COMMAND, handle_message))
    return application
