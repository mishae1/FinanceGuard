class AntifraudAnalyzer:
    def __init__(self, config: dict):
        settings = config["system_settings"]
        self.limit = settings["dataset_avg_amount"] * settings["antifraud_threshold_multiplier"]

        self.blocked_fraud = 0
        self.false_positives = 0
        self.leak_fraud = 0

    def check_is_safe(self, tx) -> bool:
        if tx.amount > self.limit:
            if tx.is_fraud:
                self.blocked_fraud += 1
            else:
                self.false_positives += 1
            return False
        else:
            if tx.is_fraud:
                self.leak_fraud += 1
            return True