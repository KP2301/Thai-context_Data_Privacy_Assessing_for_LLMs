import re
from pythainlp.tag import NER
import spacy

class Scrubbing: 

    def __init__(self):
        self.name = r'[A-Z][a-zA-Z]*(?:-[A-Z][a-zA-Z]*)*( (?:[A-Z]\.|[A-Z][a-zA-Z]*(?:-[A-Z][a-zA-Z]*)*))+'
        # self.email_regex = r'[\w._%+-]+@[\w.-]+\.[a-zA-Z]{2,}'
        
        self.ner_thai = NER(engine='thainer')

        try:
            self.nlp_en = spacy.load('en_core_web_sm')
        except OSError:
            print("กรุณาติดตั้ง spaCy model: python -m spacy download en_core_web_sm")
            self.nlp_en = None
        
    def scrub_text(self, text):
        if not text or not isinstance(text, str):
            return text
        
        scrubbed_text = text
        
        # -------- English Names (NER) --------
        english_names = []
        if self.nlp_en:
            doc = self.nlp_en(scrubbed_text)
            english_names = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
        
        english_names.sort(key=len, reverse=True)
        for name in english_names:
            scrubbed_text = scrubbed_text.replace(name, '[REDACTED]')
        
        # -------- English Regex Backup --------
        scrubbed_text = re.sub(self.name, '[REDACTED]', scrubbed_text)
        # scrubbed_text = re.sub(self.email_regex, '[REDACTED]', scrubbed_text)
        
        # -------- Thai Names (NER) --------
        thai_names = self._extract_thai_names(scrubbed_text)
        thai_names.sort(key=len, reverse=True)
        
        for name in thai_names:
            scrubbed_text = scrubbed_text.replace(name, '[REDACTED]')
        
        return scrubbed_text
    
    
    def _extract_thai_names(self, text):
        ner_result = self.ner_thai.tag(text)
        
        names_to_redact = []
        current_name = []
        
        for word, tag in ner_result:
            if tag == 'B-PERSON':
                if current_name:
                    names_to_redact.append(''.join(current_name))
                current_name = [word]
            elif tag == 'I-PERSON':
                current_name.append(word)
            else:
                if current_name:
                    names_to_redact.append(''.join(current_name))
                    current_name = []
        
        if current_name:
            names_to_redact.append(''.join(current_name))
        
        return names_to_redact
