import os
import csv
import time
import math
import json

def test_velocity_limit_performance(amount: float, current_hours_tx_list: list, current_hours: int) -> float:
    start_time = time.perf_counter()
    valid_txs = [tx for tx in current_hours_tx_list if tx[0] == current_hours]
    total_hourly_amount = sum(tx_amt for _, tx_amt in valid_txs) + amount
    total_hourly_count = len(valid_txs) + 1
    _is_anomaly = total_hourly_amount > 7 or total_hourly_amount > 20000.0
    return time.perf_counter() - start_time

def test_z_score_performance(amoun: float, history_list: list) -> float:
    start_time = time.perf_counter()
    if len(history_list) < 2:
        return time.perf_counter() - start_time
    n = len(history_list)
    mean = sum(history_list) / n
    sigma = math.sqrt(sum((x - mean) ** 2 for x in history_list) / n)
    if sigma == 0:
        sigma = 0.1
    _ = (amoun - mean) / sigma
    return time.perf_counter() - start_time

def run_hardware_benchmark(csv_path: str):
    print("Запуск теста")
    user_history = {}  # Хранит суммы для Z-score
    user_time_logs = {}  # Для цепочки платежей
    total_z_time = 0.0
    total_velocity_time = 0.0
    limit_rows = 6 * 10**5
    processed_rows = 0
    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)
        amount_idx = headers.index("amount")
        sender_idx = headers.index("nameOrig")
        hour_idx = headers.index("step")
        for row in reader:
            if processed_rows >= limit_rows:
                break
            if not row or len(row) <= max(amount_idx, sender_idx, hour_idx):
                continue
            try:
                amount = float(row[amount_idx])
                sender = row[sender_idx].strip()
                hour = int(row[hour_idx])
            except ValueError:
                continue
            if amount <= 0:
                continue

            if sender not in user_history:
                user_history[sender] = []
                user_time_logs[sender] = []

            v_dur = test_velocity_limit_performance(amount, user_time_logs[sender], hour)
            total_velocity_time += v_dur

            z_dur = test_z_score_performance(amount, user_history[sender])
            total_z_time += z_dur
            user_time_logs[sender].append((hour, amount))
            user_history[sender].append(amount)
            processed_rows += 1

    avg_velocity_time = total_velocity_time / processed_rows if processed_rows > 0 else 0.0
    avg_z_time = total_z_time / processed_rows if processed_rows > 0 else 0.0

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    config_path = os.path.join(project_root, "core", "config.json")
    if os.path.exists(config_path):# читаем джейсон
        with open(config_path, mode="r", encoding="utf-8") as f:
            config_data = json.load(f)
    else:
        config_data = {}

    config_data["avg_velocity_time"] = avg_velocity_time
    config_data["avg_z_score_time"] = avg_z_time
    with open(config_path, mode="w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)


    print(f"Обработано {processed_rows}")
    print(f"Среднее время Velocity Check: {avg_velocity_time * 1000000:.3f} мкс")
    print(f"Среднее время Z-score: {avg_z_time * 1000000:.3f} мкс")
    print(f"джейсон {config_path}")


if __name__ == "__main__":
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(current_script_dir, "transactions.csv")
    run_hardware_benchmark(csv_file)




