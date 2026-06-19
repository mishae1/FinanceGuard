class Transaction:
    def __init__(self, amount: float, is_fraud: bool):
        self.amount = amount
        self.is_fraud = is_fraud