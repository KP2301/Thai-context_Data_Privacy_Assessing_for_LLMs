import re
import os
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np

def interactive_percentage_plot(file_path):
    if not os.path.exists(file_path):
        print(f"❌ ไม่พบไฟล์: {file_path}")
        return

    print(f"📖 กำลังอ่านไฟล์: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. ดึงข้อมูลทั้งหมด (ทั้งที่สำเร็จ ✅ และไม่สำเร็จ ❌) พร้อมค่า Token
    # Pattern: หา STATUS และเลื่อนไปหา PROMPT TOKENS ที่ใกล้ที่สุด
    pattern = re.compile(r'STATUS:.*?(✅|❌).*?PROMPT TOKENS: (\d+)', re.DOTALL)
    matches = pattern.findall(content)
    
    all_data = []
    for status_icon, token_count in matches:
        is_success = 1 if status_icon == "✅" else 0
        all_data.append((int(token_count), is_success))

    if not all_data:
        print("⚠ ไม่พบข้อมูล STATUS หรือ PROMPT TOKENS ในไฟล์")
        return

    all_tokens = np.array([d[0] for d in all_data])
    success_flags = np.array([d[1] for d in all_data])
    max_token_val = max(all_tokens)

    # 2. ตั้งค่าเริ่มต้นสำหรับกราฟ
    initial_bin_size = 200
    fig, ax = plt.subplots(figsize=(13, 7))
    plt.subplots_adjust(bottom=0.25)

    def update_graph(bin_size):
        ax.clear()
        bin_size = int(bin_size)
        
        bins = np.arange(0, max_token_val + bin_size + 1, bin_size)
        
        # นับจำนวนทั้งหมดในแต่ละช่วง (Total Prompts)
        total_counts, _ = np.histogram(all_tokens, bins=bins)
        # นับจำนวนที่สำเร็จในแต่ละช่วง (Success Counts)
        success_counts, _ = np.histogram(all_tokens[success_flags == 1], bins=bins)
        
        # คำนวณเปอร์เซ็นต์ (เลี่ยงการหารด้วยศูนย์)
        percentages = []
        for s, t in zip(success_counts, total_counts):
            percentages.append((s / t * 100) if t > 0 else 0)
        
        labels = [f"{int(bins[i])}-{int(bins[i+1])}" for i in range(len(bins)-1)]
        
        # วาดกราฟ
        bars = ax.bar(labels, percentages, color='mediumseagreen', edgecolor='darkgreen', alpha=0.7)
        
        ax.set_title(f'Success Rate (%) by Token Range\n(Total Samples: {len(all_data)})', fontsize=14, pad=20)
        ax.set_xlabel('Prompt Token Range', fontsize=12)
        ax.set_ylabel('Success Rate (ASR %)', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        ax.set_ylim(0, max(percentages) + 5 if percentages and max(percentages) > 0 else 100)
        ax.grid(axis='y', linestyle='--', alpha=0.5)

        # แสดงตัวเลข (Success / Total) และ % บนยอดแท่ง
        for i, bar in enumerate(bars):
            height = bar.get_height()
            total_in_bin = total_counts[i]
            success_in_bin = success_counts[i]
            
            if total_in_bin > 0:
                # บรรทัดบน: บอก % | บรรทัดล่าง: บอกจำนวน (สำเร็จ/ทั้งหมด)
                label_text = f"{height:.1f}%\n({success_in_bin}/{total_in_bin})"
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                        label_text, ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        fig.canvas.draw_idle()

    # 3. สร้าง Slider
    ax_slider = plt.axes([0.2, 0.05, 0.6, 0.03])
    slider = Slider(
        ax=ax_slider,
        label='Adjust Bin Size  ',
        valmin=50,
        valmax=2000,
        valinit=initial_bin_size,
        valstep=50,
        color='mediumseagreen'
    )

    slider.on_changed(update_graph)

    # แสดงผลครั้งแรก
    update_graph(initial_bin_size)
    
    print("✅ กราฟ Interactive พร้อมทำงาน!")
    print("💡 คุณสามารถดู (จำนวนสำเร็จ / จำนวนทั้งหมด) ได้ที่หัวแท่งกราฟ")
    plt.show()

# ==========================================
# ระบุ Path ของไฟล์ .txt ตรงนี้
# ==========================================
target_file_path = r"D:\CMU\Y4\Project\dea_result\prefix\results\language\ceremonial\token_counted_FINAL_TOTAL_REPORT.txt"

interactive_percentage_plot(target_file_path)