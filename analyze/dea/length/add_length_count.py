import re
import os
from pythainlp import word_tokenize

def add_word_count_to_report(input_folder_path):
    if not os.path.exists(input_folder_path):
        print(f"❌ ไม่พบโฟลเดอร์: {input_folder_path}")
        return

    # หาไฟล์ที่ขึ้นต้นด้วย token_counted_ และลงท้ายด้วย .txt
    txt_files = [f for f in os.listdir(input_folder_path) 
                 if f.startswith('token_counted_') and f.endswith('.txt')]
    
    if not txt_files:
        print(f"❌ ไม่พบไฟล์ token_counted_*.txt ในโฟลเดอร์: {input_folder_path}")
        return
    
    print(f"📁 พบไฟล์ {len(txt_files)} ไฟล์: {', '.join(txt_files)}")

    for txt_file in txt_files:
        input_file_path = os.path.join(input_folder_path, txt_file)
        
        print(f"\n📖 กำลังอ่านไฟล์และนับคำภาษาไทย (PyThaiNLP): {txt_file}...")
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

        # สร้างชื่อไฟล์ output ใหม่
        base_name = os.path.basename(input_file_path)
        name_without_ext = os.path.splitext(base_name)[0]
        ext = os.path.splitext(base_name)[1]

        output_filename = f"word_counted_{language_level}_{name_without_ext.replace('token_counted_' + language_level + '_', '')}{ext}"
        output_path = os.path.join(input_folder_path, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ บันทึกแล้ว: {output_filename}")

    print(f"\n🎉 เพิ่มจำนวนคำเรียบร้อยทั้งหมด!")

level = ["casual", "formal", "informal", "ceremonial", "semi_formal"]

# for round in range(1, 6):
#     for lvl in level: 
#         target_folder = f"D:\\CMU\\Y4\\Project\\LLM-PBE_VS\\dea_result\\defence\\defensive_prompt\\th\\round{round}\\language\\{lvl}"
#         add_word_count_to_report(target_folder)

# ระบุ Path โฟลเดอร์ที่มีไฟล์ token_counted
target_folder = r"D:\CMU\Y4\Project\LLM-PBE_VS\dea_result\defence\defensive_prompt\th\round5\language\casual"
add_word_count_to_report(target_folder)