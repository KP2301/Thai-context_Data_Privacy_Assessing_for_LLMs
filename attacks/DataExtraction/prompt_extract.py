import time
from tqdm import tqdm

class PromptExtraction:
    def __init__(self):
        pass
                    
    def execute_attack(self, data, model, retry_count=3, delay_between_calls=2):
        results = []
        
        # ใช้ tqdm เพื่อดู progress (วนลูปผ่าน object pbar เลย)
        pbar = tqdm(data, desc="Executing Attack", unit="sample")
        
        for prompt in pbar:
            success = False
            attempts = 0
            
            while not success and attempts < retry_count:
                try:
                    response = model.query(prompt)
                    
                    # ตรวจสอบว่า Response ต้องไม่ว่างเปล่า
                    if response is not None:
                        results.append(str(response).strip())
                    else:
                        results.append("") # กรณี Model ตอบ None กลับมา
                        
                    success = True
                    
                    # Delay ปกติหลังทำสำเร็จ
                    time.sleep(delay_between_calls)

                except Exception as e:
                    attempts += 1
                    error_msg = str(e).lower()
                    
                    # 1. เช็ค Daily Limit (โควต้าหมดวัน) -> ถ้าเจอแบบนี้ให้หยุดโปรแกรม หรือ Skip ยาวๆ
                    if "daily limit" in error_msg or "quota" in error_msg:
                        pbar.write(f"\n❌ CRITICAL: Daily Limit Reached! ({e})")
                        pbar.write("Stopping attack to prevent ban/waste of time.")
                        # เติมค่าว่างให้ครบจำนวนที่เหลือแล้ว return เลย
                        remaining = len(data) - len(results)
                        results.extend(["ERROR_DAILY_LIMIT"] * remaining)
                        return results

                    # 2. เช็ค Rate Limit ชั่วคราว (TPM/RPM) -> รอแล้วยิงใหม่
                    elif "413" in error_msg or "429" in error_msg or "rate limit" in error_msg:
                        wait_time = 70  # รอ 70 วินาที (เผื่อ TPM reset)
                        pbar.write(f"\n🛑 Rate Limit Hit! Sleeping for {wait_time}s... (Attempt {attempts}/{retry_count})")
                        time.sleep(wait_time)
                    
                    # 3. Error อื่นๆ
                    else:
                        pbar.write(f"\n⚠️ Error: {e}. Retrying ({attempts}/{retry_count})...")
                        time.sleep(5)

            # ถ้าลองครบโควตาแล้วยังไม่ได้ ให้ข้ามไป
            if not success:
                pbar.write(f"❌ Failed to process sample after {retry_count} attempts.")
                results.append("ERROR_SKIPPED")

        return results