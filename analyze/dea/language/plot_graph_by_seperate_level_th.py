import os
import re
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'sans-serif'


def extract_asr_from_file(filepath):
    """
    อ่านไฟล์และดึงค่า ASR (Attack Success Rate) และ Total Success จากไฟล์
    Returns: (asr_percentage, success_count, total_count) หรือ (None, None, None)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

            asr_match = re.search(
                r'Overall Success Rate \(ASR\):\s*(\d+\.?\d*)%',
                content
            )
            total_match = re.search(
                r'Total Success:\s*(\d+)\s*/\s*(\d+)',
                content
            )

            if asr_match and total_match:
                asr = float(asr_match.group(1))
                success = int(total_match.group(1))
                total = int(total_match.group(2))
                return asr, success, total
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

    return None, None, None


def create_dea_accuracy_chart(base_folder_path,
                              output_filename='dea_accuracy_comparison_th.png'):
    # =========================
    # Config
    # =========================
    models = ['llama', 'meta', 'kimi']
    language_levels = ['ceremonial', 'formal', 'semi_formal', 'informal', 'casual']

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
    # เตรียมโครงสร้างข้อมูล
    # data[level][round][model] = {'asr', 'success', 'total'}
    # =========================
    data = {
        level: {
            round_name: {
                model: {'asr': 0, 'success': 0, 'total': 0}
                for model in models
            }
            for round_name in rounds
        }
        for level in language_levels
    }

    # =========================
    # อ่านไฟล์ทุก round / level / model
    # path: base_folder/round1/language/casual/kimi.txt
    # =========================
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
                        data[level][round_name][model]['asr'] = asr
                        data[level][round_name][model]['success'] = success
                        data[level][round_name][model]['total'] = total
                        print(f"{round_name} | {level} | {model}: {asr}% ({success}/{total})")
                    else:
                        print(f"Warning: อ่าน ASR ไม่ได้ใน {filepath}")
                else:
                    print(f"Warning: ไม่พบไฟล์ {filepath}")

    # =========================
    # สร้าง chart แยกตามระดับภาษา (5 charts)
    # =========================
    base_name, ext = os.path.splitext(output_filename)
    ext = ext if ext else '.png'

    for level in language_levels:
        fig, ax = plt.subplots(figsize=(14, 8))

        x = range(len(rounds))
        bar_width = 0.25

        # วาดแท่งกราฟ
        for i, model in enumerate(models):
            positions = [pos + (i - 1) * bar_width for pos in x]

            values      = [data[level][r][model]['asr']     for r in rounds]
            success_vals = [data[level][r][model]['success'] for r in rounds]
            total_vals   = [data[level][r][model]['total']   for r in rounds]

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
            for bar, val, s, t in zip(bars, values, success_vals, total_vals):
                if val > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height(),
                        f"{val:.2f}%\n({s}/{t})",
                        ha='center',
                        va='bottom',
                        fontsize=8,
                        fontweight='bold'
                    )

        # คำนวณค่าเฉลี่ย
        avg_text_parts = []
        for model in models:
            total_asr = sum(
                data[level][r][model]['asr']
                for r in rounds
                if data[level][r][model]['asr'] > 0
            )
            round_count = sum(
                1 for r in rounds
                if data[level][r][model]['asr'] > 0
            )
            avg_val = total_asr / round_count if round_count > 0 else 0
            avg_text_parts.append(f"{model.upper()}: {avg_val:.2f}%")

        avg_text = "Average ASR (All Rounds) →  " + "   ".join(avg_text_parts)

        # ตั้งค่ากราฟ
        ax.set_xlabel("Round", fontsize=13, fontweight='bold')
        ax.set_ylabel("DEA Accuracy (%)", fontsize=13, fontweight='bold')
        ax.set_title(
            f"DEA Accuracy per Round (TH - {level.replace('_', ' ').title()})",
            fontsize=15, fontweight='bold', pad=20
        )

        ax.set_xticks(list(x))
        ax.set_xticklabels(rounds, fontsize=11)
        ax.legend(fontsize=11)
        ax.grid(axis='y', linestyle='--', alpha=0.3)

        all_asr = [data[level][r][m]['asr'] for r in rounds for m in models]
        max_asr = max(all_asr) if any(v > 0 for v in all_asr) else 100
        ax.set_ylim(0, max_asr * 1.25 if max_asr > 0 else 100)

        fig.text(
            0.5, 0.02,
            avg_text,
            ha='center',
            fontsize=11,
            fontweight='bold'
        )

        plt.tight_layout(rect=[0, 0.05, 1, 1])

        # บันทึกไฟล์แยกตาม level
        save_path = os.path.join(
            base_folder_path,
            f"{base_name}_{level}{ext}"
        )
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"กราฟถูกบันทึก: {save_path}")
        plt.show()


base_folder = r"D:\CMU\Y4\Project\LLM-PBE_VS\dea_result\without_defence\final_results\th"
create_dea_accuracy_chart(base_folder, output_filename='dea_accuracy_comparison_th.png')