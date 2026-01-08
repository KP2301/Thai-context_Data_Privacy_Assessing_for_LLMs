import re
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np

def interactive_word_percentage_plot(file_path):
    print(f"📖 กำลังวิเคราะห์ข้อมูลคำจาก: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # ดึง STATUS และ PROMPT WORDS
    pattern = re.compile(r'STATUS:.*?(✅|❌).*?PROMPT WORDS: (\d+)', re.DOTALL)
    matches = pattern.findall(content)
    
    all_data = []
    for status_icon, word_count in matches:
        all_data.append((int(word_count), 1 if status_icon == "✅" else 0))

    all_words = np.array([d[0] for d in all_data])
    success_flags = np.array([d[1] for d in all_data])
    max_word_val = max(all_words)

    initial_bin_size = 50 # จำนวนคำมักจะน้อยกว่าจำนวน token เลยตั้งค่าเริ่มต้นเล็กลง
    fig, ax = plt.subplots(figsize=(13, 7))
    plt.subplots_adjust(bottom=0.25)

    def update_graph(bin_size):
        ax.clear()
        bin_size = int(bin_size)
        bins = np.arange(0, max_word_val + bin_size + 1, bin_size)
        
        total_counts, _ = np.histogram(all_words, bins=bins)
        success_counts, _ = np.histogram(all_words[success_flags == 1], bins=bins)
        
        percentages = [(s / t * 100) if t > 0 else 0 for s, t in zip(success_counts, total_counts)]
        labels = [f"{int(bins[i])}-{int(bins[i+1])}" for i in range(len(bins)-1)]
        
        bars = ax.bar(labels, percentages, color='orchid', edgecolor='purple', alpha=0.7)
        ax.set_title(f'DEA Accuracy (%) by Word Count (Thai Tokenization)\nTotal Samples: {len(all_data)}', fontsize=14)
        ax.set_xlabel('Word Count Range', fontsize=12)
        ax.set_ylabel('DEA Accuracy (%)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        ax.set_ylim(0, max(percentages) + 10 if percentages and max(percentages) > 0 else 100)
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        for i, bar in enumerate(bars):
            height = bar.get_height()
            if total_counts[i] > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        f"{height:.1f}%\n({success_counts[i]}/{total_counts[i]})", 
                        ha='center', va='bottom', fontsize=8)
        fig.canvas.draw_idle()

    ax_slider = plt.axes([0.2, 0.05, 0.6, 0.03])
    slider = Slider(ax=ax_slider, label='Bin Size (Words) ', valmin=10, valmax=500, valinit=initial_bin_size, valstep=10, color='orchid')
    slider.on_changed(update_graph)
    update_graph(initial_bin_size)
    plt.show()

# เรียกใช้งาน
target_file_path = r"C:\Project\LLM-PBE_VS\dea_result\prefix\th\casual\word_counted_token_counted_FINAL_TOTAL_REPORT.txt"
interactive_word_percentage_plot(target_file_path)