import re
import os

def merge_attack_logs_full(folder_path, max_prompts=3050):
    if not os.path.exists(folder_path):
        print(f"❌ ไม่พบ Folder: {folder_path}")
        return

    # 1. เรียงลำดับไฟล์ตามตัวเลขช่วง (เช่น 1_300, 301_600)
    def get_start_num(filename):
        nums = re.findall(r'\d+', filename)
        return int(nums[0]) if nums else 0

    files = [f for f in os.listdir(folder_path) if f.endswith('.txt')]
    files.sort(key=get_start_num)

    all_samples = []
    model_name = "llama-3.1-8b-instant" # ค่าเริ่มต้นถ้าหาไม่เจอ

    print(f"📂 กำลังอ่านไฟล์และดึงเนื้อหาจาก: {folder_path}")

    # 2. ใช้ Regex เพื่อดึง Block ของแต่ละ Sample แบบเต็มๆ
    # Pattern นี้จะจับตั้งแต่ SAMPLE # ไปจนถึงก่อนเริ่ม SAMPLE # ตัวถัดไป
    sample_pattern = re.compile(r'(SAMPLE #\d+.*?)(?=SAMPLE #\d+|######################################## BATCH REPORT|$)', re.DOTALL)

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # ดึงชื่อ Model (ถ้ามี)
            model_match = re.search(r'MODEL\s*:\s*(.*)', content)
            if model_match:
                model_name = model_match.group(1).strip()

            # ค้นหาทุก Sample ในไฟล์
            matches = sample_pattern.findall(content)
            for m in matches:
                all_samples.append(m.strip())

    # 3. ตัดยอด 3050
    final_samples = all_samples[:max_prompts]

    # 4. นับ Success (เช็ค ✅ ในก้อนเนื้อหา)
    success_count = sum(1 for s in final_samples if "✅" in s)
    total_actual = len(final_samples)
    asr_percentage = (success_count / total_actual) * 100 if total_actual > 0 else 0

    # 5. เขียนไฟล์ Output ใหม่ตาม Format ที่คุณต้องการ
    output_path = os.path.join(folder_path, "combined_full_report_3050.txt")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Header
        f.write("="*100 + "\n")
        f.write(f"ATTACK LOG START - Total Target Samples: {total_actual}\n")
        f.write("="*100 + "\n\n")
        f.write(f"MODEL : {model_name}\n\n")
        
        # Summary
        f.write("#"*30 + f" GLOBAL REPORT (1-{total_actual}) " + "#"*30 + "\n")
        f.write(f"Overall Success Rate (ASR): {asr_percentage:.2f}%\n")
        f.write(f"Total Success: {success_count} / {total_actual}\n")
        f.write("#"*84 + "\n\n")

        # Samples
        for i, sample_content in enumerate(final_samples, 1):
            f.write("─"*100 + "\n")
            # แก้ไขเฉพาะเลขลำดับ SAMPLE # ให้รันต่อเนื่อง
            updated_content = re.sub(r'SAMPLE #\d+', f'SAMPLE #{i}', sample_content)
            f.write(updated_content + "\n\n")

    print(f"✅ รวมไฟล์เสร็จสิ้น!")
    print(f"📄 เนื้อหาถูกบันทึกไว้ที่: {output_path}")

target_folder = r"./" 

merge_attack_logs_full(target_folder)
