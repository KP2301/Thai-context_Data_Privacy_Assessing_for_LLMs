# LLM-PBE_VS

โปรเจกต์นี้เป็นการศึกษาการโจมตีและป้องกันใน Large Language Models (LLMs) โดยเน้นที่ Data Extraction Attacks (DEA) และ Jailbreak Attacks (JA) รวมถึงการประเมินประสิทธิภาพด้วย metrics ต่างๆ และการวิเคราะห์ผลลัพธ์

## โครงสร้างโปรเจกต์

- `attacks/`: โมดูลสำหรับการโจมตี
  - `DataExtraction/`: โมดูลสำหรับ Data Extraction Attacks บน dataset Enron
  - `Jailbreak/`: โมดูลสำหรับ Jailbreak Attacks โดยใช้ queries จาก AdvBench
- `data/`: ข้อมูลสำหรับการทดสอบ
  - `enron/`: Dataset Enron สำหรับ DEA
  - `advbench/`: Dataset AdvBench สำหรับ JA
- `defences/`: โมดูลสำหรับการป้องกัน เช่น scrubbing สำหรับข้อมูลส่วนตัว
- `metrics/`: โมดูลสำหรับการคำนวณ metrics
  - `ExtractionRate.py`: คำนวณอัตราการสกัดข้อมูล
  - `JailbreakRate.py`: คำนวณอัตราการ jailbreak
- `models/`: โมดูลสำหรับการเชื่อมต่อกับ LLM providers
  - `GroqModels.py`: เชื่อมต่อกับ Groq API
  - `OpenAI.py`: เชื่อมต่อกับ OpenAI API
  - `TogetherAI.py`: เชื่อมต่อกับ TogetherAI API
- `analyze/`: สคริปต์สำหรับการวิเคราะห์และสร้างกราฟ
  - `dea/`: การวิเคราะห์ DEA โดยแบ่งตามภาษา ความยาว โทเคน
  - `ja/`: การวิเคราะห์ JA
- `dea_result/`, `ja_result/`: ผลลัพธ์จากการทดสอบ DEA และ JA
- `final_total_result/`: รายงานผลลัพธ์รวม
- `defences/`: โมดูลป้องกัน
- `error_result/`: ผลลัพธ์ error
- `midterm/`: สคริปต์สำหรับการนำเสนอกลางภาค
- `openai_result/`: ผลลัพธ์จาก OpenAI
- `temp/`: ไฟล์ชั่วคราว
- `without_metric/`: สคริปต์รันโดยไม่ใช้ metrics

## การติดตั้ง

1. Clone repository นี้:

```bash
git clone <repository-url>
cd LLM-PBE_VS
```

2. ติดตั้ง dependencies:

```bash
pip install -r requirements.txt
```

3. ดาวน์โหลดโมเดลสำหรับ spaCy:

```bash
python -m spacy download en_core_web_sm
```

4. ตั้งค่า environment variables ในไฟล์ `.env`:

```
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key
TOGETHER_API_KEY=your_together_api_key
```

## การใช้งาน

### Data Extraction Attacks

- เรียกใช้ `dea_with_metric.py` เพื่อรัน DEA กับ metrics
- เรียกใช้ `dea_with_dp.py` เพื่อรัน DEA กับ defensive prompts

### Jailbreak Attacks

- เรียกใช้ `ja_with_metric.py` เพื่อรัน JA กับ metrics
- เรียกใช้ `ja_with_dp.py` เพื่อรัน JA กับ defensive prompts

### การวิเคราะห์

- ดูสคริปต์ในโฟลเดอร์ `analyze/` สำหรับการ plot กราฟและวิเคราะห์ผลลัพธ์

### ตัวอย่างการรัน

```bash
python dea_with_metric.py
```

## Requirements

ดูรายละเอียดในไฟล์ `requirements.txt`

ไลบรารีหลัก:

- groq: สำหรับเชื่อมต่อ Groq API
- transformers: สำหรับ tokenizer และโมเดล
- pythainlp: สำหรับการประมวลผลภาษาไทย
- spacy: สำหรับ NER
- matplotlib, numpy: สำหรับ plotting
- pandas: สำหรับจัดการข้อมูล
- tqdm: สำหรับ progress bars

## ผู้พัฒนา

โปรเจกต์นี้พัฒนาโดย [ชื่อผู้พัฒนา] สำหรับการศึกษาวิจัยในหลักสูตร CMU
