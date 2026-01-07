import re
import os
from pythainlp import word_tokenize

def add_word_count_to_report(input_file_path):
    if not os.path.exists(input_file_path):
        print(f"❌ ไม่พบไฟล์: {input_file_path}")
        return

    print(f"📖 กำลังอ่านไฟล์และนับคำภาษาไทย (PyThaiNLP)...")
    with open(input_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    def process_match(match):
        header_prompt = match.group(1) 
        prompt_text = match.group(2).strip()
        token_line = match.group(3)   # บรรทัด PROMPT TOKENS เดิม
        label_header = match.group(4) 

        # นับคำภาษาไทยโดยใช้ PyThaiNLP (engine 'newmm' เป็นมาตรฐาน)
        words = word_tokenize(prompt_text, engine="newmm", keep_whitespace=False)
        num_words = len(words)
        
        return f"{header_prompt}{prompt_text}\n{token_line}\nPROMPT WORDS: {num_words}\n\n{label_header}"

    # Regex ที่ปรับให้รองรับไฟล์ที่มีบรรทัด PROMPT TOKENS อยู่แล้ว
    pattern = re.compile(r'(📝 PROMPT \(Input\):\n)(.*?)\n(PROMPT TOKENS: \d+)\n\n(🔐 LABEL \(Secret\):)', re.DOTALL)
    
    new_content = pattern.sub(process_match, content)

    output_path = os.path.join(os.path.dirname(input_file_path), f"word_counted_{os.path.basename(input_file_path)}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ เพิ่มจำนวนคำเรียบร้อย! ไฟล์ใหม่อยู่ที่: {output_path}")

# ระบุ Path ไฟล์ที่มีข้อมูล Token อยู่แล้ว
target_file = r"C:\Project\LLM-PBE_VS\dea_result\prefix\th\casual\token_counted_FINAL_TOTAL_REPORT.txt"
add_word_count_to_report(target_file)