from utils.helpers import clean_str
from datetime import datetime
class Account:
    def __init__(self, acc_id: int, name: str, balance: int | float = 0) -> None:
        if not (isinstance(name, str) and isinstance(acc_id, int) and (1000 <= acc_id <= 10**7)):
            raise ValueError("Недопустимые значения имени или id")
        self.name = clean_str(name)
        self.balance = balance
        self.acc_id = acc_id
        self.is_activ = True
        self.history = []
        self.last_update = datetime.now()
