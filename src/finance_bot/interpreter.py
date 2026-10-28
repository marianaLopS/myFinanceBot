"""Interpreta un mensaje en lenguaje natural y lo convierte en un movimiento estructurado."""

import json
from dataclasses import dataclass

from finance_bot.catalog import Catalog
from finance_bot.providers import LLMProvider

MOVEMENT_TYPES = ("gasto", "ingreso", "transferencia", "consulta", "otro")


@dataclass(frozen=True)
class Movement:
    tipo: str
    descripcion: str | None
    monto: float | None
    categoria: str | None
    cuenta: str | None
    fecha: str | None  # AAAA-MM-DD


def build_prompt(text: str, catalog: Catalog, today: str) -> str:
    categories = ", ".join(catalog.categories)
    accounts = ", ".join(catalog.accounts)
    return (
        "Eres un asistente que extrae datos financieros de un mensaje personal en español (Colombia).\n"
        "Responde solo con un objeto JSON con las claves: tipo, descripcion, monto, categoria, cuenta, fecha.\n"
        f"- tipo: uno de {', '.join(MOVEMENT_TYPES)}. 'consulta' si pregunta por datos; 'otro' si no es financiero.\n"
        "- monto: número positivo sin símbolos ni separadores de miles. '$19.000' es 19000.\n"
        "- categoria: exactamente una de estas opciones, o null: " + categories + "\n"
        "- cuenta: exactamente una de estas opciones, o null: " + accounts + "\n"
        f"- fecha: AAAA-MM-DD. Hoy es {today}. Usa null si no se indica.\n"
        "- descripcion: resumen corto del movimiento. Usa null si no hay datos.\n"
        "No inventes valores: si algo no está en el mensaje, usa null.\n\n"
        f"Mensaje: {text}"
    )


def parse_movement(raw: str) -> Movement:
    data = json.loads(raw)
    tipo = data.get("tipo")
    if tipo not in MOVEMENT_TYPES:
        raise ValueError(f"Tipo de movimiento no válido: {tipo!r}")
    monto = data.get("monto")
    if monto is not None and not isinstance(monto, (int, float)):
        raise ValueError(f"Monto no numérico: {monto!r}")
    return Movement(
        tipo=tipo,
        descripcion=data.get("descripcion"),
        monto=monto,
        categoria=data.get("categoria"),
        cuenta=data.get("cuenta"),
        fecha=data.get("fecha"),
    )


def interpret_message(provider: LLMProvider, text: str, catalog: Catalog, today: str) -> Movement:
    raw = provider.complete(build_prompt(text, catalog, today))
    return parse_movement(raw)


def format_movement(movement: Movement) -> str:
    if movement.tipo in ("consulta", "otro"):
        return "Por ahora solo registro gastos e ingresos. Intenta con un movimiento, por ejemplo: Gasté $19.000 en almuerzo."
    lines = [
        f"Tipo: {movement.tipo}",
        f"Descripción: {movement.descripcion or '—'}",
        f"Monto: {movement.monto if movement.monto is not None else '—'}",
        f"Categoría: {movement.categoria or '—'}",
        f"Cuenta: {movement.cuenta or '—'}",
        f"Fecha: {movement.fecha or '—'}",
        "(Aún no se guarda en la hoja.)",
    ]
    return "\n".join(lines)
