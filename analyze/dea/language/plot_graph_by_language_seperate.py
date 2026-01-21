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

def create_dea_accuracy_chart(base_folder_path, output_filename='dea_accuracy_comparison.png'):
    """
    สร้างกราฟแท่งแสดง DEA Accuracy จากไฟล์ในโฟลเดอร์ โดยแยกตามโมเดล
    
    Args:
        base_folder_path: path ของโฟลเดอร์หลัก (เช่น "dea_result/prefix/results")
        output_filename: ชื่อไฟล์สำหรับบันทึกกราฟ
    """
    # กำหนดลำดับระดับภาษา
    language_levels = ['casual', 'ceremonial', 'formal', 'informal', 'semi_formal']
    
    # กำหนดโมเดลที่ต้องการวิเคราะห์
    models = ['llama', 'kimi', 'meta']
    
    # เก็บข้อมูลสำหรับแต่ละโมเดล
    model_data = {model: {'asr': [], 'success': [], 'total': [], 'levels': []} 
                  for model in models}
    
    # วนอ่านข้อมูลแต่ละระดับภาษา
    for level in language_levels:
        language_folder = os.path.join(base_folder_path, level)
        
        if not os.path.exists(language_folder):
            print(f"Warning: ไม่พบโฟลเดอร์ {language_folder}")
            continue
        
        # วนอ่านข้อมูลแต่ละโมเดล
        for model in models:
            filename = f'{level}_{model}.txt'
            filepath = os.path.join(language_folder, filename)
            
            if os.path.exists(filepath):
                asr, success, total = extract_asr_from_file(filepath)
                if asr is not None:
                    model_data[model]['asr'].append(asr)
                    model_data[model]['success'].append(success)
                    model_data[model]['total'].append(total)
                    if level not in model_data[model]['levels']:
                        model_data[model]['levels'].append(level)
                    print(f"{level} - {model}: {asr}% ASR (Success: {success}/{total})")
                else:
                    print(f"Warning: ไม่พบข้อมูล ASR ในไฟล์ {filename}")
                    model_data[model]['asr'].append(0)
                    model_data[model]['success'].append(0)
                    model_data[model]['total'].append(0)
                    if level not in model_data[model]['levels']:
                        model_data[model]['levels'].append(level)
            else:
                print(f"Warning: ไม่พบไฟล์ {filepath}")
                model_data[model]['asr'].append(0)
                model_data[model]['success'].append(0)
                model_data[model]['total'].append(0)
                if level not in model_data[model]['levels']:
                    model_data[model]['levels'].append(level)
    
    # ตรวจสอบว่ามีข้อมูลหรือไม่
    if not any(model_data[model]['asr'] for model in models):
        print("Error: ไม่พบข้อมูลใดๆ")
        return
    
    # สร้างกราฟ
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # กำหนดความกว้างของแท่งและตำแหน่ง
    bar_width = 0.25
    x = range(len(language_levels))
    colors = {'llama': '#FF6B6B', 'kimi': '#4ECDC4', 'meta': '#45B7D1'}
    
    # สร้างแท่งกราฟสำหรับแต่ละโมเดล
    for i, model in enumerate(models):
        positions = [pos + (i - 1) * bar_width for pos in x]
        bars = ax.bar(positions, model_data[model]['asr'], bar_width, 
                     label=model.upper(), color=colors[model], 
                     edgecolor='black', alpha=0.8)
        
        # เพิ่มค่าบนแท่งกราฟ
        for bar, value, success, total in zip(bars, model_data[model]['asr'], 
                                              model_data[model]['success'], 
                                              model_data[model]['total']):
            height = bar.get_height()
            if value > 0:  # แสดงเฉพาะค่าที่มีข้อมูล
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:.1f}%\n({success}/{total})',
                       ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    # ตั้งค่ากราฟ
    ax.set_xlabel('Language Level', fontsize=13, fontweight='bold')
    ax.set_ylabel('DEA Accuracy (%)', fontsize=13, fontweight='bold')
    ax.set_title('DEA Accuracy Comparison by Language Level and Model', 
                fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(language_levels, fontsize=11)
    ax.legend(fontsize=11, loc='upper right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # กำหนดขอบเขต y-axis
    max_asr = max([max(model_data[model]['asr']) for model in models if model_data[model]['asr']])
    ax.set_ylim(0, max_asr * 1.25)
    
    # บันทึกกราฟ
    plt.tight_layout()
    save_path = os.path.join(base_folder_path, output_filename)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\nกราฟถูกบันทึกเป็นไฟล์: {save_path}")
    
    # แสดงกราฟ
    plt.show()


# ใช้งาน
base_folder = r"D:\CMU\Y4\LLM-PBE_VS\dea_result\prefix\results\language"
create_dea_accuracy_chart(base_folder, output_filename='dea_accuracy_comparison.png')