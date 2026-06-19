import os
import sys
import json

# Говорим Python искать файлы прямо в папке Bank
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from core.generator import TrafficGenerator
from core.analyzer import AntifraudAnalyzer
from core.queue_manager import QueueManager
from ui.renderer import SimulationRenderer


def main():
    pygame.init()
    clock = pygame.time.Clock()

    # Загружаем конфиг напрямую, без посредников
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core", "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    # Достаем множитель скорости из конфига (по умолчанию 1.0, если ключа нет)
    time_scale = config_data.get("system_settings", {}).get("time_scale", 1.0)

    # Инициализация модулей
    generator = TrafficGenerator(config_data)
    analyzer = AntifraudAnalyzer(config_data)
    queue_manager = QueueManager(config_data, analyzer)
    renderer = SimulationRenderer(config_data)

    running = True
    while running:
        # Получаем реальное время между кадрами (в секундах)
        dt = clock.tick(60) / 1000.0

        # Умножаем реальное время на коэффициент масштабирования
        scaled_dt = dt * time_scale

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Обновление логики симуляции (передаем УСКОРЕННОЕ время)
        generator.update(scaled_dt, queue_manager.temp_buffer)
        queue_manager.update(scaled_dt)

        # Сбор статистики
        stats = {
            "processed": queue_manager.total_processed,
            "total_fraud": generator.total_fraud_generated,
            "tp": analyzer.blocked_fraud,
            "fp": analyzer.false_positives,
            "fn": analyzer.leak_fraud
        }

        # Отрисовка
        renderer.render_frame(
            mode=generator.current_mode,
            metrics=stats,
            queue_obj=queue_manager.queue,
            gateways=queue_manager.gateways,
            fps=clock.get_fps()
        )

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()