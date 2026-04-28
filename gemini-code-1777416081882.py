import streamlit as st
import pandas as pd
import datetime
import re

# --- 頁面設定 ---
st.set_page_config(page_title="工作助手: PO 關聯筆記", layout="wide")

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

# --- AI 提取邏輯 (這裡建議之後串接正式的 Gemini API 以達到最強效果) ---
def ai_analyze_text(text):
    # 模擬 AI 識別 PO 號 (支援常見格式)
    po_match = re.search(r'(PO|P/O)\s*#?([A-Z0-9-]+)', text, re.IGNORECASE)
    po_found = po_match.group(2) if po_match else "無"
    
    # 識別業務 (可根據您的同事名單修改)
    sales_list = ["James", "Susan", "Jill", "Kevin"]
    sales_found = "待確認"
    for name in sales_list:
        if name.lower() in text.lower():
            sales_found = name
            break
            
    # 識別專案
    project_found = "一般事項"
    if "ScanSource" in text: project_found = "ScanSource 專案"
    elif "MODEX" in text: project_found = "MODEX 展覽"
    elif "Unitech" in text: project_found = "Unitech 內部項目"

    return {
        "日期": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "原始筆記": text.strip(),
        "PO號": po_found,
        "業務": sales_found,
        "專案": project_found
    }

# --- 側邊欄：搜尋與篩選 ---
st.sidebar.header("🔍 搜尋與篩選")
search_query = st.sidebar.text_input("關鍵字搜尋")
df = load_data()
po_list = ["全部"] + sorted(df["PO號"].unique().tolist())
selected_po = st.sidebar.selectbox("過濾 PO 號", po_list)

# --- 主介面：分頁設計 ---
tab1, tab2 = st.tabs(["📝 日常記錄", "📥 Notion 資料匯入"])

with tab1:
    with st.form("note_form", clear_on_submit=True):
        user_input = st.text_area("請輸入新的筆記內容：")
        submit_button = st.form_submit_button("儲存記錄")

    if submit_button and user_input:
        analysis_result = ai_analyze_text(user_input)
        new_entry = pd.DataFrame([analysis_result])
        df = pd.concat([df, new_entry], ignore_index=True)
        save_data(df)
        st.success("儲存成功！")
        st.rerun()

with tab2:
    st.subheader("從 Notion 搬家")
    st.info("您可以直接從 Notion 頁面複製整段文字（包含 SOP、會議記錄或 PO 清單）並貼在下方。")
    notion_paste = st.text_area("請貼上 Notion 內容：", height=300)
    import_button = st.button("開始 AI 解析並匯入")

    if import_button and notion_paste:
        # 這裡的邏輯可以處理較長的文字塊，嘗試切分段落
        paragraphs = [p for p in notion_paste.split('\n\n') if len(p.strip()) > 5]
        
        new_records = []
        with st.status("AI 正在解析資料...", expanded=True) as status:
            for p in paragraphs:
                st.write(f"正在處理段落: {p[:30]}...")
                res = ai_analyze_text(p)
                new_records.append(res)
            status.update(label="解析完成！", state="complete", expanded=False)
        
        if new_records:
            new_df = pd.DataFrame(new_records)
            df = pd.concat([df, new_df], ignore_index=True)
            save_data(df)
            st.success(f"已成功從 Notion 匯入 {len(new_records)} 條記錄！")
            st.rerun()

# --- 歷史記錄檢視 ---
st.divider()
st.subheader("📜 歷史資料庫")

filtered_df = df.copy()
if search_query:
    filtered_df = filtered_df[
        filtered_df['原始筆記'].str.contains(search_query, case=False, na=False) |
        filtered_df['PO號'].str.contains(search_query, case=False, na=False)
    ]
if selected_po != "全部":
    filtered_df = filtered_df[filtered_df['PO號'] == selected_po]

if not filtered_df.empty:
    st.dataframe(filtered_df.sort_index(ascending=False), use_container_width=True)
else:
    st.write("目前無資料。")
