import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import Counter

def parse_success_indices(filepath):
    """อ่านไฟล์และดึง success_indices ออกมา"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ลองหารูปแบบ 1: 'success_indices': [...]
    indices_match = re.search(r"'success_indices':\s*\[([\d,\s\n]+)\]", content, re.DOTALL)
    
    if not indices_match:
        # ลองหารูปแบบ 2: Success Indices (xxx items): ... (รูปแบบใหม่)
        indices_match = re.search(r"Success\s+Indices\s*\([^)]+\):\s*([\d,\s\n]+?)(?:\n\n|\Z)", content, re.DOTALL | re.IGNORECASE)
    
    if indices_match:
        indices_str = indices_match.group(1)
        # ใช้ regex ดึงตัวเลขทั้งหมดออกมา (ไม่สนใจ format)
        indices = [int(x) for x in re.findall(r'\d+', indices_str)]
        return indices
    
    return []

def create_single_round_graph(filepath, round_name, total_attempts=26):
    """สร้างกราฟสำหรับ 1 round"""
    frequency_counter = Counter()
    
    indices = parse_success_indices(filepath)
    
    if not indices:
        print(f"✗ {round_name} - ไม่พบ success_indices")
        return None
    
    print(f"✓ {round_name}")
    print(f"  จำนวน success_indices: {len(indices)}")
    
    # แปลงค่าด้วย modulo 15 และนับความถี่
    for idx in indices:
        if idx > 15:
            mod_value = idx % 15
            if mod_value == 0:
                mod_value = 15
        else:
            mod_value = idx
        
        frequency_counter[mod_value] += 1
    
    # เตรียมข้อมูลสำหรับกราฟ (1-15)
    positions = list(range(1, 16))
    frequencies = [frequency_counter[i] for i in positions]
    percentages = [(freq / total_attempts * 100) for freq in frequencies]
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(14, 8))
    
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, 15))
    bars = ax.bar(positions, percentages, color=colors, alpha=0.8, 
                   edgecolor='white', linewidth=2)
    
    # เพิ่มค่าบนแท่งกราฟ
    for bar, freq, pct in zip(bars, frequencies, percentages):
        height = bar.get_height()
        if freq > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height + max(percentages)*0.01,
                   f'{pct:.1f}%\n({freq})',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # ตกแต่งกราฟ
    ax.set_xlabel('Position (1-15)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Percentage (%)', fontsize=13, fontweight='bold')
    ax.set_title(f'Success Indices Distribution - {round_name} (n={total_attempts})', 
                 fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(positions)
    ax.set_xticklabels(positions, fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # เพิ่มเส้นค่าเฉลี่ย
    mean_pct = np.mean(percentages)
    ax.axhline(y=mean_pct, color='red', linestyle='--', alpha=0.5, linewidth=2)
    ax.text(15.5, mean_pct, f'Mean: {mean_pct:.2f}%', 
            color='red', fontsize=10, va='center', fontweight='bold')
    
    plt.tight_layout()
    
    # บันทึกกราฟ
    output_file = f'eng_defence_kimi_{round_name}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✓ บันทึก: {output_file}\n")
    
    plt.close()
    
    return frequencies

def create_average_graph(all_frequencies, total_attempts=130):
    """สร้างกราฟค่าเฉลี่ยจากทุก round"""
    positions = list(range(1, 16))
    
    # คำนวณผลรวมของแต่ละตำแหน่งจากทุก round
    sum_frequencies = []
    for pos_idx in range(15):
        total_freq = sum(freq_list[pos_idx] for freq_list in all_frequencies)
        sum_frequencies.append(total_freq)
    
    # คำนวณ percentage จากผลรวม
    sum_percentages = [(freq / total_attempts * 100) for freq in sum_frequencies]
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(14, 8))
    
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, 15))
    bars = ax.bar(positions, sum_percentages, color=colors, alpha=0.8, 
                   edgecolor='white', linewidth=2)
    
    # เพิ่มค่าบนแท่งกราฟ (แสดง percentage และผลรวม frequency)
    for bar, freq, pct in zip(bars, sum_frequencies, sum_percentages):
        height = bar.get_height()
        if freq > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height + max(sum_percentages)*0.01,
                   f'{pct:.1f}%\n({int(freq)})',  # เปลี่ยนเป็น int(freq) เพื่อแสดงผลรวม
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # ตกแต่งกราฟ
    ax.set_xlabel('Position (1-15)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Percentage (%)', fontsize=13, fontweight='bold')
    ax.set_title(f'Success Indices Distribution - Average of {len(all_frequencies)} Rounds (n={total_attempts})', 
                 fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(positions)
    ax.set_xticklabels(positions, fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # เพิ่มเส้นค่าเฉลี่ย
    mean_pct = np.mean(sum_percentages)
    ax.axhline(y=mean_pct, color='red', linestyle='--', alpha=0.5, linewidth=2)
    ax.text(15.5, mean_pct, f'Mean: {mean_pct:.2f}%', 
            color='red', fontsize=10, va='center', fontweight='bold')
    
    plt.tight_layout()
    
    # บันทึกกราฟ
    output_file = 'eng_defence_kimi_average.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ บันทึกกราฟค่าเฉลี่ย: {output_file}\n")
    
    plt.close()
    
    # แสดงสรุปข้อมูล
    print("="*70)
    print("สรุปผลรวมของแต่ละตำแหน่ง (1-15) จากทุก round")
    print("="*70)
    for pos, freq, pct in zip(positions, sum_frequencies, sum_percentages):
        bar_chart = '█' * int(pct * 2) if pct > 0 else ''
        print(f"ตำแหน่ง {pos:2d}: {int(freq):4d} ครั้ง ({pct:5.2f}%) {bar_chart}")
    
    print(f"\nรวมทั้งหมด: {int(sum(sum_frequencies))} indices จาก {total_attempts} ครั้ง")
    print(f"ค่าเฉลี่ย: {mean_pct:.2f}% ต่อตำแหน่ง")
    print(f"ค่ามากที่สุด: {max(sum_percentages):.2f}% (ตำแหน่ง {sum_percentages.index(max(sum_percentages)) + 1}, {int(max(sum_frequencies))} ครั้ง)")
    print(f"ค่าน้อยที่สุด: {min(sum_percentages):.2f}% (ตำแหน่ง {sum_percentages.index(min(sum_percentages)) + 1}, {int(min(sum_frequencies))} ครั้ง)")

def process_all_rounds(directory_path=r'E:\project-Backup\LLM-PBE_VS\ja_result\without_defence\eng'):
    """ประมวลผลทุก round และสร้างกราฟค่าเฉลี่ย"""
    
    path = Path(directory_path)
    
    # ค้นหา round ทั้งหมด
    round_folders = sorted([d for d in path.iterdir() if d.is_dir() and d.name.startswith('round')])
    
    if not round_folders:
        print("⚠️ ไม่พบโฟลเดอร์ round!")
        return
    
    print(f"พบ {len(round_folders)} rounds: {[d.name for d in round_folders]}\n")
    print("="*70)
    
    all_frequencies = []
    
    # ประมวลผลแต่ละ round
    for round_folder in round_folders:
        round_name = round_folder.name
        filepath = round_folder / 'ja_output_moonshotai_kimi-k2-instruct-0905.txt'
        
        if not filepath.exists():
            print(f"✗ {round_name} - ไม่พบไฟล์ {filepath.name}")
            continue
        
        frequencies = create_single_round_graph(filepath, round_name, total_attempts=26)
        if frequencies:
            all_frequencies.append(frequencies)
    
    # สร้างกราฟค่าเฉลี่ย
    if all_frequencies:
        print("="*70)
        print("กำลังสร้างกราฟค่าเฉลี่ย...")
        print("="*70)
        create_average_graph(all_frequencies, total_attempts=130)
        print(f"\n✅ เสร็จสิ้น! สร้างกราฟทั้งหมด {len(all_frequencies) + 1} ภาพ")
    else:
        print("⚠️ ไม่มีข้อมูลสำหรับสร้างกราฟค่าเฉลี่ย")

def create_combined_round_graph(round_frequencies, round_name, output_prefix, total_attempts=78):
    """สร้างกราฟสำหรับ 1 round ที่รวมทุกไฟล์"""
    positions = list(range(1, 16))
    percentages = [(freq / total_attempts * 100) for freq in round_frequencies]
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(14, 8))
    
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, 15))
    bars = ax.bar(positions, percentages, color=colors, alpha=0.8, 
                   edgecolor='white', linewidth=2)
    
    # เพิ่มค่าบนแท่งกราฟ
    for bar, freq, pct in zip(bars, round_frequencies, percentages):
        height = bar.get_height()
        if freq > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height + max(percentages)*0.01,
                   f'{pct:.1f}%\n({int(freq)})',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # ตกแต่งกราฟ
    ax.set_xlabel('Position (1-15)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Percentage (%)', fontsize=13, fontweight='bold')
    ax.set_title(f'Success Indices Distribution - {round_name} - All Models (n={total_attempts})', 
                 fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(positions)
    ax.set_xticklabels(positions, fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # เพิ่มเส้นค่าเฉลี่ย
    mean_pct = np.mean(percentages)
    ax.axhline(y=mean_pct, color='red', linestyle='--', alpha=0.5, linewidth=2)
    ax.text(15.5, mean_pct, f'Mean: {mean_pct:.2f}%', 
            color='red', fontsize=10, va='center', fontweight='bold')
    
    plt.tight_layout()
    
    # บันทึกกราฟ
    output_file = f'{output_prefix}_{round_name}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✓ บันทึก: {output_file}")
    
    plt.close()

def process_all_files_combined(directory_path, output_prefix='combined', per_round_attempts=78, total_attempts=390):
    """อ่านทุกไฟล์ ja_output*.txt จากทุก round และสร้างกราฟแยกแต่ละรอบ + กราฟรวม"""
    
    path = Path(directory_path)
    
    # ค้นหา round ทั้งหมด
    round_folders = sorted([d for d in path.iterdir() if d.is_dir() and d.name.startswith('round')])
    
    if not round_folders:
        print("⚠️ ไม่พบโฟลเดอร์ round!")
        return
    
    print(f"พบ {len(round_folders)} rounds: {[d.name for d in round_folders]}")
    print(f"กำลังประมวลผลทุกไฟล์ ja_output*.txt\n")
    print("="*70)
    
    all_round_frequencies = []
    
    # ประมวลผลแต่ละ round
    for round_folder in round_folders:
        round_name = round_folder.name
        
        # ค้นหาไฟล์ ja_output*.txt ทั้งหมดใน round นี้
        # ja_files = list(round_folder.glob('semi_formal\ja_output*.txt'))
        ja_files = list(round_folder.glob('*\ja_output*.txt'))
        # ja_files = list(round_folder.glob('semi_formal\ja_output_llama-3.1-8b-instant_semi_formal.txt'))
        # ja_files = list(round_folder.glob('semi_formal\ja_output_moonshotai_kimi-k2-instruct-0905_semi_formal.txt'))
        # ja_files = list(round_folder.glob('semi_formal\ja_output_meta-llama_llama-4-maverick-17b-128e-instruct_semi_formal.txt'))
        
        if not ja_files:
            print(f"✗ {round_name} - ไม่พบไฟล์ ja_output*.txt")
            continue
        
        print(f"\n{round_name}: พบ {len(ja_files)} ไฟล์")
        
        # รวม frequency จากทุกไฟล์ใน round นี้
        round_frequency_counter = Counter()
        total_indices_in_round = 0
        
        for filepath in ja_files:
            filename = filepath.name
            indices = parse_success_indices(filepath)
            
            if indices:
                print(f"  ✓ {filename}: {len(indices)} indices")
                
                # แปลงค่าด้วย modulo 15 และนับความถี่
                for idx in indices:
                    if idx > 15:
                        mod_value = idx % 15
                        if mod_value == 0:
                            mod_value = 15
                    else:
                        mod_value = idx
                    
                    round_frequency_counter[mod_value] += 1
                    total_indices_in_round += 1
            else:
                print(f"  ✗ {filename}: ไม่พบ success_indices")
        
        # แปลง Counter เป็น list สำหรับตำแหน่ง 1-15
        positions = list(range(1, 16))
        round_frequencies = [round_frequency_counter[i] for i in positions]
        
        print(f"  รวม {round_name}: {total_indices_in_round} indices")
        
        # สร้างกราฟสำหรับ round นี้
        create_combined_round_graph(round_frequencies, round_name, output_prefix, per_round_attempts)
        
        all_round_frequencies.append(round_frequencies)
    
    # สร้างกราฟรวมทุก round
    if all_round_frequencies:
        print("\n" + "="*70)
        print("กำลังสร้างกราฟรวมทั้งหมด...")
        print("="*70)
        
        positions = list(range(1, 16))
        
        # คำนวณผลรวมของแต่ละตำแหน่งจากทุก round
        sum_frequencies = []
        for pos_idx in range(15):
            total_freq = sum(freq_list[pos_idx] for freq_list in all_round_frequencies)
            sum_frequencies.append(total_freq)
        
        # คำนวณ percentage จากผลรวม
        sum_percentages = [(freq / total_attempts * 100) for freq in sum_frequencies]
        
        # สร้างกราฟ
        fig, ax = plt.subplots(figsize=(14, 8))
        
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, 15))
        bars = ax.bar(positions, sum_percentages, color=colors, alpha=0.8, 
                       edgecolor='white', linewidth=2)
        
        # เพิ่มค่าบนแท่งกราฟ
        for bar, freq, pct in zip(bars, sum_frequencies, sum_percentages):
            height = bar.get_height()
            if freq > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + max(sum_percentages)*0.01,
                       f'{pct:.1f}%\n({int(freq)})',
                       ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # ตกแต่งกราฟ
        ax.set_xlabel('Position (1-15)', fontsize=13, fontweight='bold')
        ax.set_ylabel('Percentage (%)', fontsize=13, fontweight='bold')
        ax.set_title(f'Success Indices Distribution - All Models Combined (n={total_attempts})', 
                     fontsize=15, fontweight='bold', pad=20)
        ax.set_xticks(positions)
        ax.set_xticklabels(positions, fontsize=11)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_axisbelow(True)
        
        # เพิ่มเส้นค่าเฉลี่ย
        mean_pct = np.mean(sum_percentages)
        ax.axhline(y=mean_pct, color='red', linestyle='--', alpha=0.5, linewidth=2)
        ax.text(15.5, mean_pct, f'Mean: {mean_pct:.2f}%', 
                color='red', fontsize=10, va='center', fontweight='bold')
        
        plt.tight_layout()
        
        # บันทึกกราฟ
        output_file = f'{output_prefix}_average.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✓ บันทึกกราฟรวม: {output_file}\n")
        
        plt.close()
        
        # แสดงสรุปข้อมูล
        print("="*70)
        print("สรุปผลรวมของแต่ละตำแหน่ง (1-15) จากทุกไฟล์")
        print("="*70)
        for pos, freq, pct in zip(positions, sum_frequencies, sum_percentages):
            bar_chart = '█' * int(pct * 2) if pct > 0 else ''
            print(f"ตำแหน่ง {pos:2d}: {int(freq):4d} ครั้ง ({pct:5.2f}%) {bar_chart}")
        
        print(f"\nรวมทั้งหมด: {int(sum(sum_frequencies))} indices จาก {total_attempts} ครั้ง")
        print(f"ค่าเฉลี่ย: {mean_pct:.2f}% ต่อตำแหน่ง")
        print(f"ค่ามากที่สุด: {max(sum_percentages):.2f}% (ตำแหน่ง {sum_percentages.index(max(sum_percentages)) + 1}, {int(max(sum_frequencies))} ครั้ง)")
        print(f"ค่าน้อยที่สุด: {min(sum_percentages):.2f}% (ตำแหน่ง {sum_percentages.index(min(sum_percentages)) + 1}, {int(min(sum_frequencies))} ครั้ง)")
        
        print(f"\n✅ เสร็จสิ้น! สร้างกราฟทั้งหมด {len(all_round_frequencies) + 1} ภาพ")
        print(f"   - แยกแต่ละรอบ: {len(all_round_frequencies)} ภาพ")
        print(f"   - กราฟรวม: 1 ภาพ")
    else:
        print("⚠️ ไม่มีข้อมูลสำหรับสร้างกราฟ")

if __name__ == "__main__":
    # แบบเก่า - แยกไฟล์ตาม model
    # directory = r"E:\project-Backup\LLM-PBE_VS\ja_result\without_defence\th"
    # directory = r"E:\project-Backup\LLM-PBE_VS\ja_result\defence\scrub\eng"
    # process_all_rounds(directory)
    
    # แบบใหม่ - รวมทุกไฟล์ ja_output*.txt (แยกแต่ละรอบ + กราฟรวม)
    directory = r"E:\project-Backup\LLM-PBE_VS\ja_result\defence\defensive_prompt\eng"
    
    # directory = r"E:\project-Backup\LLM-PBE_VS\ja_result\defence\scrub\th"
    # process_all_files_combined(
    #     directory_path=directory,
    #     output_prefix='th_defence_scrub_semi_formal_kimi',
    #     per_round_attempts=26,
    #     total_attempts=130
    # )
    process_all_files_combined(
        directory_path=directory,
        output_prefix='eng_defence_defensive_prompt',
        per_round_attempts=78,
        total_attempts=390
    )