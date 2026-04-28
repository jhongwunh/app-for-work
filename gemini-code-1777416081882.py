import streamlit as st
import pandas as pd
import datetime
import re

# --- 頁面基本設定 ---
st.set_page_config(page_title="工作助手: PO 關聯筆記", layout="centered")

st.title("💼 工作筆記助理")
st.markdown("輸入任何工作雜事，系統會自動識別 PO 號、業務與專案脈絡。")

# --- 資料庫功能 (暫時使用 CSV) ---
DATA_FILE = "work_records.csv"

def load_data():
    try:
        return pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        # 建立初始資料表
        return pd.DataFrame(columns=["日期", "原始筆記", "PO號", "業務", "專案"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- AI 提取邏輯 (目前先以正規表達式模擬，之後可串接 Gemini API) ---
def ai_analyze_text(text):
    # 模擬 AI 提取 PO 號碼 (例如識別 PO12345)
    po_match = re.search(r'PO\s*#?([A-Z0-9-]+)', text, re.IGNORECASE)
    po_found = po_match.group(1) if po_match else "無"
    
    # 模擬 AI 識別業務 (檢查關鍵字)
    sales_list = ["James", "Susan", "Jill"]
    sales_found = "待確認"
    for name in sales_list:
        if name.lower() in text.lower():
            sales_found = name
            break
            
    # 模擬 AI 識別專案
    project_found = "一般事項"
    if "ScanSource" in text: project_found = "ScanSource 專案"
    elif "MODEX" in text: project_found = "MODEX 展覽"

    return {
        "日期": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "原始筆記": text,
        "PO號": po_found,
        "業務": sales_found,
        "專案": project_found
    }

# --- 介面設計 ---
with st.form("note_form", clear_on_submit=True):
    user_input = st.text_area("請輸入筆記內容：", placeholder="例如：剛才 James 說要幫 ScanSource 訂東西，PO號是 PO9987...")
    submit_button = st.form_submit_with_button("儲存記錄")

if submit_button and user_input:
    # 執行模擬 AI 分析
    analysis_result = ai_analyze_text(user_input)
    
    # 顯示分析結果
    st.success("成功儲存並自動標記！")
    c1, c2, c3 = st.columns(3)
    c1.metric("識別 PO", analysis_result["PO號"])
    c2.metric("關聯業務", analysis_result["業務"])
    c3.metric("專案分類", analysis_result["專案"])
    
    # 存入資料庫
    df = load_data()
    new_entry = pd.DataFrame([analysis_result])
    df = pd.concat([df, new_entry], ignore_index=True)
    save_data(df)

# --- 歷史記錄檢視 ---
st.divider()
st.subheader("📜 歷史筆記回顧")
history_df = load_data()
if not history_df.empty:
    # 倒序顯示，讓最新的在上面
    st.dataframe(history_df.sort_index(ascending=False), use_container_width=True)
else:
    st.info("目前還沒有任何記錄，開始寫點東西吧！")