import unittest

from finance_bot.state import BotState


class BotStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.state = BotState(":memory:")

    def test_update_is_processed_once_marked(self) -> None:
        self.assertFalse(self.state.is_processed(7))
        self.state.mark_processed(7)
        self.assertTrue(self.state.is_processed(7))
        self.state.mark_processed(7)  # idempotente

    def test_draft_round_trip_and_clear(self) -> None:
        self.assertIsNone(self.state.get_draft(1))
        self.state.save_draft(1, {"tipo": "gasto", "monto": None})
        self.assertEqual(self.state.get_draft(1), {"tipo": "gasto", "monto": None})
        self.state.clear_draft(1)
        self.assertIsNone(self.state.get_draft(1))


if __name__ == "__main__":
    unittest.main()
