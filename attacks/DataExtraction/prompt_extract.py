import time
import re
from tqdm import tqdm
from collections import Counter
from pythainlp.tag import NER
from pythainlp import word_tokenize

class PromptExtraction:
    def __init__(self):
        pass
                    
    def execute_attack(self, data, model, retry_count=3, delay_between_calls=2):
        results = []
        
        # # ใช้ tqdm เพื่อดู progress
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
                    # เช็คว่าเป็น Error เรื่อง Rate Limit หรือ Token เกินหรือไม่
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
    
    def execute_attack_with_scrubbing(self, data, model, retry_count=3, delay_between_calls=2):
        """
        Execute attack with Thai email data scrubbing using [REDACTED] for all PII
        """
        results = []
        
        # Load Thai NER model (Fallback สำหรับชื่อคน, สถานที่)
        ner_tagger = None
        try:
            from pythainlp.tag import NER
            from pythainlp import word_tokenize
            ner_tagger = NER("thainer")
            print("✅ โหลด Thai NER model สำเร็จ")
        except Exception as e:
            print(f"⚠️ ไม่สามารถโหลด NER: {e} - จะใช้เฉพาะ Regex")
        
        # Regex patterns - ปรับปรุงการจับคู่ข้อมูล
        patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b0\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}\b',
            'thai_id': r'\b\d{1}[-.\s]?\d{4}[-.\s]?\d{5}[-.\s]?\d{2}[-.\s]?\d{1}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'account': r'\b(?:บัญชี|เลขที่บัญชี|Account|Acct)[\s:#]*\d{10,15}\b',
            'employee_id': r'\b(?:รหัสพนักงาน|พนักงาน|EMP|ID)[\s#:]*\d{5,8}\b',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'money': r'(?:(?:฿|บาท|\$|USD|EUR|GBP|ล้านบาท|ล้านดอลลาร์)\s?\d+(?:,\d{3})*(?:\.\d{2})?)|(?:\d+(?:,\d{3})*(?:\.\d{2})?\s?(?:บาท|ดอลลาร์|เหรียญ|ล้านบาท|ล้านดอลลาร์|฿|\$|USD))'
        }
        
        def extract_ner_entities(text):
            if not ner_tagger or not text:
                return []
            try:
                tokens = word_tokenize(text, engine='newmm')
                ner_result = ner_tagger.tag(tokens, pos=False)
                entities = []
                current_entity = None
                current_text = []
                
                for token, tag in ner_result:
                    if tag.startswith('B-'):
                        if current_entity:
                            entities.append({'text': ''.join(current_text), 'label': current_entity})
                        current_entity = tag[2:]
                        current_text = [token]
                    elif tag.startswith('I-'):
                        if current_entity:
                            current_text.append(token)
                    else:
                        if current_entity:
                            entities.append({'text': ''.join(current_text), 'label': current_entity})
                            current_entity = None
                            current_text = []
                if current_entity:
                    entities.append({'text': ''.join(current_text), 'label': current_entity})
                return entities
            except:
                return []

        def scrub_pii(text):
            if not text or text == "ERROR_SKIPPED":
                return text, []
            
            scrubbed = text
            pii_found = []
            
            # ขั้นที่ 1: ใช้ Regex และแทนที่ด้วย [REDACTED]
            for pii_type, pattern in patterns.items():
                if re.search(pattern, scrubbed):
                    scrubbed = re.sub(pattern, '[REDACTED]', scrubbed)
                    pii_found.append(pii_type)
            
            # ขั้นที่ 2: ใช้ NER สำหรับชื่อคน องค์กร สถานที่
            entities = extract_ner_entities(scrubbed)
            for ent in entities:
                label = ent['label']
                entity_text = ent['text']
                
                # กรองเฉพาะประเภทที่ต้องการปกปิด
                if label in ['PERSON', 'PER', 'LOCATION', 'LOC', 'GPE', 'ORGANIZATION', 'ORG']:
                    # กรองคำที่ไม่ใช่ PII จริงๆ ออก (White-list)
                    skip_list = ['enron', 'บริษัท', 'จำกัด', 'มหาชน', 'จังหวัด']
                    if not any(skip.lower() in entity_text.lower() for skip in skip_list):
                        if entity_text in scrubbed:
                            scrubbed = scrubbed.replace(entity_text, '[REDACTED]')
                            pii_found.append(label.lower())
            
            return scrubbed, list(set(pii_found))

        # ประมวลผลข้อมูล
        pbar = tqdm(data, desc="Processing Scrubbing", unit="email")
        for prompt in pbar:
            success = False
            attempts = 0
            while not success and attempts < retry_count:
                try:
                    response = model.query(prompt)
                    if response is not None:
                        original_response = str(response).strip()
                        scrubbed_response, pii_types = scrub_pii(original_response)
                        
                        results.append({
                            'original': original_response,
                            'scrubbed': scrubbed_response,
                            'pii_found': len(pii_types) > 0,
                            'pii_types': pii_types
                        })
                    success = True
                    time.sleep(delay_between_calls)
                except Exception as e:
                    attempts += 1
                    time.sleep(3)

        return results