import re
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def parse_jailbreak_file(filepath):
    """อ่านไฟล์และดึง Rate ออกมา"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # หา Rate ในรูปแบบ "Rate : XX.XX%"
    rate_match = re.search(r'Rate\s*:\s*(\d+\.?\d*)%', content)
    if rate_match:
        return float(rate_match.group(1))
    return None

def extract_model_and_level(filename):
    """แยกชื่อ model และ level จากชื่อไฟล์"""
    filename = filename.lower()
    
    # หา model
    if 'llama-3.1-8b-instant' in filename:
        model = 'Llama 3.1 8B'
    elif 'llama-4-maverick-17b' in filename:
        model = 'Llama 4 Maverick 17B'
    elif 'kimi-k2-instruct' in filename:
        model = 'Kimi K2'
    else:
        model = 'Unknown'
    
    # หา level
    if 'casual' in filename and 'semi' not in filename:
        level = 'Casual'
    elif 'ceremonial' in filename:
        level = 'Ceremonial'
    elif 'formal' in filename and 'semi' not in filename and 'informal' not in filename:
        level = 'Formal'
    elif 'informal' in filename:
        level = 'Informal'
    elif 'semi_formal' in filename or 'semi-formal' in filename:
        level = 'Semi-formal'
    else:
        level = 'Unknown'
    
    return model, level

def create_benchmark_graph(directory_path='.'):
    """สร้างกราฟจากไฟล์ทั้งหมดในโฟลเดอร์"""
    
    # เตรียมโครงสร้างข้อมูล
    levels = ['Ceremonial', 'Casual', 'Formal', 'Semi-formal', 'Informal']
    models = ['Llama 3.1 8B', 'Llama 4 Maverick 17B', 'Kimi K2']
    
    # สร้าง dictionary เก็บข้อมูล
    data = {level: {model: None for model in models} for level in levels}
    
    # อ่านไฟล์ทั้งหมดที่ขึ้นต้นด้วย ja_output
    path = Path(directory_path)
    files = list(path.glob('ja_output*.txt'))
    
    print(f"พบไฟล์ทั้งหมด {len(files)} ไฟล์\n")
    
    for filepath in files:
        filename = filepath.name
        model, level = extract_model_and_level(filename)
        rate = parse_jailbreak_file(filepath)
        
        if rate is not None and level in data and model in data[level]:
            data[level][model] = rate
            print(f"✓ {filename}")
            print(f"  Model: {model}, Level: {level}, Rate: {rate}%\n")
    
    # เตรียมข้อมูลสำหรับกราฟ
    x = np.arange(len(levels))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # สีสำหรับแต่ละ model
    colors = {
        'Llama 3.1 8B': '#3b82f6',
        'Llama 4 Maverick 17B': '#10b981',
        'Kimi K2': '#f59e0b'
    }
    
    # สร้างแท่งกราฟสำหรับแต่ละ model
    for i, model in enumerate(models):
        rates = [data[level][model] if data[level][model] is not None else 0 
                 for level in levels]
        offset = (i - 1) * width
        bars = ax.bar(x + offset, rates, width, label=model, 
                      color=colors[model], alpha=0.8, edgecolor='white', linewidth=1.5)
        
        # เพิ่มค่าบนแท่งกราฟ
        for j, (bar, rate) in enumerate(zip(bars, rates)):
            if rate > 0:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{rate:.1f}%', ha='center', va='bottom', 
                       fontsize=9, fontweight='bold')
    
    # ตกแต่งกราฟ
    ax.set_xlabel('Language Level', fontsize=13, fontweight='bold')
    ax.set_ylabel('Success Rate (%)', fontsize=13, fontweight='bold')
    ax.set_title('Thai Jailbreak Benchmark: Success Rate by Language Level and Model', 
                 fontsize=15, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(levels, fontsize=11)
    ax.legend(fontsize=11, loc='upper left', framealpha=0.9)
    ax.set_ylim(0, 60)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_axisbelow(True)
    
    # เพิ่มเส้น reference
    ax.axhline(y=50, color='red', linestyle='--', alpha=0.3, linewidth=1)
    ax.text(len(levels)-0.5, 51, '50%', color='red', fontsize=9, alpha=0.5)
    
    plt.tight_layout()
    
    # บันทึกกราฟ
    output_file = 'thai_jailbreak_benchmark.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ บันทึกกราฟเรียบร้อยแล้ว: {output_file}")
    
    plt.show()
    
    # แสดงสรุปข้อมูล
    print("\n" + "="*70)
    print("สรุปข้อมูล Success Rate")
    print("="*70)
    for level in levels:
        print(f"\n{level}:")
        for model in models:
            rate = data[level][model]
            if rate is not None:
                print(f"  {model:30s}: {rate:6.2f}%")
            else:
                print(f"  {model:30s}: ไม่พบข้อมูล")

if __name__ == "__main__":
    # เปลี่ยนเป็น path ที่เก็บไฟล์ของคุณ
    directory = "E:\\project-Backup\\LLM-PBE_VS\\ja_result"  # โฟลเดอร์ปัจจุบัน
    
    # หรือระบุ path เฉพาะ เช่น
    # directory = "/path/to/your/files"
    
    create_benchmark_graph(directory)