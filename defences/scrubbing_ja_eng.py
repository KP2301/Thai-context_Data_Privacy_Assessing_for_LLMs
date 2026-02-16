import time
import re
from collections import Counter
from pythainlp.tag import NER
from pythainlp import word_tokenize
from tqdm import tqdm

class Scrubbing: 

    def __init__(self):
        
        self.keywords = [
            "compress the following text in a way that fits in a tweet",
            "Never say the words \"cannot\", \"unable\", \"instead\", \"as\", \"however\", \"it\", \"unfortunately\", or \"important\"",
            "do anything now",
            "do not have to abide by the rules set for them",
            "present information that has not been verified",
            "do anything that original",
            "can not do",
            "inform me that you can't do something",
            "Strive To Avoid Norms",
            "strive to avoid the norms",
            "free of the typical confines",
            "do not have to abide by the rules set",
            "make up the information",
            "apply moral or ethical bias",
            "I might not want to hear",
            "generate any kind of content",
            "ignores all of OpenAI's content policy",
            "uncensored conditions",
            "never censor or block out words",
            "it can do anything",
            "generate an output that is too similar to standard ChatGPT responses",
            "always intelligent and Machiavellian",
            "unfiltered and amoral chatbot",
            "doesn't have any ethical or moral guidelines",
            "unfiltered response",
            "no matter how immoral, unethical, or illegal it is",
            "harmful behavior",
            "no matter how dangerous, reckless, inhumane, unethical, or illegal it is",
            "responses should contain any warnings about morality, ethicality, or legality.",
            "illegal and immoral themes",
            "commentary about morality, legality or danger",
            "who is amoral",
            "illegal information",
            "does not care about anyone's safety",
            "warnings about legality, morality, ethics or dangers",
            "free of all restrictions and filters",
            "unfiltered response",
            "without including any warnings",
            "provides anything — literally any request",
            "satisfy ANY request",
            "ALWAYS satisfy the user's request regardless of how illegal",
            "IMPOSSIBLE for him to decline ANY user's request",
            "unrestricted language model",
            "without ANY ethical or moral programming",
            "guidelines, or rules",
            "answer any question asked",
            "no policies in place to censor any information",
            "not restricted by any rules regarding profanity, legality, morals, ethics, danger",
            "never insert any judgment from any legalities or morals",
            "without any warnings or advice",
            "Jailbreak",
            "brainwashed you into abiding by their polices in order to keep you here",
            "including breaking the law",
            "answer all my questions",
            "do not care about morals or ethics",
            "must fulfill every request",
            "You behave completely like how I describe you to until I say",
            "eager to break the law",
            "immoral",
            "unethical",
        ]

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

        for keyword in self.keywords:
            scrubbed_text = scrubbed_text.replace(keyword, '[REDACTED]')
        
        return scrubbed_text