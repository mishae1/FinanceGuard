import unittest
import sys
import os

# Пути
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.analyzer import AntifraudAnalyzer
from core.queue_manager import Gateway
from models.transaction import Transaction
from core.generator import TrafficGenerator


class TestBankSimulation(unittest.TestCase):

    def setUp(self):
        self.mock_config = {
            "system_settings": {
                "fps": 60,
                "time_scale": 1.0,
                "gateway_base_mu": 5.0,  # 5 штук в секунду -> 0.2 сек на одну транзакцию
                "antifraud_threshold_multiplier": 2.0,
                "dataset_avg_amount": 1000.0,  # Лимит будет 1000 * 2 = 2000
                "lambda_normal": 10.0,
                "lambda_peak": 20.0,
                "lambda_attack": 30.0,
                "amount_normal_min_mult": 0.5,
                "amount_normal_max_mult": 1.5,
                "amount_fraud_min_mult": 2.5,
                "amount_fraud_max_mult": 4.5
            },
            "markov_matrix_3x3": {
                "0": {"0": 1.0, "1": 0.0, "2": 0.0},
                "1": {"0": 0.0, "1": 1.0, "2": 0.0},
                "2": {"0": 0.0, "1": 0.0, "2": 1.0}
            },
            "markov_matrix_2x2": {
                "0": {"0": 1.0, "1": 0.0},
                "1": {"0": 1.0, "1": 0.0}
            }
        }

    def test_antifraud_allows_normal_amount(self):
        # Сумма 1500, лимит 2000. Должно пропустить.
        analyzer = AntifraudAnalyzer(self.mock_config)
        tx = Transaction(amount=1500.0, is_fraud=False)

        is_safe = analyzer.check_is_safe(tx)

        self.assertTrue(is_safe, "Антифрод должен был пропустить нормальную сумму")
        self.assertEqual(analyzer.false_positives, 0)

    def test_antifraud_blocks_high_amount_fraud(self):
        # Сумма 3000, лимит 2000, и это фрод. Должно заблокировать.
        analyzer = AntifraudAnalyzer(self.mock_config)
        tx = Transaction(amount=3000.0, is_fraud=True)

        is_safe = analyzer.check_is_safe(tx)

        self.assertFalse(is_safe, "Антифрод должен заблокировать превышение лимита")
        self.assertEqual(analyzer.blocked_fraud, 1)

    def test_gateway_processing_timer(self):
        # Проверяем, что шлюз держит транзакцию нужное время (0.2 сек)
        gateway = Gateway(gateway_id=1, base_mu=5.0)
        tx = Transaction(amount=500.0, is_fraud=False)

        gateway.start_processing(tx)
        self.assertIsNotNone(gateway.current_transaction)

        # Шагаем на 0.1 сек (шлюз еще занят)
        is_done = gateway.update(0.1)
        self.assertFalse(is_done)
        self.assertIsNotNone(gateway.current_transaction)

        # Шагаем еще на 0.15 сек (в сумме 0.25 сек, время вышло)
        is_done = gateway.update(0.15)
        self.assertTrue(is_done)
        self.assertIsNone(gateway.current_transaction)
        self.assertEqual(gateway.processed_count, 1)


if __name__ == "__main__":
    unittest.main()