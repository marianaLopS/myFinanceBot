"""Reglas para decidir si un movimiento se guarda, se aclara o se rechaza."""

import re
from dataclasses import asdict, dataclass, replace
from datetime import date

from finance_bot.catalog import Catalog, match_option
from finance_bot.interpreter import Movement

RECORDABLE_TYPES = ("gasto", "ingreso")
CANCEL_WORD = "cancelar"


@dataclass(frozen=True)
class Save:
    row: tuple[str | int | float, ...]  # Descripción | Fecha | Categoría | Monto | Cuenta
    summary: str


@dataclass(frozen=True)
class Ask:
    text: str
    draft: dict


@dataclass(frozen=True)
class Reply:
    text: str
    clear_draft: bool = False


Outcome = Save | Ask | Reply


def start(movement: Movement, catalog: Catalog, today: str, original_text: str) -> Outcome:
    notices = []
    categoria = _resolve(movement.categoria, catalog.categories, "categoría", notices)
    cuenta = _resolve(movement.cuenta, catalog.accounts, "cuenta", notices)
    fecha = movement.fecha if _is_iso_date(movement.fecha) else today
    draft = replace(
        movement,
        descripcion=movement.descripcion or original_text,
        monto=abs(movement.monto) if movement.monto is not None else None,
        categoria=categoria,
        cuenta=cuenta,
        fecha=fecha,
    )
    return _next(draft, catalog, " ".join(notices))


def answer(draft: dict, reply: str, catalog: Catalog) -> Outcome:
    if reply.strip().casefold() == CANCEL_WORD:
        return Reply("Cancelado. No se guardó nada.", clear_draft=True)

    movement = Movement(**draft)
    if movement.monto is None:
        amount = parse_amount(reply)
        if amount is None:
            return _ask(movement, "No entendí el monto. ¿Cuánto fue? (ejemplo: 19.000)")
        movement = replace(movement, monto=amount)
    elif movement.categoria is None:
        option = match_option(reply, catalog.categories)
        if option is None:
            return _ask(movement, f"No reconozco '{reply.strip()}'.", catalog.categories)
        movement = replace(movement, categoria=option)
    elif movement.cuenta is None:
        option = match_option(reply, catalog.accounts)
        if option is None:
            return _ask(movement, f"No reconozco '{reply.strip()}'.", catalog.accounts)
        movement = replace(movement, cuenta=option)
    return _next(movement, catalog)


def parse_amount(text: str) -> float | None:
    # Formato colombiano: "19.000" y "$19,000" son 19000. Solo se aceptan enteros.
    cleaned = re.sub(r"[\s$.,]", "", text)
    if not cleaned.isdigit() or int(cleaned) == 0:
        return None
    return float(int(cleaned))


def _next(movement: Movement, catalog: Catalog, notice: str = "") -> Outcome:
    if movement.tipo not in RECORDABLE_TYPES:
        return Reply("Por ahora solo registro gastos e ingresos.", clear_draft=True)
    if movement.monto is None:
        return _ask(movement, "¿Cuánto fue el monto?", notice=notice)
    if movement.categoria is None:
        return _ask(movement, "¿En qué categoría lo registro?", catalog.categories, notice)
    if movement.cuenta is None:
        return _ask(movement, "¿Con qué cuenta lo pagaste?", catalog.accounts, notice)
    return _save(movement)


def _ask(movement: Movement, question: str, options: tuple[str, ...] = (), notice: str = "") -> Ask:
    prefix = f"{notice} " if notice else ""
    listing = f"\nOpciones: {', '.join(options)}" if options else ""
    return Ask(text=f"{prefix}{question}{listing}", draft=asdict(movement))


def _save(movement: Movement) -> Save:
    # Gastos negativos, ingresos positivos (regla de la plantilla).
    signed = -movement.monto if movement.tipo == "gasto" else movement.monto
    row = (movement.descripcion, movement.fecha, movement.categoria, signed, movement.cuenta)
    summary = (
        f"Guardado: {movement.tipo} de {movement.monto:,.0f} en {movement.categoria} "
        f"desde {movement.cuenta} ({movement.fecha})."
    )
    return Save(row=row, summary=summary)


def _resolve(value: str | None, options: tuple[str, ...], label: str, notices: list[str]) -> str | None:
    if value is None:
        return None
    matched = match_option(value, options)
    if matched is None:
        notices.append(f"No tengo la {label} '{value}'.")
    return matched


def _is_iso_date(value: str | None) -> bool:
    if not value:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True
