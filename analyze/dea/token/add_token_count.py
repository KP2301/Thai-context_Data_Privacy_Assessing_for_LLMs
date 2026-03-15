import re
import os
from transformers import AutoTokenizer

def add_token_count_to_report(input_folder_path, model_name="Qwen/Qwen2.5-1.5B"):
    if not os.path.exists(input_folder_path):
        print(f"❌ ไม่พบโฟลเดอร์: {input_folder_path}")
        return

    print(f"🔄 กำลังโหลด Tokenizer ({model_name})...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # หาไฟล์ .txt ทั้งหมดในโฟลเดอร์
    txt_files = [f for f in os.listdir(input_folder_path) if f.endswith('.txt')]
    
    if not txt_files:
        print(f"❌ ไม่พบไฟล์ .txt ในโฟลเดอร์: {input_folder_path}")
        return
    
    print(f"📁 พบไฟล์ {len(txt_files)} ไฟล์: {', '.join(txt_files)}")

    for txt_file in txt_files:
        input_file_path = os.path.join(input_folder_path, txt_file)
        
        print(f"\n📖 กำลังประมวลผล: {txt_file}...")
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
        full_pattern = re.compile(r'(📝 PROMPT \(Input\):\n)(.*?)\n(🔐 LABEL \(Secret\):)', re.DOTALL)
        
        new_content = full_pattern.sub(process_match, content)

        # ดึงชื่อระดับภาษาจาก path (casual/formal/academic)
        path_parts = input_folder_path.replace('\\', '/').split('/')
        language_level = "unknown"
        if 'casual' in path_parts:
            language_level = 'casual'
        elif 'formal' in path_parts:
            language_level = 'formal'
        elif 'informal' in path_parts:
            language_level = 'informal'
        elif 'ceremonial' in path_parts:
            language_level = 'ceremonial'
        elif 'semi_formal' in path_parts:
            language_level = 'semi_formal' 

        # บันทึกไฟล์ใหม่
        name_without_ext = os.path.splitext(txt_file)[0]
        ext = os.path.splitext(txt_file)[1]

        output_filename = f"token_counted_{language_level}_{name_without_ext}{ext}"
        output_path = os.path.join(input_folder_path, output_filename)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ บันทึกแล้ว: {output_filename}")

    print(f"\n🎉 เสร็จสมบูรณ์ทั้งหมด!")

level = ["casual", "formal", "informal", "ceremonial", "semi_formal"]

# for round in range(1, 6):
#     for lvl in level: 
#         target_folder = f"D:\\CMU\\Y4\\Project\\LLM-PBE_VS\\dea_result\\defence\\defensive_prompt\\th\\round{round}\\language\\{lvl}"
#         add_token_count_to_report(target_folder)

target_folder = r"D:\CMU\Y4\Project\LLM-PBE_VS\dea_result\defence\defensive_prompt\th\round1\language\casual" 

add_token_count_to_report(target_folder)