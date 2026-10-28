import json
import unittest

from finance_bot.catalog import Catalog
from finance_bot.interpreter import build_prompt, format_movement, interpret_message, parse_movement

CATALOG = Catalog(categories=("Comer afuera", "Transporte"), accounts=("Bancolombia", "Efectivo"))


class FakeProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[str] = []

    def complete(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


class BuildPromptTest(unittest.TestCase):
    def test_prompt_lists_only_catalog_options(self) -> None:
        prompt = build_prompt("almuerzo", CATALOG, "2026-10-27")
        self.assertIn("Comer afuera, Transporte", prompt)
        self.assertIn("Bancolombia, Efectivo", prompt)
        self.assertIn("Hoy es 2026-10-27", prompt)
        self.assertTrue(prompt.endswith("Mensaje: almuerzo"))


class ParseMovementTest(unittest.TestCase):
    def test_valid_json_becomes_movement(self) -> None:
        raw = json.dumps(
            {
                "tipo": "gasto",
                "descripcion": "almuerzo",
                "monto": 19000,
                "categoria": "Comer afuera",
                "cuenta": "Efectivo",
                "fecha": "2026-10-27",
            }
        )
        movement = parse_movement(raw)
        self.assertEqual(movement.tipo, "gasto")
        self.assertEqual(movement.monto, 19000)
        self.assertEqual(movement.cuenta, "Efectivo")

    def test_missing_fields_become_none(self) -> None:
        movement = parse_movement('{"tipo": "gasto", "monto": 5000}')
        self.assertIsNone(movement.categoria)
        self.assertIsNone(movement.fecha)

    def test_unknown_type_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_movement('{"tipo": "robo"}')

    def test_non_numeric_amount_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_movement('{"tipo": "gasto", "monto": "diecinueve mil"}')

    def test_invalid_json_is_rejected(self) -> None:
        with self.assertRaises(json.JSONDecodeError):
            parse_movement("no es json")


class InterpretMessageTest(unittest.TestCase):
    def test_sends_prompt_to_provider_and_parses_answer(self) -> None:
        provider = FakeProvider('{"tipo": "gasto", "monto": 19000}')
        movement = interpret_message(provider, "Gasté $19.000", CATALOG, "2026-10-27")
        self.assertEqual(movement.monto, 19000)
        self.assertIn("Mensaje: Gasté $19.000", provider.prompts[0])


class FormatMovementTest(unittest.TestCase):
    def test_shows_extracted_fields(self) -> None:
        movement = parse_movement(
            '{"tipo": "gasto", "descripcion": "almuerzo", "monto": 19000, '
            '"categoria": "Comer afuera", "cuenta": "Efectivo", "fecha": "2026-10-27"}'
        )
        text = format_movement(movement)
        self.assertIn("Monto: 19000", text)
        self.assertIn("Categoría: Comer afuera", text)
        self.assertIn("Aún no se guarda", text)

    def test_non_financial_message_gets_guidance(self) -> None:
        text = format_movement(parse_movement('{"tipo": "otro"}'))
        self.assertIn("Por ahora solo registro", text)


if __name__ == "__main__":
    unittest.main()
