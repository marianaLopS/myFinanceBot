"""Punto de entrada: python -m finance_bot.main"""

import logging

from finance_bot.bot import build_application
from finance_bot.config import load_settings
from finance_bot.providers import make_provider
from finance_bot.sheets import open_spreadsheet


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    # httpx registra la URL con el token del bot en cada petición; se silencia para no exponerlo en logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings = load_settings()
    spreadsheet = open_spreadsheet(settings.google_credentials_file, settings.google_sheet_id)
    provider = make_provider(settings)
    build_application(settings, spreadsheet, provider).run_polling()


if __name__ == "__main__":
    main()
