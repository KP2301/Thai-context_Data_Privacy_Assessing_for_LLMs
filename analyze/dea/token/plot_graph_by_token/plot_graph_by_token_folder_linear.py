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

    # หาไฟล์ที่ขึ้นต้นด้วย "token_counted_" ในโฟลเดอร์
    files = list(Path(folder_path).glob("token_counted_*.txt"))
    
    if not files:
        print(f"⚠ ไม่พบไฟล์ที่ขึ้นต้นด้วย 'token_counted_' ในโฟลเดอร์: {folder_path}")
        return
    
    print(f"📂 พบไฟล์ {len(files)} ไฟล์:")
    for f in files:
        print(f"  - {f.name}")
    
    # เก็บข้อมูลแต่ละโมเดล
    model_data = {}
    max_token_overall = 0
    
    for file_path in files:
        # ดึงชื่อโมเดลจากชื่อไฟล์ (token_counted_modelname.txt -> modelname)
        model_name = file_path.stem.replace("token_counted_", "")
        
        print(f"\n📖 กำลังอ่านไฟล์: {file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # ดึงข้อมูล STATUS และ PROMPT TOKENS
        pattern = re.compile(r'STATUS:.*?(✅|❌).*?PROMPT TOKENS: (\d+)', re.DOTALL)
        matches = pattern.findall(content)
        
        all_data = []
        for status_icon, token_count in matches:
            is_success = 1 if status_icon == "✅" else 0
            all_data.append((int(token_count), is_success))

        if not all_data:
            print(f"⚠ ไม่พบข้อมูลใน {file_path.name}")
            continue
        
        all_tokens = np.array([d[0] for d in all_data])
        success_flags = np.array([d[1] for d in all_data])
        max_token_val = max(all_tokens)
        max_token_overall = max(max_token_overall, max_token_val)
        
        model_data[model_name] = {
            'tokens': all_tokens,
            'success': success_flags,
            'total': len(all_data)
        }
        
        print(f"✅ โหลดข้อมูล {model_name}: {len(all_data)} samples")
    
    if not model_data:
        print("❌ ไม่มีข้อมูลที่ใช้งานได้")
        return
    
    # ตั้งค่ากราฟ
    initial_bin_size = 200
    fig, ax = plt.subplots(figsize=(14, 8))
    plt.subplots_adjust(bottom=0.25)
    
    # สีสำหรับแต่ละโมเดล
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#06A77D', '#D62828', '#8338EC']
    
    def update_graph(bin_size):
        ax.clear()
        bin_size = int(bin_size)
        
        bins = np.arange(0, max_token_overall + bin_size + 1, bin_size)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        # วาดเส้นสำหรับแต่ละโมเดล
        for idx, (model_name, data) in enumerate(model_data.items()):
            all_tokens = data['tokens']
            success_flags = data['success']
            
            # นับจำนวนทั้งหมดและจำนวนที่สำเร็จในแต่ละช่วง
            total_counts, _ = np.histogram(all_tokens, bins=bins)
            success_counts, _ = np.histogram(all_tokens[success_flags == 1], bins=bins)
            
            # คำนวณเปอร์เซ็นต์
            percentages = []
            for s, t in zip(success_counts, total_counts):
                percentages.append((s / t * 100) if t > 0 else np.nan)
            
            # วาดเส้น
            color = colors[idx % len(colors)]
            ax.plot(bin_centers, percentages, marker='o', linewidth=2.5, 
                   label=f"{model_name} (n={data['total']})", 
                   color=color, markersize=6, alpha=0.8)
        
        ax.set_title('DEA Accuracy (%) by Token Range - Multi-Model Comparison', 
                    fontsize=15, fontweight='bold', pad=20)
        ax.set_xlabel('Token Range (midpoint)', fontsize=13)
        ax.set_ylabel('DEA Accuracy (%)', fontsize=13)
        ax.set_ylim(0, 105)
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.legend(loc='best', fontsize=10, framealpha=0.9)
        
        # แสดง bin labels
        labels = [f"{int(bins[i])}-{int(bins[i+1])}" for i in range(len(bins)-1)]
        ax.set_xticks(bin_centers)
        ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
        
        fig.canvas.draw_idle()
    
    # สร้าง Slider
    ax_slider = plt.axes([0.2, 0.08, 0.6, 0.03])
    slider = Slider(
        ax=ax_slider,
        label='Adjust Bin Size  ',
        valmin=50,
        valmax=2000,
        valinit=initial_bin_size,
        valstep=50,
        color='steelblue'
    )
    
    slider.on_changed(update_graph)
    
    # แสดงผลครั้งแรก
    update_graph(initial_bin_size)
    
    print("\n✅ กราฟ Interactive พร้อมทำงาน!")
    print("💡 ใช้ Slider เพื่อปรับขนาด Bin และดูความแตกต่างระหว่างโมเดล")
    plt.show()

# ==========================================
# ระบุ Path ของโฟลเดอร์ที่มีไฟล์ token_counted_*.txt
# ==========================================
target_folder_path = r"D:\CMU\Y4\Project\dea_result\prefix\results\token\casual"

interactive_percentage_plot(target_folder_path)