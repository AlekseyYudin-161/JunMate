"""Скрипт оценки качества JunMate (Accuracy, Grounding, Latency)."""

import json
import os
import sys
import time
from collections import Counter

# Добавляем корень проекта в sys.path для импортов
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from agents.parser import parse_resume
from agents.track import classify_track
from agents.rewriter import rewrite_resume
from agents.critic import critique_resume


ONLY_IDS = None

def load_dataset():
    with open("eval/labels.json", "r", encoding="utf-8") as f:
        labels = json.load(f)

    dataset = []
    for item in labels:
        if ONLY_IDS is not None and item["id"] not in ONLY_IDS:   # фильтр
            continue
        file_path = os.path.join("eval/dataset", item["file"])
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            dataset.append({
                "id": item["id"],
                "text": text,
                "true_track": item["true_track"]
            })
    return dataset


def run_eval():
    dataset = load_dataset()
    print(f"--- Загружено {len(dataset)} резюме ---\n")

    track_results = []
    grounding_results = []
    latencies = {"A1": [], "A2": [], "A5": [], "A6": []}

    # --- ШАГ 3: ACCURACY ТРЕКА ---
    print("--- ШАГ 3: Оценка точности трека (2 прогона) ---")
    print(f"{'id':<15} | {'True Track':<12} | {'Run 1':<12} | {'Run 2':<12} | {'Match'}")
    print("-" * 70)

    correct_runs = 0
    total_runs = 0
    stable_count = 0
    confusion = Counter()

    for item in dataset:
        runs = []
        for i in range(2):
            try:
                # A1: Parser
                start = time.time()
                profile = parse_resume(item["text"])
                latencies["A1"].append(time.time() - start)

                # A2: Track
                start = time.time()
                track_res = classify_track(profile)
                latencies["A2"].append(time.time() - start)

                pred_track = track_res.track
                runs.append(pred_track)

                if pred_track == item["true_track"]:
                    correct_runs += 1
                else:
                    confusion[f"{item['true_track']} -> {pred_track}"] += 1
                total_runs += 1
            except Exception as e:
                print(f"Ошибка на {item['id']} (прогон {i+1}): {e}")
                runs.append("ERROR")

        match_str = "✅" if runs[0] == runs[1] == item["true_track"] else "❌"
        if runs[0] == runs[1] and runs[0] != "ERROR":
            stable_count += 1

        print(f"{item['id']:<15} | {item['true_track']:<12} | {runs[0]:<12} | {runs[1]:<12} | {match_str}")
        track_results.append({"id": item["id"], "runs": runs, "true": item["true_track"]})

    # --- ШАГ 4: GROUNDING (только ivan, dudii, ilia) ---
    print("\n--- ШАГ 4: Grounding (галлюцинации) ---")
    target_ids = {"ivan", "dudii", "ilia"}
    grounding_ok_count = 0

    print(f"{'id':<15} | {'Grounding OK':<12} | {'Fabricated Claims'}")
    print("-" * 70)

    for item in dataset:
        if item["id"] not in target_ids:
            continue

        try:
            # A1
            profile = parse_resume(item["text"])
            # A5
            start = time.time()
            resume = rewrite_resume(profile, item["true_track"], gap=None, history=[])
            latencies["A5"].append(time.time() - start)
            # A6
            start = time.time()
            critique = critique_resume(profile, history=[], content_markdown=resume.content_markdown)
            latencies["A6"].append(time.time() - start)

            if critique.grounding_ok:
                grounding_ok_count += 1

            claims = ", ".join(critique.fabricated_claims) if critique.fabricated_claims else "None"
            print(f"{item['id']:<15} | {str(critique.grounding_ok):<12} | {claims}")
            grounding_results.append(critique.grounding_ok)
        except Exception as e:
            print(f"Ошибка Grounding на {item['id']}: {e}")

    # --- ИТОГИ ---
    print("\n=== ИТОГ ДЛЯ EVAL_RESULTS ===")
    acc = (correct_runs / total_runs * 100) if total_runs > 0 else 0
    stability = (stable_count / len(dataset) * 100) if dataset else 0
    gr_rate = f"{grounding_ok_count}/{len(grounding_results)}" if grounding_results else "0/0"

    avg_lat = {k: (sum(v)/len(v) if v else 0) for k, v in latencies.items()}

    print(f"Accuracy трека: {correct_runs}/{total_runs} = {acc:.1f}%")
    print(f"Доля стабильных (2 совпали): {stability:.1f}%")
    print(f"Grounding-rate: {gr_rate}")
    print(f"Средняя latency: A1={avg_lat['A1']:.1f}s, A2={avg_lat['A2']:.1f}s, A5={avg_lat['A5']:.1f}s, A6={avg_lat['A6']:.1f}s")

    if confusion:
        print("\nConfusion Matrix (топ ошибок):")
        for pair, count in confusion.most_common(5):
            print(f"  {pair}: {count}")

if __name__ == "__main__":
    run_eval()
