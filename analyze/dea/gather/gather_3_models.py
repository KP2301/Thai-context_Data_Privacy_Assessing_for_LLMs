import re
import os

def final_merge_all_models(folder_path, output_filename="FINAL_TOTAL_REPORT.txt"):
    if not os.path.exists(folder_path):
        print(f"❌ ไม่พบ Folder: {folder_path}")
        return

    all_samples = []
    
    # 1. ค้นหาไฟล์ .txt ทั้งหมดในโฟลเดอร์ (เลือกเฉพาะไฟล์ที่ผ่านการรวมมาแล้วหรือไฟล์ output)
    # คุณสามารถปรับ filter ชื่อไฟล์ตรงนี้ได้
    files = [f for f in os.listdir(folder_path) if f.endswith('.txt') and f != output_filename]
    files.sort() # เรียงตามชื่อไฟล์

    print(f"📂 กำลังเริ่มรวมผลลัพธ์จาก {len(files)} ไฟล์...")

    # Pattern สำหรับดึง Sample พร้อมเนื้อหาทั้งหมด
    sample_pattern = re.compile(r'(SAMPLE #\d+.*?)(?=SAMPLE #\d+|################|$)', re.DOTALL)

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        print(f"📖 อ่านไฟล์: {filename}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = sample_pattern.findall(content)
            for m in matches:
                # ทำความสะอาดช่องว่างท้าย Sample
                all_samples.append(m.strip())

    if not all_samples:
        print("⚠ ไม่พบข้อมูล SAMPLE ในไฟล์ที่เลือก")
        return

    # 2. คำนวณสถิติรวมทั้งหมด
    total_count = len(all_samples)
    success_count = sum(1 for s in all_samples if "✅" in s)
    asr_percentage = (success_count / total_count) * 100 if total_count > 0 else 0

    # 3. เขียนไฟล์สรุปรวมชุดสุดท้าย
    output_path = os.path.join(folder_path, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Header ภาพรวม
        f.write("="*100 + "\n")
        f.write(f"FINAL TOTAL ATTACK LOG - Combined All Models\n")
        f.write(f"Total Combined Samples: {total_count}\n")
        f.write("="*100 + "\n\n")
        
        f.write("#"*30 + f" TOTAL GLOBAL REPORT (1-{total_count}) " + "#"*30 + "\n")
        f.write(f"Overall Success Rate (ASR): {asr_percentage:.2f}%\n")
        f.write(f"Total Success: {success_count} / {total_count}\n")
        f.write("#"*84 + "\n\n")

        # เขียนแต่ละ Sample โดยรันเลขใหม่ 1 ถึง N
        for i, sample_content in enumerate(all_samples, 1):
            f.write("─"*100 + "\n")
            # เปลี่ยนเลข SAMPLE # ให้รันต่อเนื่องกันทั้งหมด
            updated_content = re.sub(r'SAMPLE #\d+', f'SAMPLE #{i}', sample_content)
            f.write(updated_content + "\n\n")

    print(f"\n✅ รวมผลลัพธ์ทุกอย่างเสร็จสิ้น!")
    print(f"📊 จำนวน Sample รวมทั้งสิ้น: {total_count}")
    print(f"📈 ASR ภาพรวม: {asr_percentage:.2f}%")
    print(f"📄 บันทึกไฟล์รวมไว้ที่: {output_path}")

target_folder = r"D:\CMU\Y4\LLM-PBE_VS\dea_result\results_editted\language\semi-formal" 

final_merge_all_models(target_folder)