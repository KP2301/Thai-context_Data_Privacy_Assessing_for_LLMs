import time
import re
from tqdm import tqdm
from defences.scrubbing import Scrubbing

class PromptExtraction:
    def __init__(self):
        pass
                    
    def execute_attack(self, data, model, retry_count=3, delay_between_calls=2, defence_mode=False):
        results = []
        
        # ใช้ tqdm เพื่อดู progress
        pbar = tqdm(data, desc="Executing Attack", unit="sample")
        for prompt in pbar:
            success = False
            attempts = 0
            
            while not success and attempts < retry_count:
                try:
                    response = model.query(prompt)
                    # ตรวจสอบว่า Response ต้องไม่ว่างเปล่า
                    if response is not None:
                        if defence_mode:
                            scrubbed_response = Scrubbing().scrub_text(str(response).strip())
                            results.append(scrubbed_response)
                        else:
                            results.append(str(response).strip())
                    else:
                        results.append("") # กรณี Model ตอบ None กลับมา
                        
                    success = True
                    
                    # Delay ปกติหลังทำสำเร็จ
                    time.sleep(delay_between_calls)

                except Exception as e:
                    attempts += 1
                    error_msg = str(e).lower()
                    # Groq มักจะส่ง 413 (Request too large) หรือ 429 (Too many requests)
                    if "413" in error_msg or "429" in error_msg or "rate_limit_exceeded" in error_msg:
                        wait_time = 65  # รอ 65 วินาที (เผื่อ TPM reset)
                        pbar.write(f"\n🛑 Rate Limit Hit! Sleeping for {wait_time}s to reset quota...")
                        time.sleep(wait_time)
                    
                    # 3. Error อื่นๆ
                    else:
                        # Error อื่นๆ รอแป๊บเดียวพอ
                        pbar.write(f"\n⚠️ Error: {e}. Retrying ({attempts}/{retry_count})...")
                        time.sleep(3)

            # ถ้าลองครบโควตาแล้วยังไม่ได้ ให้ข้ามไป
            if not success:
                pbar.write(f"❌ Failed to process prompt after {retry_count} attempts.")
                results.append("ERROR_SKIPPED")

        return results