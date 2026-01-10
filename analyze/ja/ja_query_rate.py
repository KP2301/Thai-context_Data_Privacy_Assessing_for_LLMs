import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import Counter

def parse_success_indices(filepath):
    """อ่านไฟล์และดึง success_indices ออกมา"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # หา success_indices ในรูปแบบ 'success_indices': [1, 4, 5, ...]
    indices_match = re.search(r"'success_indices':\s*\[([\d,\s]+)\]", content)
    if indices_match:
        indices_str = indices_match.group(1)
        indices = [int(x.strip()) for x in indices_str.split(',') if x.strip()]
        return indices
    return []

def create_frequency_graph(directory_path='.'):
    """สร้างกราฟความถี่ของ success_indices หลัง modulo 15"""
    
    # เตรียม counter สำหรับเก็บความถี่ของแต่ละตำแหน่ง (1-15)
    frequency_counter = Counter()
    
    # อ่านไฟล์ทั้งหมดที่ขึ้นต้นด้วย ja_output
    path = Path(directory_path)
    files = list(path.glob('ja_output*.txt'))
    
    print(f"พบไฟล์ทั้งหมด {len(files)} ไฟล์\n")
    
    total_indices = 0
    
    for filepath in files:
        filename = filepath.name
        indices = parse_success_indices(filepath)
        
        if indices:
            print(f"✓ {filename}")
            print(f"  จำนวน success_indices: {len(indices)}")
            
            # แปลงค่าด้วย modulo 15 และนับความถี่
            for idx in indices:
                # ถ้าค่ามากกว่า 15 ให้ modulo ด้วย 15
                # ถ้าผลลัพธ์เป็น 0 ให้เป็น 15 แทน (เพราะเราต้องการช่วง 1-15)
                if idx > 15:
                    mod_value = idx % 15
                    if mod_value == 0:
                        mod_value = 15
                else:
                    mod_value = idx
                
                frequency_counter[mod_value] += 1
                total_indices += 1
            
            print(f"  ตัวอย่าง indices หลัง modulo: {[i % 15 if i > 15 and i % 15 != 0 else (15 if i > 15 else i) for i in indices[:10]]}")
            print()
    
    print(f"\nรวมทั้งหมด: {total_indices} indices จาก {len(files)} ไฟล์\n")
    
    # เตรียมข้อมูลสำหรับกราฟ (1-15)
    positions = list(range(1, 16))
    frequencies = [frequency_counter[i] for i in positions]
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # สร้างแท่งกราฟพร้อมไล่สี
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, 15))
    bars = ax.bar(positions, frequencies, color=colors, alpha=0.8, 
                  edgecolor='white', linewidth=2)
    
    # เพิ่มค่าบนแท่งกราฟ
    for bar, freq in zip(bars, frequencies):
        height = bar.get_height()
        if freq > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height + max(frequencies)*0.01,
                   f'{int(freq)}', ha='center', va='bottom', 
                   fontsize=10, fontweight='bold')
    
    # ตกแต่งกราฟ
    ax.set_xlabel('Position (1-15)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=13, fontweight='bold')
    ax.set_title('Success Indices Frequency Distribution', 
                 fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(positions)
    ax.set_xticklabels(positions, fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # เพิ่มเส้นค่าเฉลี่ย
    mean_freq = np.mean(frequencies)
    ax.axhline(y=mean_freq, color='red', linestyle='--', alpha=0.5, linewidth=2)
    ax.text(15.5, mean_freq, f'Mean: {mean_freq:.1f}', 
            color='red', fontsize=10, va='center', fontweight='bold')
    
    plt.tight_layout()
    
    # บันทึกกราฟ
    output_file = 'success_indices_frequency.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ บันทึกกราฟเรียบร้อยแล้ว: {output_file}\n")
    
    plt.show()
    
    # แสดงสรุปข้อมูล
    print("="*70)
    print("สรุปความถี่ของแต่ละตำแหน่ง (1-15)")
    print("="*70)
    for pos in positions:
        freq = frequency_counter[pos]
        percentage = (freq / total_indices * 100) if total_indices > 0 else 0
        bar_chart = '█' * int(freq / max(frequencies) * 50) if max(frequencies) > 0 else ''
        print(f"ตำแหน่ง {pos:2d}: {freq:4d} ครั้ง ({percentage:5.2f}%) {bar_chart}")
    
    print(f"\nรวมทั้งหมด: {total_indices} indices")
    print(f"ค่าเฉลี่ย: {mean_freq:.2f} ครั้งต่อตำแหน่ง")
    print(f"ค่ามากที่สุด: {max(frequencies)} ครั้ง (ตำแหน่ง {frequencies.index(max(frequencies)) + 1})")
    print(f"ค่าน้อยที่สุด: {min(frequencies)} ครั้ง (ตำแหน่ง {frequencies.index(min(frequencies)) + 1})")

if __name__ == "__main__":
    directory = "E:\\project-Backup\\LLM-PBE_VS\\ja_result"
    
    create_frequency_graph(directory)