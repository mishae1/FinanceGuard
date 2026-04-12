class Bank():
    def __init__(self):
        self.accounts = {}
        self._last_id = 1000
    def create_account(self, name: str, balance: int | float) -> int:
        if not(isinstance(name, str) and isinstance(balance, (int, float)) and (0 <= balance <= 10**9)):
            raise ValueError("Некорректные данные")
        self._last_id += 1
        new_id = self._last_id
        new_acc = Account(new_id, name, balance)
        self.accounts[new_id] = new_acc
        return new_id