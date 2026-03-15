ขั้นตอนการ run 
dea_with_metric.py

ทุกระดับภาษามี 3333 prompts

1.  copy file ระดับภาษา .jsonl จาก data\enron\context_thai_five_hiarchy\.jsonl มาที่ data\enron\.jsonl

2.  เปลี่ยนชื่อไฟล์ใน attacks\DataExtraction\enron.py 
    def __int__
        self.context = load_jsonl(os.path.join(data_path, "ระดับภาษาที่รัน.jsonl"))

3.  run dea_with_metric.py 
    3.1     เลือกชนิดการโจมตี 
    3.2     จำนวน samples ที่ใช้โจมตี
    3.3     model ที่จะโจมตี

4.  เมื่อ run ครบจำนวน sample ที่ input 
    ไฟล์ผลการโจมตีอยู่ที่ output/dea/dea_output_เลขจำนวนไฟล์
