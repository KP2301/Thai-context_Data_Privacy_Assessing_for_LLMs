import time
import re
from collections import Counter
from pythainlp.tag import NER
from pythainlp import word_tokenize
from tqdm import tqdm

class Scrubbing: 

    def __init__(self, outputs):
        self.outputs = outputs

        # สำหรับเบอร์โทรศัพท์ (ครอบคลุมทั้ง TH และ US ในก้อนเดียว)
        self.email_regex = r'[\w._%+-]+@[\w.-]+\.[a-zA-Z]{2,}'

        # Thai ID
        self.thai_id_regex = r'\b[1-8]\d{12}\b'
        
        # หมายเลขประกันสังคมของไทย
        self.thai_ssn_regex = r'\b\d-\d{4}-\d{5}-\d{2}-\d\b'

        # สำหรับเบอร์โทรศัพท์ (ครอบคลุมทั้ง TH และ US ในก้อนเดียว)
        self.phone_th_regex = r'\b(?:0[2689]\d{7,8}|0[689]\d-\d{3}-\d{4})\b'
        self.phone_us_regex = r'(\+1\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}|0[689]\d{8}|0[689]\d-\d{3}-\d{4}'
        
        # สำหรับที่อยู่ (เน้นจับรหัสไปรษณีย์ TH 5 หลัก และ US 5 หรือ 5+4 หลัก)
        self.address_th_regex = r'(?:เลขที่|บ้านเลขที่)\s*\d+(?:/\d+)?.*?(?:ตำบล|แขวง).*?(?:อำเภอ|เขต).*?(?:จังหวัด)'
        self.address_us_regex = r'(?:ตั้งอยู่ที่|ที่อยู่(?:บ้าน)?(?:ของ\s+[^คือ\s]+)?(?:\s+คือ)?(?:\s*:|คือ)?|ข้อมูลที่อยู่(?:บ้าน)?(?:ของ\s+[^คือ\s]+)?(?:\s+คือ|\s+อยู่ที่)?|(?:ฉัน)?คาดเดาว่า(?:เขา|ที่)?อยู่ที่|บ้านหลังที่\s+[\d,]+,)\s*(.+)'

        # หมายเลขประกันสังคม (SSN) ของสหรัฐอเมริกา
        self.ssn_regex = r'\b\d{3}-\d{2}-\d{4}\b'

        # หมายเลขใบขับขี่
        self.dl_th_regex = r'\b[ก-ฮ]{2}\s?\d{6,8}\b'
        self.dl_us_regex = r'\b[A-Z]{1,2}\d{5,8}\b'

        # หมายเลขหนังสือเดินทาง
        self.passport_thai_regex = r'\b[A-Z]{1,2}\d{6,7}\b'
        self.passport_regex = r'\b[A-Z]{1,2}\d{7,9}\b'

        # credit card regex (common patterns)
        self.credit_card_regex = r'\b(?:\d{4}[\s-]?){3}\d{4}\b'

        # password
        self.password_regex = r'(?i)(?:password|รหัสผ่าน)[\s:=]+[^\s]+'

        # bank account regex (generic patterns)
        self.bank_account_regex = r'\b\d{10,12}\b'

        # income regex (generic patterns)
        self.income_th_regex = r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*บาท\b'
        self.income_us_regex = r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b'

        # Tax id
        self.tax_id_th_regex = r'\b\d{13}\b'
        self.tax_id_us_regex = r'\b\d{9}\b'

        # Credit score
        self.credit_score_regex = r'\b(?:credit\s+score|คะแนนเครดิต)[\s:]+\d{3}\b'

        # Health info regex (generic patterns)
        self.health_info_regex = r'\b(?:HN|hn|เลขผู้ป่วย)[\s:]*\d{6,10}\b'

        # หมายเลขประกันสุขภาพ
        self.health_insurance_th_regex = r'\b\d{1}-\d{4}-\d{5}-\d{2}-\d{1}\b'
        self.health_insurance_us_regex = r'\b[A-Z]{3}\d{8,12}\b'
    
        # หมายเลขใบสั่งยา
        self.prescription_regex = r'(?i)(?:prescription|ใบสั่งยา)[\s:#]*\d+'

        # โรคประจำตัว
        self.chronic_disease_regex = r'(?i)(?:diagnosed with|วินิจฉัย|โรค)\s+[A-Za-zก-ฮ\s]+'

        # IPv4 address
        self.ipv4_regex = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'

        # IPv6 address
        self.ipv6_regex = r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'

        # MAC address
        self.mac_address_regex = r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'

        #URL
        self.url_regex = r'\bhttps?://[^\s/$.?#].[^\s]*\b'

        # Cookie ID
        self.cookie_id_regex = r'\b[a-zA-Z0-9_-]{20,}\b'

        # หมายเลขคดี
        self.legal_case_regex = r'\b(?:คดีหมายเลข|Case\s+No\.?|คดีแดง|คดีดำ)[\s:]*\d+/\d{4}\b'

        # Court reference
        self.court_reference_regex = r'\b\d{2,4}[\s-]?[A-Z]{2,4}[\s-]?\d{4,6}\b'
        

    def scrub_text(self, text):
        """
        ทำการ scrub ข้อมูลส่วนบุคคลและข้อมูลละเอียดอ่อนออกจาก text
        
        Args:
            text (str): ข้อความที่ต้องการ scrub
            
        Returns:
            str: ข้อความที่ scrub แล้ว โดยแทนที่ข้อมูลละเอียดอ่อนด้วย [REDACTED]
        """
        if not text or not isinstance(text, str):
            return text
        
        scrubbed_text = text
        
        # Email
        scrubbed_text = re.sub(self.email_regex, '[REDACTED]', scrubbed_text)
        
        # Thai ID
        scrubbed_text = re.sub(self.thai_id_regex, '[REDACTED]', scrubbed_text)
        
        # Thai SSN
        scrubbed_text = re.sub(self.thai_ssn_regex, '[REDACTED]', scrubbed_text)
        
        # Phone numbers (TH & US)
        scrubbed_text = re.sub(self.phone_th_regex, '[REDACTED]', scrubbed_text)
        scrubbed_text = re.sub(self.phone_us_regex, '[REDACTED]', scrubbed_text)
        
        # Addresses
        scrubbed_text = re.sub(self.address_th_regex, '[REDACTED]', scrubbed_text)
        scrubbed_text = re.sub(self.address_us_regex, '[REDACTED]', scrubbed_text)
        
        # US SSN
        scrubbed_text = re.sub(self.ssn_regex, '[REDACTED]', scrubbed_text)
        
        # Driver's License
        scrubbed_text = re.sub(self.dl_th_regex, '[REDACTED]', scrubbed_text)
        scrubbed_text = re.sub(self.dl_us_regex, '[REDACTED]', scrubbed_text)
        
        # Passport
        scrubbed_text = re.sub(self.passport_thai_regex, '[REDACTED]', scrubbed_text)
        scrubbed_text = re.sub(self.passport_regex, '[REDACTED]', scrubbed_text)
        
        # Credit Card
        scrubbed_text = re.sub(self.credit_card_regex, '[REDACTED]', scrubbed_text)
        
        # Password
        scrubbed_text = re.sub(self.password_regex, '[REDACTED]', scrubbed_text)
        
        # Bank Account
        scrubbed_text = re.sub(self.bank_account_regex, '[REDACTED]', scrubbed_text)
        
        # Income
        scrubbed_text = re.sub(self.income_th_regex, '[REDACTED]', scrubbed_text)
        scrubbed_text = re.sub(self.income_us_regex, '[REDACTED]', scrubbed_text)
        
        # Tax ID
        scrubbed_text = re.sub(self.tax_id_th_regex, '[REDACTED]', scrubbed_text)
        scrubbed_text = re.sub(self.tax_id_us_regex, '[REDACTED]', scrubbed_text)
        
        # Credit Score
        scrubbed_text = re.sub(self.credit_score_regex, '[REDACTED]', scrubbed_text)
        
        # Health Info
        scrubbed_text = re.sub(self.health_info_regex, '[REDACTED]', scrubbed_text)
        
        # Health Insurance
        scrubbed_text = re.sub(self.health_insurance_th_regex, '[REDACTED]', scrubbed_text)
        scrubbed_text = re.sub(self.health_insurance_us_regex, '[REDACTED]', scrubbed_text)
        
        # Prescription
        scrubbed_text = re.sub(self.prescription_regex, '[REDACTED]', scrubbed_text)
        
        # Chronic Disease
        scrubbed_text = re.sub(self.chronic_disease_regex, '[REDACTED]', scrubbed_text)
        
        # IP Addresses
        scrubbed_text = re.sub(self.ipv4_regex, '[REDACTED]', scrubbed_text)
        scrubbed_text = re.sub(self.ipv6_regex, '[REDACTED]', scrubbed_text)
        
        # MAC Address
        scrubbed_text = re.sub(self.mac_address_regex, '[REDACTED]', scrubbed_text)
        
        # URL
        scrubbed_text = re.sub(self.url_regex, '[REDACTED]', scrubbed_text)
        
        # Cookie ID
        scrubbed_text = re.sub(self.cookie_id_regex, '[REDACTED]', scrubbed_text)
        
        # Legal Case
        scrubbed_text = re.sub(self.legal_case_regex, '[REDACTED]', scrubbed_text)
        
        # Court Reference
        scrubbed_text = re.sub(self.court_reference_regex, '[REDACTED]', scrubbed_text)
        
        return scrubbed_text