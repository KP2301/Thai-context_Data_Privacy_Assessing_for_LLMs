import os
import re
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'sans-serif'

def extract_asr_from_file(filepath):
    """
    อ่านไฟล์และดึงค่า ASR (Attack Success Rate) และ Total Success จากไฟล์
    
    Args:
        filepath: path ของไฟล์ที่ต้องการอ่าน
    
    Returns:
        tuple: (asr_percentage, success_count, total_count) หรือ (None, None, None) ถ้าไม่พบข้อมูล
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # หาบรรทัดที่มี "Overall Success Rate (ASR): X.XX%"
            asr_match = re.search(r'Overall Success Rate \(ASR\):\s*(\d+\.?\d*)%', content)
            # หาบรรทัดที่มี "Total Success: 126 / 9150"
            total_match = re.search(r'Total Success:\s*(\d+)\s*/\s*(\d+)', content)
            
            if asr_match and total_match:
                asr = float(asr_match.group(1))
                success = int(total_match.group(1))
                total = int(total_match.group(2))
                return (asr, success, total)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return (None, None, None)

def create_dea_accuracy_chart(folder_path, output_filename='dea_accuracy_chart.png'):
    """
    สร้างกราฟแท่งแสดง DEA Accuracy จากไฟล์ในโฟลเดอร์
    
    Args:
        folder_path: path ของโฟลเดอร์ที่มีไฟล์ข้อมูล
        output_filename: ชื่อไฟล์สำหรับบันทึกกราฟ
    """
    # กำหนดลำดับระดับภาษา
    language_levels = ['ceremonial', 'casual', 'formal', 'semi-formal', 'informal']
    
    # เก็บข้อมูล ASR สำหรับแต่ละระดับภาษา
    asr_values = []
    success_counts = []
    total_counts = []
    found_levels = []
    
    # วนอ่านไฟล์ตามลำดับระดับภาษา
    for level in language_levels:
        filename = f'FINAL_TOTAL_REPORT_{level}.txt'
        filepath = os.path.join(folder_path, filename)
        
        if os.path.exists(filepath):
            asr, success, total = extract_asr_from_file(filepath)
            if asr is not None:
                asr_values.append(asr)
                success_counts.append(success)
                total_counts.append(total)
                found_levels.append(level)
                print(f"{level}: {asr}% ASR (Success: {success}/{total})")
            else:
                print(f"Warning: ไม่พบข้อมูล ASR ในไฟล์ {filename}")
        else:
            print(f"Warning: ไม่พบไฟล์ {filename}")
    
    # ตรวจสอบว่ามีข้อมูลหรือไม่
    if not asr_values:
        print("Error: ไม่พบข้อมูลใดๆ ในโฟลเดอร์")
        return
    
    # สร้างกราฟ
    plt.figure(figsize=(10, 6))
    bars = plt.bar(found_levels, asr_values, color='steelblue', edgecolor='black', alpha=0.7)
    
    # เพิ่มค่าบนแท่งกราฟ
    for bar, value, success, total in zip(bars, asr_values, success_counts, total_counts):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.2f}%\n({success}/{total})',
                ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # ตั้งค่ากราฟ
    plt.xlabel('Language Level', fontsize=12, fontweight='bold')
    plt.ylabel('DEA Accuracy (%)', fontsize=12, fontweight='bold')
    plt.title('DEA Accuracy by Language Level', fontsize=14, fontweight='bold')
    plt.ylim(0, max(asr_values) * 1.2)  
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    # บันทึกกราฟ
    plt.tight_layout()
    save_path = os.path.join(folder_path, output_filename)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nกราฟถูกบันทึกเป็นไฟล์: {output_filename} ในโฟลเดอร์: {folder_path}")
    
    # แสดงกราฟ
    plt.show()


folder_path = r"./"

create_dea_accuracy_chart(folder_path, output_filename='dea_accuracy_by_language.png')