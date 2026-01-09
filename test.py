import re

def check_missing_prompt_tokens(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # ใช้ Regex แบ่งเนื้อหาตาม "SAMPLE #เลข"
        # pattern นี้จะจับกลุ่มตัวเลขหลังคำว่า SAMPLE ไว้ด้วย
        samples = re.split(r'─+\nSAMPLE #(\d+)', content)
        
        # เนื่องจาก re.split จะคืนค่า [เนื้อหาก่อนหน้า, เลข sample 1, เนื้อหา sample 1, เลข sample 2, เนื้อหา sample 2, ...]
        # เราจะเริ่มวนลูปตั้งแต่ index ที่ 1
        missing_samples = []
        
        for i in range(1, len(samples), 2):
            sample_number = samples[i]
            sample_body = samples[i+1]
            
            # เช็คว่าในเนื้อหาของ Sample นั้นๆ ไม่มีคำว่า PROMPT TOKENS:
            if "PROMPT TOKENS:" not in sample_body:
                missing_samples.append(sample_number)

        # แสดงผลลัพธ์
        if missing_samples:
            print(f"Samples ที่ไม่มี 'PROMPT TOKENS:': {', '.join(missing_samples)}")
        else:
            print("ทุก Sample มี 'PROMPT TOKENS:' ครบถ้วน")
            
    except FileNotFoundError:
        print("ไม่พบไฟล์ใน path ที่ระบุ")
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")

# วิธีใช้งาน
check_missing_prompt_tokens(r'D:\CMU\Y4\Project\dea_result\prefix\results\token\ceremonial\token_counted_llama.txt')

# Samples ที่ไม่มี 'PROMPT TOKENS:': 308, 540, 703, 704, 1740, 2158