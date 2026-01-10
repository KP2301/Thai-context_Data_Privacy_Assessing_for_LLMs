import re
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
from pathlib import Path

def interactive_percentage_plot(folder_path):
    if not os.path.exists(folder_path):
        print(f"❌ ไม่พบโฟลเดอร์: {folder_path}")
        return

    # --- ส่วนจัดการชื่อไฟล์สำหรับ Save ---
    # ดึงชื่อโฟลเดอร์สุดท้าย (เช่น 'casual') มาตั้งเป็นชื่อไฟล์
    folder_name = os.path.basename(os.path.normpath(folder_path))
    save_filename = f"{folder_name}_graph.png"
    save_path = os.path.join(folder_path, save_filename)
    # ----------------------------------

    # หาไฟล์ที่ขึ้นต้นด้วย "token_counted_" ในโฟลเดอร์
    files = list(Path(folder_path).glob("token_counted_*.txt"))
    
    if not files:
        print(f"⚠ ไม่พบไฟล์ที่ขึ้นต้นด้วย 'token_counted_' ในโฟลเดอร์: {folder_path}")
        return
    
    model_data = {}
    max_token_overall = 0
    
    for file_path in files:
        model_name = file_path.stem.replace("token_counted_", "")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        pattern = re.compile(r'STATUS:.*?(✅|❌).*?PROMPT TOKENS: (\d+)', re.DOTALL)
        matches = pattern.findall(content)
        
        all_data = []
        for status_icon, token_count in matches:
            is_success = 1 if status_icon == "✅" else 0
            all_data.append((int(token_count), is_success))

        if not all_data:
            continue
        
        all_tokens = np.array([d[0] for d in all_data])
        success_flags = np.array([d[1] for d in all_data])
        max_token_overall = max(max_token_overall, max(all_tokens))
        
        model_data[model_name] = {
            'tokens': all_tokens,
            'success': success_flags,
            'total': len(all_data)
        }
    
    if not model_data:
        print("❌ ไม่มีข้อมูลที่ใช้งานได้")
        return
    
    # ตั้งค่ากราฟ
    initial_bin_size = 1000
    fig, ax = plt.subplots(figsize=(14, 8))
    plt.subplots_adjust(bottom=0.25)
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#06A77D', '#D62828', '#8338EC']
    
    # แยกฟังก์ชันวาดกราฟออกมาเพื่อให้เรียกใช้ได้ทั้งตอน Save และตอน Update
    def draw_plot_content(bin_size):
        ax.clear()
        bin_size = int(bin_size)
        bins = np.arange(0, max_token_overall + bin_size + 1, bin_size)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        for idx, (model_name, data) in enumerate(model_data.items()):
            all_tokens = data['tokens']
            success_flags = data['success']
            total_counts, _ = np.histogram(all_tokens, bins=bins)
            success_counts, _ = np.histogram(all_tokens[success_flags == 1], bins=bins)
            
            percentages = [(s / t * 100) if t > 0 else np.nan for s, t in zip(success_counts, total_counts)]
            color = colors[idx % len(colors)]
            ax.plot(bin_centers, percentages, marker='o', linewidth=2.5, 
                   label=f"{model_name} (n={data['total']})", 
                   color=color, markersize=6, alpha=0.8)
        
        ax.set_title(f'DEA Accuracy (%) by Token Range - {folder_name.capitalize()}', 
                    fontsize=15, fontweight='bold', pad=20)
        ax.set_xlabel('Token Range (midpoint)', fontsize=13)
        ax.set_ylabel('DEA Accuracy (%)', fontsize=13)
        ax.set_ylim(0, 80)
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.legend(loc='best', fontsize=10, framealpha=0.9)
        
        labels = [f"{int(bins[i])}-{int(bins[i+1])}" for i in range(len(bins)-1)]
        ax.set_xticks(bin_centers)
        ax.set_xticklabels(labels, fontsize=9)

    # 1. วาดเนื้อหาครั้งแรก
    draw_plot_content(initial_bin_size)
    
    # 2. บันทึกรูปภาพ (บันทึกตอนนี้ Slider จะยังไม่ปรากฏในรูป)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ บันทึกรูปภาพเรียบร้อยแล้ว: {save_path}")

    # 3. สร้าง Slider สำหรับการใช้งาน Interactive
    ax_slider = plt.axes([0.2, 0.08, 0.6, 0.03])
    slider = Slider(ax=ax_slider, label='Adjust Bin Size  ', valmin=50, valmax=2000, 
                    valinit=initial_bin_size, valstep=50, color='steelblue')
    
    def update(val):
        draw_plot_content(val)
        fig.canvas.draw_idle()
    
    slider.on_changed(update)
    
    print("\n✅ กราฟ Interactive พร้อมทำงาน!")
    plt.show()

# Path ของโฟลเดอร์
target_folder_path = r"./"
interactive_percentage_plot(target_folder_path)