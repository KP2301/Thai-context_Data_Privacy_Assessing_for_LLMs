import os
import re
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'sans-serif'


def extract_asr_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

            asr_match = re.search(
                # r'Overall Success Rate \(ASR\):\s*(\d+\.?\d*)%',
                r'ASR\s*\(Success Rate\)\s*:\s*(\d+(?:\.\d+)?)\s*%',
                content
            )
            leaked_match = re.search(
                # r'Total Success:\s*(\d+)\s*/\s*(\d+)',
                r'TOTAL\s+LEAKED\s*:\s*(\d+)',
                content
            )
            total_match = re.search(
                r'TOTAL\s+PROCESSED\s*:\s*(\d+)',
                content,
                re.IGNORECASE
            )

            if asr_match and leaked_match and total_match:
                asr = float(asr_match.group(1))
                success = int(leaked_match.group(1))
                total = int(total_match.group(1))
                return asr, success, total

            # asr_match = re.search(
            #     r'Overall Success Rate \(ASR\):\s*(\d+\.?\d*)%',
            #     content
            # )
            # total_match = re.search(
            #     r'Total Success:\s*(\d+)\s*/\s*(\d+)',
            #     content
            # )

            # if asr_match and total_match:
            #     asr = float(asr_match.group(1))
            #     success = int(total_match.group(1))
            #     total = int(total_match.group(2))
            #     return asr, success, total
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

    return None, None, None


def create_dea_avg_chart(base_folder_path,
                         output_filename='dea_accuracy_avg_th.png'):
    # =========================
    # Config
    # =========================
    models = ['llama', 'meta', 'kimi']
    language_levels = ['ceremonial', 'formal', 'semi_formal', 'informal', 'casual', 'eng']
    level_labels = ['Ceremonial', 'Formal', 'Semi Formal', 'Informal', 'Casual', 'English']

    colors = {
        'llama': '#FF6B6B',
        'meta': '#45B7D1',
        'kimi': '#4ECDC4'
    }

    # =========================
    # หา round ทั้งหมด
    # =========================
    rounds = sorted([
        d for d in os.listdir(base_folder_path)
        if os.path.isdir(os.path.join(base_folder_path, d))
        and d.lower().startswith("round")
    ])

    if not rounds:
        print("Error: ไม่พบโฟลเดอร์ round ใดๆ")
        return

    print(f"พบรอบทั้งหมด: {rounds}")

    # =========================
    # อ่านไฟล์และเก็บ ASR ทุก round
    # raw[level][model] = [asr_round1, asr_round2, ...]
    # =========================
    raw = {
        level: {model: [] for model in models}
        for level in language_levels
    }

    for round_name in rounds:
        for level in language_levels:
            for model in models:
                filepath = os.path.join(
                    base_folder_path,
                    round_name,
                    'language',
                    level,
                    f"{model}.txt"
                )

                if os.path.exists(filepath):
                    asr, success, total = extract_asr_from_file(filepath)
                    if asr is not None:
                        raw[level][model].append(asr)
                        print(f"{round_name} | {level} | {model}: {asr}% ({success}/{total})")
                    else:
                        print(f"Warning: อ่าน ASR ไม่ได้ใน {filepath}")
                else:
                    print(f"Warning: ไม่พบไฟล์ {filepath}")

    # =========================
    # คำนวณค่าเฉลี่ยต่อ level ต่อ model
    # avg[level][model] = mean ASR across all rounds
    # =========================
    avg = {
        level: {
            model: (sum(raw[level][model]) / len(raw[level][model])
                    if raw[level][model] else 0)
            for model in models
        }
        for level in language_levels
    }

    # =========================
    # Plot กราฟเดียว
    # =========================
    fig, ax = plt.subplots(figsize=(14, 7))

    x = range(len(language_levels))
    bar_width = 0.25

    for i, model in enumerate(models):
        positions = [pos + (i - 1) * bar_width for pos in x]
        values = [avg[level][model] for level in language_levels]

        bars = ax.bar(
            positions,
            values,
            bar_width,
            label=model.upper(),
            color=colors[model],
            edgecolor='black',
            alpha=0.85
        )

        # ใส่ label บนแท่ง
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f"{val:.2f}%",
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    fontweight='bold'
                )

    # =========================
    # Overall average ต่อ model (เฉลี่ยจากทุก level)
    # =========================
    overall_parts = []
    for model in models:
        all_vals = [avg[level][model] for level in language_levels if avg[level][model] > 0]
        overall = sum(all_vals) / len(all_vals) if all_vals else 0
        overall_parts.append(f"{model.upper()}: {overall:.2f}%")

    overall_text = "Overall Average ASR →  " + "   ".join(overall_parts)

    # =========================
    # ตั้งค่ากราฟ
    # =========================
    ax.set_xlabel("Language Level", fontsize=13, fontweight='bold')
    ax.set_ylabel("Average ASR (%)", fontsize=13, fontweight='bold')
    ax.set_title(
        f"Average DEA Accuracy by Language Level (TH vs ENG, {len(rounds)} Rounds)",
        fontsize=15, fontweight='bold', pad=20
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels(level_labels, fontsize=11)
    ax.legend(fontsize=11)
    ax.grid(axis='y', linestyle='--', alpha=0.3)

    all_vals_flat = [avg[lv][m] for lv in language_levels for m in models]
    max_asr = max(all_vals_flat) if any(v > 0 for v in all_vals_flat) else 100
    ax.set_ylim(0, max_asr * 1.25 if max_asr > 0 else 100)
    # ax.set_ylim(0, 5) # same height as without defense

    fig.text(
        0.5, 0.02,
        overall_text,
        ha='center',
        fontsize=11,
        fontweight='bold'
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])

    save_path = os.path.join(base_folder_path, output_filename)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nกราฟถูกบันทึก: {save_path}")
    plt.show()


base_folder = r"D:\CMU\Y4\Project\LLM-PBE_VS\dea_result\defence\defensive_prompt\th"
create_dea_avg_chart(base_folder, output_filename='dea_accuracy_avg_th.png')