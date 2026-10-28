import datetime
import unittest

from telegram import Chat, Message, MessageEntity, Update, User
from telegram.ext import CommandHandler

from finance_bot.bot import build_application, owner_filter
from finance_bot.config import Settings

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
        self.application = build_application(make_settings())
        self.start, self.echo = self.application.handlers[0]

    def test_start_command_is_registered_and_not_echoed(self) -> None:
        # CommandHandler.check_update necesita un bot inicializado (red), así que se revisa la configuración.
        self.assertIsInstance(self.start, CommandHandler)
        self.assertEqual(self.start.commands, frozenset({"start"}))
        self.assertFalse(self.echo.check_update(make_update(OWNER_ID, "/start")))

    def test_plain_text_goes_to_echo_handler(self) -> None:
        update = make_update(OWNER_ID, "Gasté $19.000")
        self.assertFalse(self.start.check_update(update))
        self.assertTrue(self.echo.check_update(update))


if __name__ == "__main__":
    unittest.main()
