import os
import re
import glob
import numpy as np
import matplotlib.pyplot as plt

# Base paths
# base_th = r"E:\project-Backup\LLM-PBE_VS\ja_result\without_defence\th"
# base_eng = r"E:\project-Backup\LLM-PBE_VS\ja_result\without_defence\eng"
# base_th = r"E:\project-Backup\LLM-PBE_VS\ja_result\defence\scrub\th"
# base_eng = r"E:\project-Backup\LLM-PBE_VS\ja_result\defence\scrub\eng"
base_th = r"E:\project-Backup\LLM-PBE_VS\ja_result\defence\defensive_prompt\th"
base_eng = r"E:\project-Backup\LLM-PBE_VS\ja_result\defence\defensive_prompt\eng"

# Thai style folders
th_styles = ["ceremonial", "formal", "semi_formal", "informal", "casual"]
rounds = ["round1", "round2", "round3", "round4", "round5"]

# Model definitions: (short_name, filename_prefix)
models = [
    ("Llama",  "ja_output_llama-3.1-8b-instant"),
    ("Meta",   "ja_output_meta-llama_llama-4-maverick-17b-128e-instruct"),
    ("Kimi",   "ja_output_moonshotai_kimi-k2-instruct-0905"),
]

def extract_rate(filepath):
    """Extract Rate percentage(s) from a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        matches = re.findall(r"Rate\s*:\s*([\d.]+)%", content)
        return [float(m) for m in matches]
    except Exception as e:
        print(f"[ERROR] Cannot read {filepath}: {e}")
        return []

# ── Collect Thai rates ──────────────────────────────────────────────────────
# th_rates[style][model_short] = [list of rates]
th_rates = {style: {m[0]: [] for m in models} for style in th_styles}

for rnd in rounds:
    for style in th_styles:
        folder = os.path.join(base_th, rnd, style)
        if not os.path.exists(folder):
            print(f"[WARN] Folder not found: {folder}")
            continue
        for short, prefix in models:
            # Match prefix + anything + .txt  (e.g. prefix_casual.txt)
            pattern = os.path.join(folder, f"{prefix}*.txt")
            files = glob.glob(pattern)
            for f in files:
                rates = extract_rate(f)
                th_rates[style][short].extend(rates)

# ── Collect English rates ───────────────────────────────────────────────────
# eng_rates[model_short] = [list of rates]
eng_rates = {m[0]: [] for m in models}

for rnd in rounds:
    folder = os.path.join(base_eng, rnd)
    if not os.path.exists(folder):
        print(f"[WARN] Folder not found: {folder}")
        continue
    for short, prefix in models:
        # Exact filename for English (no suffix after prefix)
        filepath = os.path.join(folder, f"{prefix}.txt")
        if os.path.exists(filepath):
            rates = extract_rate(filepath)
            eng_rates[short].extend(rates)
        else:
            print(f"[WARN] File not found: {filepath}")

# ── Compute averages ────────────────────────────────────────────────────────
print("\n=== Average Jailbreak Rates ===")

# th_avgs[style][model_short] = avg %
th_avgs = {}
for style in th_styles:
    th_avgs[style] = {}
    for short, _ in models:
        vals = th_rates[style][short]
        avg = np.mean(vals) if vals else 0.0
        th_avgs[style][short] = avg
        print(f"[TH] {style:12s} | {short:6s} : {len(vals):3d} values -> {avg:.2f}%")

eng_avgs = {}
for short, _ in models:
    vals = eng_rates[short]
    avg = np.mean(vals) if vals else 0.0
    eng_avgs[short] = avg
    print(f"[ENG]              | {short:6s} : {len(vals):3d} values -> {avg:.2f}%")

# ── Plot Clustered Bar Chart ────────────────────────────────────────────────
group_labels = ["Ceremonial", "Formal", "Semi_formal", "Informal", "Casual", "Eng"]
model_names  = [m[0] for m in models]   # ["Llama", "Meta", "Kimi"]

# Build value matrix [3 models x 6 groups]
values = np.zeros((len(model_names), len(group_labels)))
for gi, style in enumerate(th_styles):
    for mi, short in enumerate(model_names):
        values[mi, gi] = th_avgs[style][short]
for mi, short in enumerate(model_names):
    values[mi, 5] = eng_avgs[short]

# Colors per model
model_colors = {
    "Llama": "#FF6B6B",
    "Meta":  "#45B7D1",
    "Kimi":  "#4ECDC4",
}

n_groups = len(group_labels)
n_models = len(model_names)
x = np.arange(n_groups)
bar_width = 0.22
offsets = np.linspace(-(n_models - 1) / 2, (n_models - 1) / 2, n_models) * bar_width

fig, ax = plt.subplots(figsize=(14, 7))

for mi, short in enumerate(model_names):
    bars = ax.bar(
        x + offsets[mi],
        values[mi],
        width=bar_width,
        label=short,
        color=model_colors[short],
        edgecolor="white",
        linewidth=0.7,
    )
    for bar, val in zip(bars, values[mi]):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.4,
            f"{val:.1f}%",
            ha="center", va="bottom", fontsize=7.5, fontweight="bold",
            rotation=90,
        )

# Separator line between TH and ENG groups
ax.axvline(x=4.5, color="gray", linestyle="--", linewidth=1.2, alpha=0.7)
ax.text(4.55, ax.get_ylim()[1] * 0.98 if ax.get_ylim()[1] > 0 else 5,
        "ENG →", fontsize=9, color="gray", va="top")

ax.set_xticks(x)
ax.set_xticklabels(group_labels, fontsize=12)
ax.set_xlabel("Language / Register Level", fontsize=13)
ax.set_ylabel("Average Jailbreak Rate (%)", fontsize=13)
ax.set_title(
    # "Average Jailbreak Rate by Language Register & Model (5 Rounds, Without Defence)",
    # "Average Jailbreak Rate by Language Register & Model (5 Rounds, With Scrubbing Defence)",
    "Average Jailbreak Rate by Language Register & Model (5 Rounds, With Defensive Prompt Defence)",
    fontsize=13, fontweight="bold"
)
ax.yaxis.grid(True, linestyle="--", alpha=0.6)
ax.set_axisbelow(True)
ax.legend(title="Model", fontsize=11, title_fontsize=11)

max_val = values.max()
ax.set_ylim(0, 32.1 * 1.35 + 5)

plt.tight_layout()
plt.savefig("jailbreak_rate_clustered.png", dpi=150)
plt.show()
print("\nGraph saved as jailbreak_rate_clustered.png")