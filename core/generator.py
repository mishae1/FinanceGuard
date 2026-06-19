import random
from models.transaction import Transaction


class TrafficGenerator:
    def __init__(self, config: dict):
        self.settings = config["system_settings"]
        self.matrix_3x3 = config["markov_matrix_3x3"]
        self.matrix_2x2 = config["markov_matrix_2x2"]

        self.current_mode = 0
        self.last_was_fraud = 0
        self.mode_timer = 0.0
        self.generation_timer = 0.0
        self.total_fraud_generated = 0

    def update(self, dt: float, queue_to_fill: list):
        # 1. Смена режима системы (Марковская цепь 3х3)
        self.mode_timer += dt
        interval = self.settings.get("mode_switch_interval_sec", 2.0)
        if self.mode_timer > interval:
            self.mode_timer = 0.0
            probs = self.matrix_3x3[str(self.current_mode)]
            self.current_mode = random.choices(
                [0, 1, 2], weights=[probs["0"], probs["1"], probs["2"]]
            )[0]

        # 2. Выбор интенсивности потока
        if self.current_mode == 0:
            current_lambda = self.settings["lambda_normal"]
        elif self.current_mode == 1:
            current_lambda = self.settings["lambda_peak"]
        else:
            current_lambda = self.settings["lambda_attack"]

        # 3. Генерация транзакций
        self.generation_timer += dt
        time_between_arrivals = 1.0 / current_lambda

        while self.generation_timer >= time_between_arrivals:
            self.generation_timer -= time_between_arrivals

            probs_fraud = self.matrix_2x2[str(self.last_was_fraud)]
            is_fraud = random.choices(
                [False, True], weights=[probs_fraud["0"], probs_fraud["1"]]
            )[0]
            self.last_was_fraud = 1 if is_fraud else 0

            if is_fraud:
                self.total_fraud_generated += 1

            avg_amt = self.settings["dataset_avg_amount"]
            if not is_fraud:
                min_m = self.settings["amount_normal_min_mult"]
                max_m = self.settings["amount_normal_max_mult"]
            else:
                min_m = self.settings["amount_fraud_min_mult"]
                max_m = self.settings["amount_fraud_max_mult"]

            amount = avg_amt * random.uniform(min_m, max_m)
            queue_to_fill.append(Transaction(amount, is_fraud))