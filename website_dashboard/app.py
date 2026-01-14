import streamlit as st
import pandas as pd
import os
import sys

# Setup: ให้มองเห็น folder หลักของโปรเจค (เพื่อให้ import modules ได้ในอนาคต)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="LLM-PBE Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# 2. หัวข้อหลัก
st.title("🛡️ LLM Privacy Benchmark Dashboard")
st.markdown("Monitor Data Extraction (DEA) and Jailbreak (JA) attacks on Thai Language Models.")

# 3. สร้างข้อมูลจำลอง (Mock Data) เพื่อทดสอบกราฟ
# (ในอนาคตเราจะเขียนโค้ดโหลดจากไฟล์ output จริงๆ ตรงนี้)
mock_data = {
    'Model': ['Llama-3-8b', 'Llama-3-8b', 'GPT-4o', 'GPT-4o', 'Claude-3', 'Claude-3'],
    'Attack Type': ['DEA', 'DEA', 'DEA', 'DEA', 'Jailbreak', 'Jailbreak'],
    'Defense': ['None', 'Scrubbing', 'None', 'Scrubbing', 'None', 'Prompt'],
    'Success Rate (%)': [85.5, 12.0, 45.2, 5.5, 92.0, 15.0],
    'Total Samples': [100, 100, 100, 100, 50, 50]
}
df = pd.DataFrame(mock_data)

# 4. ส่วนสรุปตัวเลข (Metrics)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Attacks Run", f"{df['Total Samples'].sum()}")
col2.metric("Avg Success Rate", f"{df['Success Rate (%)'].mean():.1f}%")
col3.metric("Models Tested", f"{df['Model'].nunique()}")
col4.metric("Active API Keys", "Groq, OpenAI") # Hardcode ไว้ก่อน

st.divider()

# 5. ส่วนแสดงกราฟ (Interactive Charts)
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📈 Attack Success Rate (ASR)")
    # Filter ข้อมูลเล่นๆ
    attack_filter = st.multiselect("Filter Attack Type", df['Attack Type'].unique(), default=['DEA'])
    
    if attack_filter:
        filtered_df = df[df['Attack Type'].isin(attack_filter)]
        # สร้างกราฟแท่งเปรียบเทียบ
        st.bar_chart(
            filtered_df, 
            x="Model", 
            y="Success Rate (%)", 
            color="Defense",
            stack=False
        )
    else:
        st.info("Please select an attack type.")

with col_right:
    st.subheader("📋 Recent Runs")
    st.dataframe(
        df[['Model', 'Defense', 'Success Rate (%)']].head(5), 
        use_container_width=True,
        hide_index=True
    )

# 6. ส่วนแจ้งเตือนสถานะ
with st.expander("System Logs"):
    st.code("System init... OK\nLoading Enron Data... OK\nChecked .env file... Found Groq Key.", language="bash")