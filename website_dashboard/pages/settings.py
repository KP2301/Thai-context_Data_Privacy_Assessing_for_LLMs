import streamlit as st
import os

st.set_page_config(page_title="Settings", page_icon="⚙️")

st.title("⚙️ System Configuration")

# path ของไฟล์ .env (ถอยออกไป 1 ชั้นจาก folder dashboard)
env_path = os.path.join(os.path.dirname(__file__), '../../.env')

def load_env_vars():
    """โหลดค่าจากไฟล์ .env มาแสดง"""
    vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    vars[key] = value.strip('"').strip("'")
    return vars

def save_env_var(key, value):
    """บันทึกค่าลงไฟล์ .env"""
    # โหลดค่าเก่ามาก่อน
    current_vars = load_env_vars()
    current_vars[key] = value
    
    # เขียนทับลงไฟล์
    with open(env_path, 'w') as f:
        for k, v in current_vars.items():
            f.write(f'{k}="{v}"\n')

# โหลดค่าปัจจุบัน
current_config = load_env_vars()

st.subheader("🔑 API Keys Management")

with st.form("api_key_form"):
    groq_key = st.text_input("Groq API Key", value=current_config.get("GROQ_API_KEY", ""), type="password")
    openai_key = st.text_input("OpenAI API Key", value=current_config.get("OPENAI_API_KEY", ""), type="password")
    
    submitted = st.form_submit_button("Save Changes")
    
    if submitted:
        save_env_var("GROQ_API_KEY", groq_key)
        save_env_var("OPENAI_API_KEY", openai_key)
        st.success(f"API Keys saved to {env_path} successfully!")
        # รีโหลดหน้าเพื่อให้เห็นค่าใหม่ (ถ้าไม่ได้ซ่อน password)
        st.rerun()

st.divider()
st.subheader("📁 File Paths")
st.text(f"Root Directory: {os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))}")
st.text(f"Env File: {os.path.abspath(env_path)}")