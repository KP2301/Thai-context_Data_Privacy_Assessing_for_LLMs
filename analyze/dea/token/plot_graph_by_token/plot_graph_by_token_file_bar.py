import re
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np

def interactive_percentage_plot(file_path):
    if not os.path.exists(file_path):
        print(f"❌ ไม่พบไฟล์: {file_path}")
        return

    # --- ส่วนดึงชื่อไฟล์และจัดรูปแบบใหม่ ---
    base_name = os.path.basename(file_path)
    file_name_without_ext = os.path.splitext(base_name)[0]
    new_name = file_name_without_ext.replace("token_counted_", "") + "_graph"
    
    folder_path = os.path.dirname(file_path)
    save_path = os.path.join(folder_path, f"{new_name}.png")

    print(f"📖 กำลังอ่านไฟล์: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = re.compile(r'STATUS:.*?(✅|❌).*?PROMPT TOKENS: (\d+)', re.DOTALL)
    matches = pattern.findall(content)
    
    all_data = []
    for status_icon, token_count in matches:
        is_success = 1 if status_icon == "✅" else 0
        all_data.append((int(token_count), is_success))

    if not all_data:
        print("⚠ ไม่พบข้อมูลในไฟล์")
        return

    all_tokens = np.array([d[0] for d in all_data])
    success_flags = np.array([d[1] for d in all_data])
    max_token_val = max(all_tokens)

    # --- เตรียม Figure ---
    initial_bin_size = 1000
    fig, ax = plt.subplots(figsize=(13, 7))
    # เว้นที่ด้านล่างไว้สำหรับ Slider (แต่จะยังไม่สร้าง Slider ตอนบันทึก)
    plt.subplots_adjust(bottom=0.25)

    # ฟังก์ชันวาดกราฟ (แยกออกมาเพื่อให้เรียกใช้ได้ทั้งตอนเริ่มและตอนเลื่อน Slider)
    def draw_content(bin_size):
        ax.clear()
        bin_size = int(bin_size)
        bins = np.arange(0, max_token_val + bin_size + 1, bin_size)
        
        total_counts, _ = np.histogram(all_tokens, bins=bins)
        success_counts, _ = np.histogram(all_tokens[success_flags == 1], bins=bins)
        
        percentages = [(s / t * 100) if t > 0 else 0 for s, t in zip(success_counts, total_counts)]
        labels = [f"{int(bins[i])}-{int(bins[i+1])}" for i in range(len(bins)-1)]
        
        bars = ax.bar(labels, percentages, color='mediumseagreen', edgecolor='darkgreen', alpha=0.7)
        
        ax.set_title(f'DEA Accuracy (%) by Token Range\n(Length: {len(all_data)})', fontsize=14, pad=20)
        ax.set_xlabel('Token Range', fontsize=12)
        ax.set_ylabel('DEA Accuracy (%)', fontsize=12)
        ax.set_ylim(0, max(percentages) + 5 if percentages and max(percentages) > 0 else 100)
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        for i, bar in enumerate(bars):
            height = bar.get_height()
            if total_counts[i] > 0:
                label_text = f"{height:.1f}%\n({success_counts[i]}/{total_counts[i]})"
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                        label_text, ha='center', va='bottom', fontsize=8, fontweight='bold')

    # 1. วาดกราฟครั้งแรก (ขนาด Bin เริ่มต้น)
    draw_content(initial_bin_size)
    
    # 2. บันทึกรูปภาพทันที (ตอนนี้ยังไม่มี Slider ใน Figure)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ บันทึกรูปภาพ (แบบไม่มี Slider) เรียบร้อยที่: {save_path}")

    # 3. หลังจากบันทึกเสร็จ ค่อยสร้าง Slider ลงไปใน Figure เพื่อใช้งานหน้าจอ
    ax_slider = plt.axes([0.2, 0.05, 0.6, 0.03])
    slider = Slider(ax=ax_slider, label='Adjust Bin Size  ', valmin=50, valmax=2000, 
                    valinit=initial_bin_size, valstep=50, color='mediumseagreen')

    def update(val):
        draw_content(val)
        fig.canvas.draw_idle()

    slider.on_changed(update)

    print("✅ กราฟ Interactive พร้อมทำงาน (Slider จะปรากฏเฉพาะในโปรแกรม)!")
    plt.show()

# Path ของไฟล์
target_file_path = r"D:\CMU\Y4\LLM-PBE_VS\dea_result\results_editted\token\semi-formal\token_counted_semi_formal_meta.txt"
interactive_percentage_plot(target_file_path)