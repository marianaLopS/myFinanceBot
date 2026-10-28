import asyncio
import datetime
import unittest
from unittest.mock import AsyncMock, MagicMock

from telegram import Chat, Message, MessageEntity, Update, User
from telegram.ext import CommandHandler

from finance_bot.bot import build_application, owner_filter, prueba
from finance_bot.config import Settings
from finance_bot.sheets import TEST_DESCRIPTION, append_row, build_test_row

OWNER_ID = 111
OTHER_ID = 222


def make_update(user_id: int, text: str) -> Update:
    user = User(id=user_id, first_name="Test", is_bot=False)
    chat = Chat(id=user_id, type=Chat.PRIVATE)
    # Telegram marca los comandos con una entidad bot_command al inicio del texto.
    entities = [MessageEntity(type=MessageEntity.BOT_COMMAND, offset=0, length=len(text))] if text.startswith("/") else None
    message = Message(message_id=1, date=datetime.datetime.now(), chat=chat, from_user=user, text=text, entities=entities)
    return Update(update_id=1, message=message)


def make_settings() -> Settings:
    return Settings(
        telegram_bot_token="123:TEST",
        telegram_owner_id=OWNER_ID,
        google_credentials_file="credentials.json",
        google_sheet_id="sheet",
        ai_provider="gemini",
        gemini_api_key="key",
        gemini_model="gemini-test",
        timezone="America/Bogota",
    )


class OwnerFilterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.owner = owner_filter(make_settings())

    def test_owner_text_passes(self) -> None:
        self.assertTrue(self.owner.check_update(make_update(OWNER_ID, "hola")))

    def test_other_user_text_is_blocked(self) -> None:
        self.assertFalse(self.owner.check_update(make_update(OTHER_ID, "hola")))


class HandlerRoutingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.application = build_application(make_settings(), spreadsheet=None, provider=None)
        self.start, self.prueba_handler, self.text_handler = self.application.handlers[0]

    def test_start_command_is_registered_and_not_interpreted(self) -> None:
        # CommandHandler.check_update necesita un bot inicializado (red), así que se revisa la configuración.
        self.assertIsInstance(self.start, CommandHandler)
        self.assertEqual(self.start.commands, frozenset({"start"}))
        self.assertFalse(self.text_handler.check_update(make_update(OWNER_ID, "/start")))

    def test_prueba_command_is_registered(self) -> None:
        self.assertIsInstance(self.prueba_handler, CommandHandler)
        self.assertEqual(self.prueba_handler.commands, frozenset({"prueba"}))

    def test_plain_text_goes_to_interpreter(self) -> None:
        update = make_update(OWNER_ID, "Gasté $19.000")
        self.assertFalse(self.start.check_update(update))
        self.assertTrue(self.text_handler.check_update(update))


class SheetsWriteTest(unittest.TestCase):
    def test_test_row_has_all_columns_in_order(self) -> None:
        row = build_test_row("America/Bogota")
        self.assertEqual(len(row), 5)
        self.assertEqual(row[0], TEST_DESCRIPTION)
        self.assertRegex(row[1], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(row[3], 0)

    def test_append_row_uses_user_entered_option(self) -> None:
        worksheet = MagicMock()
        append_row(worksheet, ["x", "2026-10-27", "y", 5, "z"])
        worksheet.append_row.assert_called_once_with(
            ["x", "2026-10-27", "y", 5, "z"], value_input_option="USER_ENTERED"
        )


class PruebaCommandTest(unittest.TestCase):
    def make_context(self, worksheet) -> MagicMock:
        spreadsheet = MagicMock()
        spreadsheet.worksheet.return_value = worksheet
        context = MagicMock()
        context.bot_data = {"spreadsheet": spreadsheet, "timezone": "America/Bogota"}
        return context

    def make_update(self) -> MagicMock:
        update = MagicMock()
        update.message.reply_text = AsyncMock()
        return update

    def test_confirms_only_after_sheets_succeeds(self) -> None:
        worksheet = MagicMock()
        update = self.make_update()
        asyncio.run(prueba(update, self.make_context(worksheet)))
        worksheet.append_row.assert_called_once()
        update.message.reply_text.assert_awaited_once_with("Fila de prueba guardada en Transacciones.")

    def test_does_not_confirm_when_sheets_fails(self) -> None:
        worksheet = MagicMock()
        worksheet.append_row.side_effect = RuntimeError("sin permisos")
        update = self.make_update()
        asyncio.run(prueba(update, self.make_context(worksheet)))
        reply = update.message.reply_text.await_args.args[0]
        self.assertIn("No pude guardar", reply)
        self.assertNotIn("guardada", reply)


if __name__ == "__main__":
    unittest.main()
