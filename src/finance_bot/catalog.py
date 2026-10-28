"""Lee las categorías y cuentas que existen en la hoja de cada usuario."""

import unicodedata
from dataclasses import dataclass
from typing import Sequence

import gspread

# Nombres reales de las pestañas de la plantilla. Categorías tiene un espacio final en el nombre.
CATEGORIES_TAB = "Categorías "
ACCOUNTS_TAB = "Cuentas"
CATEGORIES_HEADER = "Categoria"
ACCOUNTS_HEADER = "Cuenta"
ACCOUNTS_END = "Total"


@dataclass(frozen=True)
class Catalog:
    categories: tuple[str, ...]
    accounts: tuple[str, ...]


def parse_catalog(categories_column: Sequence[str], accounts_column: Sequence[str]) -> Catalog:
    # Toma los valores debajo del encabezado y quita espacios sobrantes.
    # Cuentas termina en la fila "Total"; las columnas siguientes de la hoja son resúmenes, no cuentas.
    categories = _values_after(categories_column, CATEGORIES_HEADER)
    accounts = _values_after(accounts_column, ACCOUNTS_HEADER, stop_at=ACCOUNTS_END)
    return Catalog(categories=tuple(categories), accounts=tuple(accounts))


def read_catalog(spreadsheet: gspread.Spreadsheet) -> Catalog:
    categories_column = spreadsheet.worksheet(CATEGORIES_TAB).col_values(1)
    accounts_column = spreadsheet.worksheet(ACCOUNTS_TAB).col_values(1)
    return parse_catalog(categories_column, accounts_column)


def match_option(text: str | None, options: Sequence[str]) -> str | None:
    # Compara sin mayúsculas ni tildes y devuelve el nombre exacto de la hoja.
    if not text:
        return None
    wanted = _normalize(text)
    for option in options:
        if _normalize(option) == wanted:
            return option
    return None


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.strip().casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _values_after(column: Sequence[str], header: str, stop_at: str | None = None) -> list[str]:
    cleaned = [value.strip() for value in column]
    if header not in cleaned:
        raise ValueError(f"No encontré el encabezado '{header}' en la hoja")
    values = []
    for value in cleaned[cleaned.index(header) + 1 :]:
        if value == stop_at:
            break
        if value:
            values.append(value)
    return values
