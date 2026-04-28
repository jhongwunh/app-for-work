import streamlit as st
import pandas as pd
import google.generativeai as genai
import datetime

# --- 頁面設定 ---
st.set_page_config(page_title="AI 智慧工作百科", layout="wide")

# --- API Key 設定 ---
# 建議做法：在 Streamlit Cloud 的 Secrets 設定中加入 API_KEY
# 這裡先提供一個輸入框讓你測試
with st.sidebar:
    st.header("🔑 設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)

st.title("🧠 我的工作智慧庫")
st.markdown("不用翻找筆記，直接問 AI 你的工作內容。")

# --- 資料庫功能 ---
DATA_FILE = "work_records.csv"
def load_data():
    try: return pd.read_csv(DATA_FILE)
    except: return pd.DataFrame(columns=["日期", "類型", "原始筆記", "PO號", "業務"])

df = load_data()

# --- 核心功能：AI 智慧整理與問答 ---
def ask_ai(query, context_notes):
    if not api_key:
        return "請先在左側輸入 API Key 才能使用 AI 功能。"
    
    model = genai.GenerativeModel('gemini-pro') # 使用最新的快速模型
    
    # 建立 Prompt：這是關鍵，要求 AI 從雜亂資料中整理
    prompt = f"""
    你是使用者的專業秘書。以下是從他過去的雜亂筆記（Notion/Sheets）中撈出的相關內容：
    ---
    {context_notes}
    ---
    請根據上述筆記回答問題："{query}"
    
    規則：
    1. 如果筆記裡有 SOP 流程，請整理成步驟。
    2. 如果有提到 PO 號碼，請列出該 PO 的負責業務與內容。
    3. 如果筆記內容很雜，請過濾掉廢話，只顯示對工作有幫助的重點。
    4. 如果筆記裡找不到答案，請老實說，不要瞎編。
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"發生錯誤: {str(e)}"

# --- 主介面：AI 問答區 ---
tab1, tab2, tab3 = st.tabs(["💬 智慧問答", "📝 快速記錄", "📁 檔案匯入"])

with tab1:
    user_query = st.text_input("你想從筆記中找什麼？", placeholder="例如：這張 PO 號是誰的專案？或是：這單的 SOP 是什麼？")
    
    if user_query:
        # 簡單的相關性過濾：從資料庫找包含關鍵字的筆記當作「背景資料」
        # 實務上可以用更精準的搜尋，這裡先用關鍵字比對
        search_keyword = user_query[:4] # 取前幾個字當關鍵字
        related_data = df[df['原始筆記'].str.contains(search_keyword, na=False, case=False)]
        context_text = "\n".join(related_data['原始筆記'].tolist()[:10]) # 取前 10 則相關筆記
        
        with st.spinner("AI 正在閱讀並整理資料..."):
            answer = ask_ai(user_query, context_text)
            st.markdown("### 💡 AI 整理結果")
            st.write(answer)

with tab2:
    # (保留之前的日常記錄功能...)
    pass

with tab3:
    # (保留之前的檔案匯入功能...)
    pass

# --- 底部原始資料檢視 ---
with st.expander("查看原始資料庫"):
    st.dataframe(df.sort_index(ascending=False))
