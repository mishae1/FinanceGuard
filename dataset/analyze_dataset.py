import csv
import time
from collections import deque
import json
import os

def run_dataset_analysis(csv_path: str):
    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)

        amount_idx = headers.index("amount")
        fraud_inx = headers.index("isFraud")
        sender_idx = headers.index("nameOrig")
        step_idx = headers.index("step")# номер часа

        total_tx_count = 0
        total_fraud_count = 0
        global_amounts_sum = 0.0
        global_fraud_amount_sum = 0.0
        user_interim_histories = {}
        hourly_stats = {}
        last_tx_type = 0
        tx_type_transitions = {i: {j: 0 for j in range(2)} for i in range(2)}

        for row in reader:
            if not row:
                continue
            if len(row) <= max(amount_idx, fraud_inx, sender_idx):
                continue
            try:
                amount = float(row[amount_idx])
                is_fraud = int(row[fraud_inx])
                sender = row[sender_idx].strip()
                hour = int(row[step_idx])
            except ValueError:
                continue
            if amount <= 0:
                continue

            total_tx_count += 1
            global_amounts_sum += amount
            if hour not in hourly_stats:
                hourly_stats[hour] = {"cnt_per_hour": 0, "cnt_fraud": 0, "total_amount": 0.0, "fraud_amount": 0.0}
            hourly_stats[hour]["cnt_per_hour"] += 1
            hourly_stats[hour]["total_amount"] += amount
            if is_fraud == 1:
                total_fraud_count += 1
                global_fraud_amount_sum += amount
                hourly_stats[hour]["fraud_amount"] += amount
                hourly_stats[hour]["cnt_fraud"] += 1
            if sender not in user_interim_histories:
                user_interim_histories[sender] = deque(maxlen=30)
            user_interim_histories[sender].append(amount)

            tx_type_transitions[last_tx_type][is_fraud] += 1# для матрицы 2х2
            last_tx_type = is_fraud

        global_average_amount = global_amounts_sum / total_tx_count if total_tx_count > 0 else 0.0
        fraud_ratio = total_fraud_count / total_tx_count if total_tx_count > 0 else 0.0

        matrix_3x3 = calculate_matrix_3x3(hourly_stats)
        matrix_2x2 = calculate_matrix_2x2(tx_type_transitions)
        config_data = {
            "global_average_amount": global_average_amount,
            "fraud_ratio": fraud_ratio,
            "markov_matrix_3x3": matrix_3x3,
            "markov_matrix_2x2": matrix_2x2,
        }

        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_script_dir)
        target_core_dir = os.path.join(project_root, "core")
        os.makedirs(target_core_dir, exist_ok=True)
        config_json_path = os.path.join(target_core_dir, "config.json")
        with open(config_json_path, mode="w", encoding="utf-8") as json_file:
            json.dump(config_data, json_file, indent=4)
        print_report(matrix_3x3, matrix_2x2)



def calculate_matrix_3x3(hourly_stats: dict) -> dict:
    total_hours = len(hourly_stats)
    if total_hours <= 9:
        return {}
    all_counts = sorted(stats["cnt_per_hour"] for stats in hourly_stats.values())
    idx_80 = int(total_hours * 0.8)
    idx_95 = int(total_hours * 0.95)
    threshold_peak = all_counts[idx_80]
    threshold_attack = all_counts[idx_95]
    hourly_modes = {}
    for hour in sorted(hourly_stats.keys()):
        cnt = hourly_stats[hour]["cnt_per_hour"]
        if  cnt > threshold_attack:
            hourly_modes[hour] = 2 # Атака
        elif cnt > threshold_peak:
            hourly_modes[hour] = 1 # Повышенный
        else:
            hourly_modes[hour] = 0
    transition_counts = {i: {j: 0 for j in range(3)} for i in range(3)}
    modes_list = [hourly_modes[h] for h in sorted(hourly_modes.keys())]
    for i in range(len(modes_list) - 1):
        current_mode = modes_list[i]
        next_mode = modes_list[i + 1]
        transition_counts[current_mode][next_mode] += 1

    markov_matrix_3x3 = {}

    for row_idx in range(3):
        row_sum = sum(transition_counts[row_idx].values())
        markov_matrix_3x3[row_idx] = {
            col_idx: (transition_counts[row_idx][col_idx] / row_sum if row_sum > 0 else 0.0)
            for col_idx in range(3)
        }
    return markov_matrix_3x3

def calculate_matrix_2x2(tx_type_transitions: dict) -> dict:
    markov_fraud_matrix_2x2 = {}
    for row_idx in range(2):
        row_sum = sum(tx_type_transitions[row_idx].values())
        markov_fraud_matrix_2x2[row_idx] = {
            col_idx: (tx_type_transitions[row_idx][col_idx] / row_sum if row_sum > 0 else 0.0)
            for col_idx in range(2)
        }

    return markov_fraud_matrix_2x2

def print_report(markov_matrix_3x3, markov_matrix_2x2) -> None:
    print("Марковская матрица 3х3")
    state_names = {0: "Normal", 1: "Peak", 2: "Attak"}
    for i in range(3):
        p = markov_matrix_3x3[i]
        print(f"Из {state_names[i]} -> На NORMAL: {p[0]:.3f} | На PEAK: {p[1]:.3f} | На ATTACK: {p[2]:.3f}")

    print("Матрица 2х2")
    fraud_state_names = {0: "Чистая", 1: "Фрод  "}

    for i in range(2):
        p = markov_matrix_2x2[i]
        print(f"Из {fraud_state_names[i]} -> на нормальную: {p[0]:.6f} / на фрод: {p[1]:.6f}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    CSV_FILE_PATH = os.path.join(script_dir, "transactions.csv")
    run_dataset_analysis(CSV_FILE_PATH)