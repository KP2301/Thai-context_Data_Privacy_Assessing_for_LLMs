import re
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = re.compile(r'STATUS:.*?(✅|❌).*?PROMPT WORDS: (\d+)', re.DOTALL)
    matches = pattern.findall(content)
    if not matches:
        return None
    return [(int(word_count), 1 if status_icon == "✅" else 0) for status_icon, word_count in matches]

def interactive_combined_line_plot(folder_path):
    print(f"📂 กำลังรวบรวมข้อมูลจากโฟลเดอร์: {folder_path}")
    
    files = [f for f in os.listdir(folder_path) if f.startswith("word_counted_") and f.endswith(".txt")]
    if not files:
        print("❌ ไม่พบไฟล์ที่ตรงตามเงื่อนไข (word_counted_*.txt)")
        return

    all_files_data = {}
    global_max_word = 0

    for file_name in files:
        full_path = os.path.join(folder_path, file_name)
        data = process_file(full_path)
        if data:
            all_files_data[file_name] = data
            max_in_file = max(d[0] for d in data)
            if max_in_file > global_max_word:
                global_max_word = max_in_file

    # ตั้งค่า Figure
    fig, ax = plt.subplots(figsize=(14, 8))
    plt.subplots_adjust(bottom=0.20) 

    initial_bin_size = 500
    
    # สร้าง Slider ไว้ก่อนเพื่อให้ฟังก์ชัน update_graph เรียกใช้การซ่อนได้
    ax_slider = plt.axes([0.25, 0.05, 0.5, 0.03])
    slider = Slider(ax=ax_slider, label='Bin Size ', valmin=50, valmax=1000, valinit=initial_bin_size, valstep=50, color='skyblue')

    def update_graph(bin_size, is_saving=False):
        ax.clear()
        bin_size = int(bin_size)
        bins = np.arange(0, global_max_word + bin_size + 1, bin_size)
        labels = [f"{int(bins[i])}-{int(bins[i+1])}" for i in range(len(bins)-1)]
        x_indices = np.arange(len(labels))

        for file_name, data in all_files_data.items():
            all_words = np.array([d[0] for d in data])
            success_flags = np.array([d[1] for d in data])
            
            total_counts, _ = np.histogram(all_words, bins=bins)
            success_counts, _ = np.histogram(all_words[success_flags == 1], bins=bins)
            
            percentages = []
            for s, t in zip(success_counts, total_counts):
                percentages.append(s / t * 100 if t > 0 else None)

            mask = [p is not None for p in percentages]
            filtered_x = x_indices[mask]
            filtered_y = [p for p in percentages if p is not None]

            display_name = file_name.replace("word_counted_", "").replace(".txt", "")
            ax.plot(filtered_x, filtered_y, marker='o', label=display_name, linewidth=2)

        ax.set_title(f'DEA Accuracy (%) by Word Count Range - {os.path.basename(folder_path)}', fontsize=14)
        ax.set_xlabel('Word Count Range', fontsize=13)
        ax.set_ylabel('DEA Accuracy (%)', fontsize=13)
        ax.set_xticks(x_indices)
        ax.set_xticklabels(labels)
        ax.set_ylim(-5, 105)
        ax.grid(True, linestyle='--', alpha=0.6)
        
        # Legend ขวาบนในกราฟ
        ax.legend(title="Datasets", loc='upper right', fontsize=10, framealpha=0.9)
        
        if not is_saving:
            fig.canvas.draw_idle()

    # ฟังก์ชันสำหรับ Save โดยไม่เอา Slider
    def save_plot(folder_path):
        ax_slider.set_visible(False) # ซ่อน slider
        update_graph(slider.val, is_saving=True)
        save_path = os.path.join(folder_path, f"{os.path.basename(folder_path)}_dea_accuracy_word_count.png")
        plt.savefig(save_path, bbox_inches='tight', dpi=300)
        ax_slider.set_visible(True) # แสดง slider กลับมา
        print(f"✅ บันทึกรูปภาพเรียบร้อยแล้วที่: {save_path}")

    slider.on_changed(lambda val: update_graph(val))
    
    # รันครั้งแรก
    update_graph(initial_bin_size)
    save_plot(folder_path) # บันทึกรูปทันทีที่เปิดโปรแกรม
    
    ax_slider._slider = slider
    plt.show()

# --- เรียกใช้งาน ---
target_folder = r"D:\CMU\Y4\LLM-PBE_VS\dea_result\prefix\results\length\casual"
interactive_combined_line_plot(target_folder)