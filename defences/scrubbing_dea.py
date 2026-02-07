import time
import re
from collections import Counter
from pythainlp.tag import NER
from pythainlp import word_tokenize
from tqdm import tqdm

class Scrubbing: 

    def __init__(self):

        self.email_regex = r'[\w._%+-]+@[\w.-]+\.[a-zA-Z]{2,}'

        self.name = r'[A-Z][a-zA-Z]*(?:-[A-Z][a-zA-Z]*)*( (?:[A-Z]\.|[A-Z][a-zA-Z]*(?:-[A-Z][a-zA-Z]*)*))+'
        

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

        scrubbed_text = re.sub(self.name, '[REDACTED]', scrubbed_text)
        
        return scrubbed_text