import csv
import math
import json
import os


def run_dataset_analysis(csv_path: str):
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_script_dir)
    config_json_path = os.path.join(project_root, "core", "config.json")

    # загружаем старый конфиг, чтобы не стереть настройки симулятора (fps, lambda и т.д.)
    if os.path.exists(config_json_path):
        with open(config_json_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    else:
        config_data = {"system_settings": {}}

    with open(csv_path, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)

        amount_idx = headers.index("amount")
        fraud_inx = headers.index("isFraud")
        step_idx = headers.index("step")  # номер часа

        total_tx_count = 0
        total_fraud_count = 0
        global_amounts_sum = 0.0
        hourly_stats = {}
        last_tx_type = 0
        tx_type_transitions = {i: {j: 0 for j in range(2)} for i in range(2)}

        for row in reader:
            if not row or len(row) <= max(amount_idx, fraud_inx, step_idx):
                continue
            try:
                amount = float(row[amount_idx])
                is_fraud = int(row[fraud_inx])
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
                hourly_stats[hour]["fraud_amount"] += amount
                hourly_stats[hour]["cnt_fraud"] += 1

            tx_type_transitions[last_tx_type][is_fraud] += 1
            last_tx_type = is_fraud

        global_average_amount = global_amounts_sum / total_tx_count if total_tx_count > 0 else 0.0

        matrix_3x3 = calculate_matrix_3x3(hourly_stats)
        matrix_2x2 = calculate_matrix_2x2(tx_type_transitions)

        # аккуратно обновляем только результаты анализа данных
        config_data["system_settings"]["dataset_avg_amount"] = global_average_amount
        config_data["markov_matrix_3x3"] = matrix_3x3
        config_data["markov_matrix_2x2"] = matrix_2x2

        with open(config_json_path, mode="w", encoding="utf-8") as json_file:
            json.dump(config_data, json_file, indent=4)

        print("средняя сумма перевода по датасету:", round(global_average_amount, 2))
        check_fraud_load_hypothesis(hourly_stats)
        analyze_top_fraud_hours(hourly_stats)
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
        if cnt > threshold_attack:
            hourly_modes[hour] = 2  # режим атаки
        elif cnt > threshold_peak:
            hourly_modes[hour] = 1  # пиковый режим
        else:
            hourly_modes[hour] = 0  # обычный режим

    transition_counts = {i: {j: 0 for j in range(3)} for i in range(3)}
    modes_list = [hourly_modes[h] for h in sorted(hourly_modes.keys())]
    for i in range(len(modes_list) - 1):
        current_mode = modes_list[i]
        next_mode = modes_list[i + 1]
        transition_counts[current_mode][next_mode] += 1

    markov_matrix_3x3 = {}
    for row_idx in range(3):
        row_sum = sum(transition_counts[row_idx].values())
        markov_matrix_3x3[str(row_idx)] = {
            str(col_idx): (transition_counts[row_idx][col_idx] / row_sum if row_sum > 0 else 0.0)
            for col_idx in range(3)
        }
    return markov_matrix_3x3


def calculate_matrix_2x2(tx_type_transitions: dict) -> dict:
    markov_fraud_matrix_2x2 = {}
    for row_idx in range(2):
        row_sum = sum(tx_type_transitions[row_idx].values())
        markov_fraud_matrix_2x2[str(row_idx)] = {
            str(col_idx): (tx_type_transitions[row_idx][col_idx] / row_sum if row_sum > 0 else 0.0)
            for col_idx in range(2)
        }
    return markov_fraud_matrix_2x2


def print_report(markov_matrix_3x3, markov_matrix_2x2) -> None:
    print("марковская матрица 3х3")
    state_names = {"0": "normal", "1": "peak", "2": "attack"}
    for i in range(3):
        p = markov_matrix_3x3[str(i)]
        print("из", state_names[str(i)], "-> на normal:", round(p["0"], 3), "| на peak:", round(p["1"], 3),
              "| на attack:", round(p["2"], 3))

    print("матрица 2х2")
    fraud_state_names = {"0": "чистая", "1": "фрод"}
    for i in range(2):
        p = markov_matrix_2x2[str(i)]
        print("из", fraud_state_names[str(i)], "-> на нормальную:", round(p["0"], 6), "/ на фрод:", round(p["1"], 6))


def check_fraud_load_hypothesis(hourly_stats: dict) -> None:
    print("проверка связи нагрузки и процента фрода")
    list_load_fraud_percent = []
    for hour, stats in hourly_stats.items():
        cnt = stats["cnt_per_hour"]
        if cnt == 0:
            continue
        fraud_percent = stats["cnt_fraud"] / cnt
        list_load_fraud_percent.append([cnt, fraud_percent])

    n = len(list_load_fraud_percent)
    if n < 2:
        print("мало данных")
        return

    mean_load = sum(pair[0] for pair in list_load_fraud_percent) / n
    mean_fraud = sum(pair[1] for pair in list_load_fraud_percent) / n
    numerator = 0.0
    sum_sq_load = 0.0
    sum_sq_fraud = 0.0

    for load, fraud_percent in list_load_fraud_percent:
        diff_load = load - mean_load
        diff_fraud = fraud_percent - mean_fraud
        numerator += diff_fraud * diff_load
        sum_sq_load += diff_load ** 2
        sum_sq_fraud += diff_fraud ** 2

    if sum_sq_fraud == 0 or sum_sq_load == 0:
        print("коэффициент пирсона 0")
        return

    person_r = numerator / math.sqrt(sum_sq_load * sum_sq_fraud)
    print("коэффициент пирсона:", round(person_r, 4))
    abs_r = abs(person_r)

    if abs_r < 0.1:
        print("линейная связь отсутствует")
    elif abs_r < 0.3:
        print("слабая линейная связь")
    elif abs_r < 0.5:
        print("умеренная линейная связь")
    else:
        print("сильная линейная связь")

    if person_r > 0.2:
        print("анализ: с ростом нагрузки растет доля фрода. мошенники бьют в часы пик.")
    elif person_r < -0.2:
        print("анализ: с ростом нагрузки доля фрода падает. мошенники растворяются в чистом трафике.")
    else:
        print("анализ: действия мошенников хаотичны и не связаны с графиком обычных пользователей.")


def analyze_top_fraud_hours(hourly_stats: dict, top_n: int = 10) -> None:
    if not hourly_stats:
        print("данных для анализа нет")
        return

    all_counts = sorted(stats["cnt_per_hour"] for stats in hourly_stats.values())
    total_hours = len(hourly_stats)
    idx_80 = int(total_hours * 0.8)
    threshold_peak = all_counts[idx_80] if total_hours > 0 else 0

    raw_hours_list = []
    for hour, stats in hourly_stats.items():
        cnt = stats["cnt_per_hour"]
        if cnt == 0:
            continue

        fraud_percent = (stats["cnt_fraud"] / cnt) * 100
        load_type = "обычная" if cnt <= threshold_peak else "пиковая"
        fraud_count = stats["cnt_fraud"]
        avg_fraud_amount = stats["fraud_amount"] / fraud_count if fraud_count > 0 else 0.0

        raw_hours_list.append({
            "hour": hour,
            "percent": fraud_percent,
            "fraud_tx": fraud_count,
            "avg_amount": avg_fraud_amount,
            "load": load_type
        })

    raw_hours_list.sort(key=lambda x: x["percent"], reverse=True)
    top_hours = raw_hours_list[:top_n]
    for item in top_hours:
        print("час", item['hour'], ": фрод составил", round(item['percent'], 2), "%, шт:", item['fraud_tx'],
              ", средняя сумма:", round(item['avg_amount'], 2), ", нагрузка:", item['load'])


if __name__ == "__main__":
    path_to_csv = "transactions.csv"

    print("Запуск анализа датасета...")
    run_dataset_analysis(path_to_csv)
    print("Анализ успешно завершен!")