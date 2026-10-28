import unittest

from finance_bot.catalog import Catalog
from finance_bot.flow import Ask, Reply, Save, answer, parse_amount, start
from finance_bot.interpreter import Movement

CATALOG = Catalog(categories=("Comer afuera", "Transporte"), accounts=("Bancolombia", "Efectivo"))
TODAY = "2026-10-27"


def movement(**overrides) -> Movement:
    fields = dict(tipo="gasto", descripcion="almuerzo", monto=19000, categoria="Comer afuera", cuenta="Efectivo", fecha="2026-10-27")
    fields.update(overrides)
    return Movement(**fields)


class ParseAmountTest(unittest.TestCase):
    def test_colombian_formats(self) -> None:
        self.assertEqual(parse_amount("19.000"), 19000.0)
        self.assertEqual(parse_amount("$19,000"), 19000.0)
        self.assertEqual(parse_amount("19000"), 19000.0)

    def test_rejects_text_zero_and_decimals(self) -> None:
        self.assertIsNone(parse_amount("diecinueve mil"))
        self.assertIsNone(parse_amount("0"))
        self.assertIsNone(parse_amount("1.5k"))


class StartTest(unittest.TestCase):
    def test_complete_expense_is_saved_with_negative_amount(self) -> None:
        outcome = start(movement(), CATALOG, TODAY, "almuerzo")
        self.assertIsInstance(outcome, Save)
        self.assertEqual(outcome.row, ("almuerzo", "2026-10-27", "Comer afuera", -19000, "Efectivo"))

    def test_income_is_saved_with_positive_amount(self) -> None:
        outcome = start(movement(tipo="ingreso", monto=150000, categoria="Salario"), CATALOG, TODAY, "sueldo")
        self.assertIsInstance(outcome, Ask)  # "Salario" no está en el catálogo de prueba
        outcome = start(movement(tipo="ingreso", monto=150000, categoria="Transporte", cuenta="Bancolombia"), CATALOG, TODAY, "sueldo")
        self.assertEqual(outcome.row[3], 150000)

    def test_negative_amount_from_model_is_made_positive(self) -> None:
        outcome = start(movement(monto=-19000), CATALOG, TODAY, "almuerzo")
        self.assertEqual(outcome.row[3], -19000)

    def test_missing_account_asks_with_options(self) -> None:
        outcome = start(movement(cuenta=None), CATALOG, TODAY, "almuerzo")
        self.assertIsInstance(outcome, Ask)
        self.assertIn("Opciones: Bancolombia, Efectivo", outcome.text)

    def test_unknown_category_is_replaced_by_question(self) -> None:
        outcome = start(movement(categoria="Mercado"), CATALOG, TODAY, "almuerzo")
        self.assertIsInstance(outcome, Ask)
        self.assertIn("No tengo la categoría 'Mercado'", outcome.text)
        self.assertIn("Opciones: Comer afuera, Transporte", outcome.text)

    def test_category_match_ignores_case_and_accents(self) -> None:
        outcome = start(movement(categoria="comer AFUERA"), CATALOG, TODAY, "almuerzo")
        self.assertEqual(outcome.row[2], "Comer afuera")

    def test_missing_date_defaults_to_today(self) -> None:
        outcome = start(movement(fecha=None), CATALOG, TODAY, "almuerzo")
        self.assertEqual(outcome.row[1], TODAY)

    def test_missing_description_uses_original_message(self) -> None:
        outcome = start(movement(descripcion=None), CATALOG, TODAY, "comí almuerzo")
        self.assertEqual(outcome.row[0], "comí almuerzo")

    def test_non_recordable_type_is_not_saved(self) -> None:
        outcome = start(movement(tipo="consulta"), CATALOG, TODAY, "¿cuánto gasté?")
        self.assertIsInstance(outcome, Reply)
        self.assertTrue(outcome.clear_draft)

    def test_missing_amount_asks(self) -> None:
        outcome = start(movement(monto=None), CATALOG, TODAY, "almuerzo")
        self.assertIn("¿Cuánto fue el monto?", outcome.text)


class AnswerTest(unittest.TestCase):
    def test_amount_answer_fills_missing_amount(self) -> None:
        draft = movement(monto=None).__dict__
        outcome = answer(draft, "19.000", CATALOG)
        self.assertEqual(outcome.row[3], -19000)

    def test_bad_amount_asks_again(self) -> None:
        outcome = answer(movement(monto=None).__dict__, "mucho", CATALOG)
        self.assertIsInstance(outcome, Ask)
        self.assertIn("No entendí el monto", outcome.text)

    def test_cancel_clears_draft(self) -> None:
        outcome = answer(movement(monto=None).__dict__, "Cancelar", CATALOG)
        self.assertEqual(outcome, Reply("Cancelado. No se guardó nada.", clear_draft=True))


if __name__ == "__main__":
    unittest.main()
