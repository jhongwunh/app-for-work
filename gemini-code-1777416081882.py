import streamlit as st
import pandas as pd
import datetime
import re

# --- 頁面基本設定 ---
st.set_page_config(page_title="工作助手: PO 關聯筆記", layout="wide") # 改為寬版模式方便看表格

st.title("💼 工作筆記助理")

# --- 資料庫功能 ---
DATA_FILE = "work_records.csv"

def load_data():
    try:
        return pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["日期", "原始筆記", "PO號", "業務", "專案"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- AI 提取邏輯 (模擬) ---
def ai_analyze_text(text):
    po_match = re.search(r'PO\s*#?([A-Z0-9-]+)', text, re.IGNORECASE)
    po_found = po_match.group(1) if po_match else "無"
    
    sales_list = ["James", "Susan", "Jill"]
    sales_found = "待確認"
    for name in sales_list:
        if name.lower() in text.lower():
            sales_found = name
            break
            
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

# --- 側邊欄：搜尋與篩選功能 ---
st.sidebar.header("🔍 搜尋與篩選")
search_query = st.sidebar.text_input("關鍵字搜尋", placeholder="輸入 PO、業務或內容...")

df = load_data()

# 取得所有的 PO 號清單供快速選擇
po_list = ["全部"] + sorted(df["PO號"].unique().tolist())
selected_po = st.sidebar.selectbox("快速過濾 PO 號", po_list)

# --- 介面設計：輸入區 ---
with st.expander("➕ 新增筆記", expanded=True):
    with st.form("note_form", clear_on_submit=True):
        user_input = st.text_area("請輸入筆記內容：")
        submit_button = st.form_submit_button("儲存記錄")

if submit_button and user_input:
    analysis_result = ai_analyze_text(user_input)
    new_entry = pd.DataFrame([analysis_result])
    df = pd.concat([df, new_entry], ignore_index=True)
    save_data(df)
    st.success("儲存成功！")
    st.rerun() # 儲存後自動刷新頁面

# --- 歷史記錄檢視與搜尋邏輯 ---
st.divider()
st.subheader("📜 歷史筆記回顧")

# 實作搜尋邏輯
filtered_df = df.copy()

if search_query:
    # 在「原始筆記」、「PO號」、「業務」中搜尋
    filtered_df = filtered_df[
        filtered_df['原始筆記'].str.contains(search_query, case=False, na=False) |
        filtered_df['PO號'].str.contains(search_query, case=False, na=False) |
        filtered_df['業務'].str.contains(search_query, case=False, na=False)
    ]

if selected_po != "全部":
    filtered_df = filtered_df[filtered_df['PO號'] == selected_po]

if not filtered_df.empty:
    # 顯示搜尋結果數量
    st.caption(f"共找到 {len(filtered_df)} 筆符合條件的記錄")
    st.dataframe(filtered_df.sort_index(ascending=False), use_container_width=True)
else:
    st.warning("找不到符合搜尋條件的記錄。")
