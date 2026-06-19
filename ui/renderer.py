import pygame


class SimulationRenderer:
    COLOR_BG = (240, 243, 246)  # Серый фон приложения
    COLOR_PANEL_BG = (255, 255, 255)  # Белый фон для панелей
    COLOR_BORDER = (220, 224, 230)  # Светлая граница блоков
    COLOR_BORDER_STATUS = (70, 130, 180)  # Синяя граница главного статуса

    # Цвета текста
    COLOR_TEXT_MAIN = (50, 70, 100)  # Синий для заголовков
    COLOR_TEXT_MUTED = (100, 110, 120)  # Серый для подписей
    COLOR_TEXT_DARK = (20, 50, 90)  # Насыщенный для важного текста

    COLOR_FRAUD = (240, 128, 128)
    COLOR_NORMAL = (144, 238, 144)
    COLOR_PROCESS = (0, 123, 255)

    # Вспомогательные
    COLOR_GATEWAY_BG = (248, 249, 250)  # Фон плашки шлюза
    COLOR_GATEWAY_BORDER = (200, 205, 210)  # Контур плашки шлюза

    def __init__(self, config: dict):
        pygame.init()
        self.settings = config["system_settings"]
        self.screen = pygame.display.set_mode((1000, 650))
        pygame.display.set_caption("Мониторинговый комплекс Банка")

        self.font_normal = pygame.font.SysFont("Arial", 14)
        self.font_bold = pygame.font.SysFont("Arial", 15, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 18, bold=True)

    def render_frame(self, mode, metrics, queue_obj, gateways, fps=0):
        # Заливаем фон
        self.screen.fill(self.COLOR_BG)
        self._draw_status_panel(mode)
        self._draw_queue_panel(queue_obj)
        self._draw_gateways_panel(gateways)
        self._draw_sidebar(metrics, mode)

        pygame.display.flip()

    def _draw_status_panel(self, mode):
        modes_text = ["NORMAL (Стабильный режим)", "PEAK (Высокая нагрузка)", "ATTACK (Критический режим)"]

        pygame.draw.rect(self.screen, self.COLOR_PANEL_BG, (20, 20, 660, 60), border_radius=8)
        pygame.draw.rect(self.screen, self.COLOR_BORDER_STATUS, (20, 20, 660, 60), width=2, border_radius=8)

        title = self.font_bold.render("ТЕКУЩЕЕ СОСТОЯНИЕ СИСТЕМЫ:", True, self.COLOR_TEXT_MUTED)
        status_val = self.font_large.render(modes_text[mode], True, self.COLOR_TEXT_DARK)

        self.screen.blit(title, (40, 28))
        self.screen.blit(status_val, (340, 26))

    def _draw_queue_panel(self, queue_list):
        pygame.draw.rect(self.screen, self.COLOR_PANEL_BG, (20, 100, 660, 180), border_radius=8)
        pygame.draw.rect(self.screen, self.COLOR_BORDER, (20, 100, 660, 180), width=1, border_radius=8)

        title = self.font_bold.render(f"ОЧЕРЕДЬ ТРАНЗАКЦИЙ НА ПРОВЕРКУ (Всего: {len(queue_list)})", True,
                                      self.COLOR_TEXT_MAIN)
        self.screen.blit(title, (40, 115))

        start_x = 40
        start_y = 150
        max_visible = 14

        for i, tx in enumerate(queue_list[:max_visible]):
            color = self.COLOR_FRAUD if tx.is_fraud else self.COLOR_NORMAL

            pygame.draw.rect(self.screen, color, (start_x + i * 42, start_y, 35, 35), border_radius=4)
            pygame.draw.rect(self.screen, self.COLOR_TEXT_MUTED, (start_x + i * 42, start_y, 35, 35), width=1,
                             border_radius=4)

    def _draw_gateways_panel(self, gateways):
        pygame.draw.rect(self.screen, self.COLOR_PANEL_BG, (20, 300, 660, 330), border_radius=8)
        pygame.draw.rect(self.screen, self.COLOR_BORDER, (20, 300, 660, 330), width=1, border_radius=8)

        title = self.font_bold.render("КАНАЛЫ ОБСЛУЖИВАНИЯ (СЕРВЕРА-ШЛЮЗЫ)", True, self.COLOR_TEXT_MAIN)
        self.screen.blit(title, (40, 315))

        start_y = 350
        for i, gw in enumerate(gateways):
            box_y = start_y + i * 85

            pygame.draw.rect(self.screen, self.COLOR_GATEWAY_BG, (40, box_y, 620, 70), border_radius=6)
            pygame.draw.rect(self.screen, self.COLOR_GATEWAY_BORDER, (40, box_y, 620, 70), width=1, border_radius=6)

            if gw.is_broken:
                status_str = f"СЛОМАН (Ремонт: {max(0.0, gw.repair_timer):.1f}с)"
                color = self.COLOR_FRAUD
            elif gw.current_transaction:
                status_str = "ОБРАБОТКА"
                color = self.COLOR_PROCESS
            else:
                status_str = "СВОБОДЕН"
                color = self.COLOR_NORMAL

            pygame.draw.circle(self.screen, color, (65, box_y + 35), 8)

            gw_info = self.font_bold.render(f"Шлюз #{gw.gateway_id + 1}  [Обработано: {gw.processed_count} шт.]", True,
                                            self.COLOR_TEXT_MAIN)
            gw_stat = self.font_normal.render(status_str, True, self.COLOR_TEXT_MUTED)

            self.screen.blit(gw_info, (90, box_y + 15))
            self.screen.blit(gw_stat, (90, box_y + 38))

    def _draw_sidebar(self, metrics, mode):
        panel_x = 700
        pygame.draw.rect(self.screen, self.COLOR_PANEL_BG, (panel_x, 0, 300, 650))
        pygame.draw.line(self.screen, self.COLOR_BORDER, (panel_x, 0), (panel_x, 650), 2)
        pygame.draw.line(self.screen, self.COLOR_BG, (710, 290), (980, 290), 1)

        self.screen.blit(self.font_bold.render("МОНИТОРИНГ СТАТИСТИКИ", True, self.COLOR_TEXT_MAIN), (panel_x + 25, 25))

        stats_labels = [
            f"Обработано заявок: {metrics['processed']}",
            f"Всего фрода создано: {metrics['total_fraud']}",
            f"Заблокировано фрода: {metrics['tp']}",
            f"Ложные срабатывания: {metrics['fp']}",
            f"Пропущено фрода: {metrics['fn']}"
        ]

        for i, label in enumerate(stats_labels):
            surf = self.font_normal.render(label, True, self.COLOR_TEXT_MAIN)
            self.screen.blit(surf, (panel_x + 25, 65 + i * 30))

        self.screen.blit(self.font_bold.render("ТЕОРЕТИЧЕСКИЙ АНАЛИЗ", True, self.COLOR_TEXT_MAIN), (panel_x + 25, 315))

        if mode == 0:
            current_lambda = self.settings.get("lambda_normal", 3.0)
        elif mode == 1:
            current_lambda = self.settings.get("lambda_peak", 15.0)
        else:
            current_lambda = self.settings.get("lambda_attack", 35.0)

        t_work = self.settings.get("gateway_break_median_sec", 30.0)
        t_repair = self.settings.get("gateway_repair_time_sec", 5.0)
        uptime_coef = t_work / (t_work + t_repair) if (t_work + t_repair) > 0 else 1.0

        gateways_count = self.settings.get("gateways_count", 3)
        mu_base = self.settings.get("gateway_base_mu", 2.6)
        mu_total = gateways_count * mu_base * uptime_coef

        load_coef = current_lambda / mu_total if mu_total > 0 else 999.0

        theory_lines = [
            "Текущий входящий поток:",
            f"  - Интенсивность: {current_lambda} ед/сек",
            "Каналы обслуживания:",
            f"  - Скорость 1 шлюза: {mu_base} ед/сек",
            f"  - Общая скорость: {mu_total:.2f} ед/сек",
            "Текущая стабильность СМО:",
            f"  - Коэф. загрузки: {load_coef:.3f}",
            "  - Очередь стабильна" if load_coef < 1.0 else "  - Внимание: перегрузка!"
        ]

        for i, line in enumerate(theory_lines):
            is_highlight = "Интенсивность:" in line or "Загрузка:" in line or "Общая" in line or "стабильна" in line
            color = self.COLOR_PROCESS if is_highlight else self.COLOR_TEXT_MUTED

            font = self.font_bold if is_highlight else self.font_normal
            surf = font.render(line, True, color)
            self.screen.blit(surf, (panel_x + 25, 355 + i * 26))