import streamlit as st
import pandas as pd
import google.generativeai as genai
import PyPDF2
from PIL import Image

# --- 1. 頁面基本設定 ---
st.set_page_config(page_title="AI 工作智慧百科", layout="wide", page_icon="🧠")

# --- 2. API Key 與模型設定 ---
# 優先從 Secrets 讀取，如果沒有則顯示警告
try:
    api_key = st.secrets["API_KEY"]
    genai.configure(api_key=api_key)
    # 使用你清單中確認可用的模型
    MODEL_NAME = 'models/gemini-2.5-flash'
except Exception:
    st.error("請在 Streamlit Secrets 中設定 API_KEY 或檢查 Key 是否正確。")
    st.stop()

# --- 3. 資料庫功能 ---
DATA_FILE = "work_records.csv"

def load_data():
    try:
        return pd.read_csv(DATA_FILE)
    except:
        return pd.DataFrame(columns=["日期", "類型", "原始筆記", "PO號", "業務", "來源"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# --- 4. AI 處理邏輯 ---
def ask_ai_with_media(query, context_notes, uploaded_media=None):
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    # 組合指令
    prompt = f"你是工作秘書。請根據提供的筆記資料回答：{query}\n\n【筆記資料】：\n{context_notes}"
    
    contents = [prompt]
    
    # 如果使用者有另外上傳圖檔/PDF，直接餵給 AI 看
    if uploaded_media:
        for file in uploaded_media:
            if file.type.startswith("image"):
                img = Image.open(file)
                contents.append(img)
            # 註：Gemini API 支援直接傳送檔案，這裡簡化處理圖片
    
    response = model.generate_content(contents)
    return response.text
# --- 5. 主介面設計 ---
st.title("🧠 我的工作智慧庫")
df = load_data()

tab1, tab2, tab3 = st.tabs(["💬 智慧整理問答", "📝 快速手動紀錄", "📁 檔案批次匯入"])

# --- Tab 1: 智慧整理問答 (相容舊資料版) ---
with tab1:
    user_query = st.text_input("想找什麼？(可配合下方上傳圖檔讓 AI 同步分析)")
    # 讓使用者可以臨時丟一張當初筆記裡的截圖給 AI 看
    extra_files = st.file_uploader("如果有相關圖片/PDF 也可以丟上來一起分析", 
                                   type=['png', 'jpg', 'jpeg', 'pdf'], 
                                   accept_multiple_files=True)
    
    if user_query:
        # 搜尋 CSV 裡的舊文字資料
        mask = df.astype(str).apply(lambda x: x.str.contains(user_query, case=False)).any(axis=1)
        related_data = df[mask].sort_index(ascending=False).head(20)
        context = "\n".join(related_data['原始筆記'].tolist())
        
        with st.spinner("AI 正在閱讀文字紀錄與分析圖片..."):
            answer = ask_ai_with_media(user_query, context, extra_files)
            st.write(answer)

# --- Tab 2: 手動紀錄 ---
with tab2:
    with st.form("manual_note", clear_on_submit=True):
        note_content = st.text_area("筆記內容：", placeholder="輸入要存下的事...")
        # 修正之前的錯誤名稱
        submit = st.form_submit_button("儲存筆記")
        
    if submit and note_content:
        new_row = {
            "日期": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "類型": "手動筆記",
            "原始筆記": note_content,
            "PO號": "無",
            "業務": "無",
            "來源": "手動輸入"
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("紀錄已儲存！")
        st.rerun()

# --- Tab 3: 檔案匯入 (支援多檔案上傳) ---
with tab3:
    st.subheader("匯入多個 Notion 或 CSV 檔案")
    # 關鍵修正：加上 accept_multiple_files=True
    uploaded_files = st.file_uploader("選擇檔案 (可多選)", type=['csv', 'md', 'txt'], accept_multiple_files=True)
    
    if uploaded_files and st.button("確認解析並匯入所有檔案"):
        new_entries = []
        
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name
            
            if filename.endswith('.csv'):
                try:
                    csv_df = pd.read_csv(uploaded_file)
                    for _, row in csv_df.iterrows():
                        # 把所有欄位的內容串起來，確保 AI 讀得到
                        content = " ".join(str(v) for v in row.values if str(v) != 'nan')
                        new_entries.append({
                            "日期": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "類型": "CSV匯入",
                            "原始筆記": content,
                            "PO號": "偵測中",
                            "業務": "待確認",
                            "來源": filename
                        })
                except Exception as e:
                    st.error(f"檔案 {filename} 讀取失敗: {e}")
            else:
                # 處理 Markdown 或 TXT
                raw_text = uploaded_file.getvalue().decode("utf-8")
                # 依據空行切分段落，保持內容完整性
                paragraphs = [p.strip() for p in raw_text.split('\n\n') if len(p.strip()) > 5]
                for p in paragraphs:
                    new_entries.append({
                        "日期": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "類型": "文件匯入",
                        "原始筆記": p,
                        "PO號": "偵測中",
                        "業務": "待確認",
                        "來源": filename
                    })
        
        if new_entries:
            df = pd.concat([df, pd.DataFrame(new_entries)], ignore_index=True)
            save_data(df)
            st.success(f"🎉 成功！已從 {len(uploaded_files)} 個檔案中匯入 {len(new_entries)} 條資料。")
            st.rerun()

# --- 6. 原始資料查看 ---
st.divider()
with st.expander("📊 查看/搜尋原始資料庫內容"):
    search_db = st.text_input("在資料庫中篩選文字：", key="db_search")
    if search_db:
        st.dataframe(df[df['原始筆記'].str.contains(search_db, case=False, na=False)], use_container_width=True)
    else:
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
