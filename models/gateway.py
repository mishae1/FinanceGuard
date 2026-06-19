class Gateway:
    def __init__(self, gateway_id: int, base_mu: float):
        self.gateway_id = gateway_id
        self.base_mu = base_mu

        self.current_transaction = None
        self.process_timer = 0.0

        self.is_broken = False
        self.repair_timer = 0.0
        self.processed_count = 0

    def start_processing(self, transaction):
        self.current_transaction = transaction
        self.process_timer = 1.0 / self.base_mu

    def update(self, dt: float):
        if self.is_broken:
            self.repair_timer -= dt
            if self.repair_timer <= 0.0:
                self.is_broken = False
            return False

        if self.current_transaction:
            self.process_timer -= dt
            if self.process_timer <= 0.0:
                self.current_transaction = None
                self.processed_count += 1
                return True
        return False