class Transaction:
    def __init__(self, tx_id: int, sender_id: int, receiver_id: int,
                 amount: float, complexity: float, status: str):
        self.id = tx_id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.amount = amount
        self.complexity = complexity
        self.status = status

