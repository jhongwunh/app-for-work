import streamlit as st
import pandas as pd
import datetime
import re
import io

# --- 頁面設定 ---
st.set_page_config(page_title="工作助手: PO 關聯筆記", layout="wide")

st.title("💼 工作筆記助理")

# --- 資料庫功能 ---
DATA_FILE = "work_records.csv"

def load_data():
    try:
        return pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["日期", "類型", "原始筆記", "PO號", "業務", "專案"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- 核心 AI 提取邏輯 (這裡最適合放入 Gemini API) ---
def ai_analyze_text(text, filename="手動輸入"):
    # 這裡目前是基礎邏輯，建議之後換成 Gemini 以處理「雜七雜八」的內容
    po_match = re.search(r'(PO|P/O)\s*#?([A-Z0-9-]+)', text, re.IGNORECASE)
    po_found = po_match.group(2) if po_match else "無"
    
    # 自動判斷類型 (模擬 AI 分類)
    doc_type = "一般筆記"
    if "SOP" in text.upper() or "步驟" in text: doc_type = "SOP流程"
    elif "會議" in text or "討論" in text: doc_type = "會議記錄"
    elif "PO" in text.upper(): doc_type = "訂單/採購"
    
    sales_list = ["James", "Susan", "Jill", "Kevin"]
    sales_found = "待確認"
    for name in sales_list:
        if name.lower() in text.lower():
            sales_found = name
            break

    return {
        "日期": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "類型": doc_type,
        "原始筆記": text.strip(),
        "PO號": po_found,
        "業務": sales_found,
        "專案": "來自檔案: " + filename if filename != "手動輸入" else "手動新增"
    }

# --- 側邊欄：搜尋與篩選 ---
st.sidebar.header("🔍 搜尋與篩選")
search_query = st.sidebar.text_input("關鍵字搜尋")
df = load_data()
type_list = ["全部"] + sorted(df["類型"].unique().tolist())
selected_type = st.sidebar.selectbox("依類型過濾", type_list)

# --- 主介面：分頁設計 ---
tab1, tab2 = st.tabs(["📝 日常記錄", "📁 檔案批次匯入"])

with tab1:
    with st.form("note_form", clear_on_submit=True):
        user_input = st.text_area("請輸入筆記內容：")
        submit_button = st.form_submit_button("儲存記錄")
    if submit_button and user_input:
        res = ai_analyze_text(user_input)
        df = pd.concat([df, pd.DataFrame([res])], ignore_index=True)
        save_data(df)
        st.success("儲存成功！")
        st.rerun()

with tab2:
    st.subheader("批次匯入 Notion / Sheets 檔案")
    st.write("支援上傳 `.csv` 或 `.md` (Markdown) 檔案")
    
    uploaded_file = st.file_uploader("選擇檔案", type=['csv', 'md', 'txt'])
    
    if uploaded_file is not None:
        if st.button("開始解析並匯入"):
            new_records = []
            
            # 如果是 CSV (例如從 Google Sheets 匯出的)
            if uploaded_file.name.endswith('.csv'):
                tmp_df = pd.read_csv(uploaded_file)
                # 假設 CSV 的每一列都是一則記錄
                for _, row in tmp_df.iterrows():
                    content = " ".join(str(val) for val in row.values)
                    new_records.append(ai_analyze_text(content, uploaded_file.name))
            
            # 如果是 Markdown 或 TXT (例如從 Notion 匯出的頁面)
            else:
                stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
                content = stringio.read()
                # 簡單按段落切分
                paragraphs = [p for p in content.split('\n\n') if len(p.strip()) > 10]
                for p in paragraphs:
                    new_records.append(ai_analyze_text(p, uploaded_file.name))
            
            if new_records:
                df = pd.concat([df, pd.DataFrame(new_records)], ignore_index=True)
                save_data(df)
                st.success(f"成功從 {uploaded_file.name} 匯入 {len(new_records)} 條資料！")
                st.rerun()

# --- 歷史資料庫 ---
st.divider()
filtered_df = df.copy()
if search_query:
    filtered_df = filtered_df[filtered_df['原始筆記'].str.contains(search_query, case=False, na=False)]
if selected_type != "全部":
    filtered_df = filtered_df[filtered_df['類型'] == selected_type]

st.subheader(f"📜 歷史資料 ({len(filtered_df)} 筆)")
st.dataframe(filtered_df.sort_index(ascending=False), use_container_width=True)
