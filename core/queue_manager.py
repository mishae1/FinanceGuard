import random
from models.gateway import Gateway


class QueueManager:
    def __init__(self, config, analyzer):
        self.config = config
        self.settings = config["system_settings"]
        self.analyzer = analyzer

        self.temp_buffer = []
        self.queue = []
        self.total_processed = 0

        base_mu = self.settings["gateway_base_mu"]
        gateways_count = self.settings.get("gateways_count", 3)

        # создаем список шлюзов
        self.gateways = []
        for i in range(gateways_count):
            self.gateways.append(Gateway(gateway_id=i, base_mu=base_mu))

    def update(self, dt):
        for tx in self.temp_buffer:
            if self.analyzer.check_is_safe(tx):
                self.queue.append(tx)
        self.temp_buffer.clear()

        for gw in self.gateways:
            if not gw.is_broken:
                break_prob = dt / self.settings["gateway_break_median_sec"]
                if random.random() < break_prob:
                    gw.is_broken = True
                    gw.repair_timer = self.settings["gateway_repair_time_sec"]
                    gw.current_transaction = None

            # таймер обработки или ремонта
            is_done = gw.update(dt)
            if is_done:
                self.total_processed += 1

            if gw.current_transaction is None and not gw.is_broken:
                if len(self.queue) > 0:
                    next_tx = self.queue.pop(0)
                    gw.start_processing(next_tx)