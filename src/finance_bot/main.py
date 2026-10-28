"""Punto de entrada: python -m finance_bot.main"""

import logging

from finance_bot.bot import build_application
from finance_bot.config import load_settings


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    # httpx registra la URL con el token del bot en cada petición; se silencia para no exponerlo en logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings = load_settings()
    build_application(settings).run_polling()


if __name__ == "__main__":
    main()
