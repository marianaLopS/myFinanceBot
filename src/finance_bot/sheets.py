"""Escritura de movimientos en la pestaña Transacciones de Google Sheets."""

from datetime import datetime
from typing import Sequence
from zoneinfo import ZoneInfo

import gspread

TRANSACTIONS_TAB = "Transacciones"
TEST_DESCRIPTION = "Prueba de conexión"


def open_spreadsheet(credentials_file: str, sheet_id: str) -> gspread.Spreadsheet:
    # Requiere que la hoja esté compartida con el correo de la cuenta de servicio (Editor).
    client = gspread.service_account(filename=credentials_file)
    return client.open_by_key(sheet_id)


def build_test_row(timezone: str) -> list[str | int]:
    today = datetime.now(ZoneInfo(timezone)).date().isoformat()
    # Orden de columnas de la plantilla: Descripción | Fecha | Categoría | Monto | Cuenta
    return [TEST_DESCRIPTION, today, "Prueba", 0, "Prueba"]


def append_row(worksheet: gspread.Worksheet, row: Sequence[str | int]) -> None:
    # USER_ENTERED hace que Sheets interprete fechas y números como lo haría el usuario al escribir.
    # Si la API falla, lanza excepción y el llamador no confirma el registro.
    worksheet.append_row(list(row), value_input_option="USER_ENTERED")
