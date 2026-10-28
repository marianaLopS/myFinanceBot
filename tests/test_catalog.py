import unittest

from finance_bot.catalog import parse_catalog


class ParseCatalogTest(unittest.TestCase):
    def test_reads_values_after_headers_and_trims_spaces(self) -> None:
        categories = ["Categoria", "Salud", "Transporte ", "Educación "]
        accounts = ["Saldo Total", "Cuenta", "Bancolombia", "Efectivo ", "Total", "ignorada"]
        catalog = parse_catalog(categories, accounts)
        self.assertEqual(catalog.categories, ("Salud", "Transporte", "Educación"))
        self.assertEqual(catalog.accounts, ("Bancolombia", "Efectivo"))

    def test_accounts_stop_at_total_row(self) -> None:
        accounts = ["Saldo Total", "Cuenta", "Nequi", "Total", "Dolares"]
        self.assertEqual(parse_catalog(["Categoria"], accounts).accounts, ("Nequi",))

    def test_missing_header_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            parse_catalog(["Salud"], ["Cuenta", "Nequi"])


if __name__ == "__main__":
    unittest.main()
