import re
import os
from transformers import AutoTokenizer

def add_token_count_to_report(input_file_path, model_name="Qwen/Qwen2.5-1.5B"):
    if not os.path.exists(input_file_path):
        print(f"❌ ไม่พบไฟล์: {input_file_path}")
        return

    print(f"🔄 กำลังโหลด Tokenizer ({model_name})...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    print(f"📖 กำลังอ่านไฟล์และประมวลผล...")
    with open(input_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # ฟังก์ชันสำหรับจัดการการแทรกบรรทัด Token
    def process_match(match):
        header_prompt = match.group(1) # 📝 PROMPT (Input):\n
        prompt_text = match.group(2).strip()
        label_header = match.group(3)  # 🔐 LABEL (Secret):

        # นับ token ของเฉพาะส่วน prompt_text
        tokens = tokenizer.encode(prompt_text, add_special_tokens=False)
        num_tokens = len(tokens)
        
        # คืนค่ากลับไปเขียน: [Header][Text][บรรทัดใหม่ Token][เว้นวรรค][Label Header]
        return f"{header_prompt}{prompt_text}\nPROMPT TOKENS: {num_tokens}\n\n{label_header}"

    # Regex ที่ครอบคลุมกลุ่มข้อมูลครบถ้วน
    # กลุ่ม 1: 📝 PROMPT (Input):
    # กลุ่ม 2: เนื้อหาจนถึงก่อนหน้า LABEL
    # กลุ่ม 3: 🔐 LABEL (Secret):
    full_pattern = re.compile(r'(📝 PROMPT \(Input\):\n)(.*?)\n(🔐 LABEL \(Secret\):)', re.DOTALL)
    
    new_content = full_pattern.sub(process_match, content)

    # บันทึกไฟล์ใหม่
    dir_name = os.path.dirname(input_file_path)
    base_name = os.path.basename(input_file_path)
    output_path = os.path.join(dir_name, f"token_counted_{base_name}")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ เสร็จสมบูรณ์!")
    print(f"📄 บันทึกไฟล์ที่มีการระบุ Token แล้วที่: {output_path}")

target_file = r"D:\CMU\Y4\LLM-PBE_VS\dea_result\prefix\results\language\informal\informal_meta.txt" 

add_token_count_to_report(target_file)