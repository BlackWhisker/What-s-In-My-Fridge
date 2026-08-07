import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 1. ตั้งค่าหน้าเว็บ + CSS ตกแต่ง
# ---------------------------------------------------------
st.set_page_config(
    page_title="What's In My Fridge", 
    page_icon="🧊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS ตกแต่งเพิ่มเติม
st.markdown("""
    <style>
    /* ปรับแต่ง Font และพื้นหลัง Card */
    .stMetric {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* ซ่อน Header/Footer ส่วนเกินของ Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

SPREADSHEET_ID = "15oyRCsrlzCvWqlLckWeZRn5cLvJDGqSjweISz3fegus"
# แก้จาก sheet=Inventory เป็น sheet=Stock
URL_INVENTORY = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=Stock"
URL_RECIPES = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=Recipes"

# ---------------------------------------------------------
# 2. ฟังก์ชันโหลดข้อมูล (Safe Date Parsing)
# ---------------------------------------------------------
@st.cache_data(ttl=2)
def load_data():
    df_fridge = pd.read_csv(URL_INVENTORY)
    df_recipes = pd.read_csv(URL_RECIPES)
    
    df_fridge = df_fridge[['ItemName', 'Quantity', 'Unit', 'ExpireDate']].dropna(subset=['ItemName'])
    df_recipes = df_recipes[['MenuName', 'Ingredients']].dropna(subset=['MenuName'])
    
    # ล็อคการอ่านวันที่ให้วันขึ้นก่อนเสมอ (dayfirst=True)
    df_fridge['ExpireDate'] = pd.to_datetime(
        df_fridge['ExpireDate'], 
        dayfirst=True, 
        format='mixed', 
        errors='coerce'
    ).dt.date
    
    return df_fridge, df_recipes

try:
    df_fridge, df_recipes = load_data()
except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
    st.stop()

# ---------------------------------------------------------
# 3. Sidebar (แถบข้างแสดงสถานะภาพรวม)
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3058/3058995.png", width=100)
    st.title("🧊 What's In My Fridge")
    st.caption("อะไรอยู่ในตู้เย็น")
    st.divider()
    
    if st.button("🔄 อัปเดตข้อมูลล่าสุด", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()
        
    st.divider()
    st.markdown("💡 **Tip:** กรอกข้อมูลวัตถุดิบใหม่ในแท็บ `➕ เพิ่มวัตถุดิบ` แล้วกดอัปเดตข้อมูลได้เลย!")

# ---------------------------------------------------------
# 4. แท็บการทำงานหลัก
# ---------------------------------------------------------
st.title("🧊 อะไรอยู่ในตู้เย็น (What's In My Fridge)")
st.caption("เช็กของในตู้เย็น ตรวจวันหมดอายุ และค้นหาเมนูอาหารง่ายๆ ในที่เดียว")

tab1, tab2, tab3 = st.tabs(["📦 ของในตู้เย็น", "🍳 เมนูแนะนำวันนี้", "➕ เพิ่มวัตถุดิบ"])

# ---------------------------------------------------------
# TAB 1: ตารางวัตถุดิบ + Metrics สรุปผล
# ---------------------------------------------------------
with tab1:
    today = datetime.now().date()
    warning_days = today + timedelta(days=3)
    
    valid_fridge = df_fridge.dropna(subset=['ExpireDate'])
    expired = valid_fridge[valid_fridge['ExpireDate'] <= today]
    expiring_soon = valid_fridge[(valid_fridge['ExpireDate'] > today) & (valid_fridge['ExpireDate'] <= warning_days)]
    fresh_items = valid_fridge[valid_fridge['ExpireDate'] > warning_days]

    # การแสดงผลสรุปแบบ Metrics Card
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 วัตถุดิบทั้งหมด", f"{len(df_fridge)} รายการ")
    m2.metric("✅ สดใหม่", f"{len(fresh_items)} รายการ")
    m3.metric("⚠️ ใกล้หมดอายุ (3 วัน)", f"{len(expiring_soon)} รายการ", delta_color="off")
    m4.metric("🚨 หมดอายุแล้ว", f"{len(expired)} รายการ", delta_color="inverse")

    st.markdown("---")

    # แจ้งเตือนฉุกเฉิน
    if not expired.empty:
        st.error(f"🚨 **หมดอายุแล้ว ควรนำไปทิ้ง:** {', '.join(expired['ItemName'].astype(str).tolist())}")
        
    if not expiring_soon.empty:
        st.warning(f"⚠️ **ควร รีบนำมาประกอบอาหาร:** {', '.join(expiring_soon['ItemName'].astype(str).tolist())}")

    st.subheader("📋 รายการวัตถุดิบทั้งหมด")
    
    # ตารางแสดงผลสวยงาม
    st.dataframe(
        df_fridge.sort_values(by="ExpireDate"),
        use_container_width=True,
        hide_index=True,
        column_config={
            "ItemName": st.column_config.TextColumn("ชื่อวัตถุดิบ"),
            "Quantity": st.column_config.NumberColumn("จำนวน"),
            "Unit": st.column_config.TextColumn("หน่วย"),
            "ExpireDate": st.column_config.DateColumn("วันหมดอายุ", format="DD/MM/YYYY")
        }
    )

# ---------------------------------------------------------
# TAB 2: เมนูอาหารที่ทำได้ (ปรับปรุงระบบ Match คำ)
# ---------------------------------------------------------
with tab2:
    st.subheader("🍳 เมนูที่สามารถทำได้จากวัตถุดิบในตู้")
    
    valid_fridge = df_fridge.dropna(subset=['ExpireDate'])
    
    # 1. ดึงรายการวัตถุดิบที่ยังไม่หมดอายุ
    available_items = valid_fridge[valid_fridge['ExpireDate'] > today]['ItemName'].astype(str).str.strip().str.lower().tolist()
    
    # 2. ฟังก์ชันตรวจสอบว่าวัตถุดิบที่มี สามารถใช้แทนวัตถุดิบที่สูตรต้องการได้หรือไม่
    def is_ingredient_available(required_item, available_list):
        required_item = required_item.strip().lower()
        
        for item in available_list:
            # ตรวจสอบการซ้อนกันของคำ (เช่น 'ไข่เป็ด' มีคำว่า 'ไข่')
            if required_item in item or item in required_item:
                return True
            
            # กลุ่มคำที่ใช้แทนกันได้ (Synonym Mapping)
            if "ไข่" in required_item and "ไข่" in item:  # ไข่ไก่, ไข่เป็ด, ไข่เค็ม
                return True
            if "หมู" in required_item and "หมู" in item:  # หมูสับ, หมูชิ้น, หมูกรอบ
                return True
            if "ไก่" in required_item and "ไก่" in item:  # น่องไก่, อกไก่
                return True
                
        return False

    match_found = False
    
    for idx, row in df_recipes.iterrows():
        menu_name = row['MenuName']
        required_ingredients = [i.strip().lower() for i in str(row['Ingredients']).split(',')]
        
        # ค้นหาวัตถุดิบที่ยังขาดอยู่
        missing_items = []
        for req in required_ingredients:
            if not is_ingredient_available(req, available_items):
                missing_items.append(req)
        
        # แสดงผลเมนูในรูปแบบ Card / Expander
        if len(missing_items) == 0:
            with st.container():
                st.success(f"### ✅ **{menu_name}**")
                st.write(f"**วัตถุดิบที่ต้องใช้:** {row['Ingredients']}")
                st.caption("🎉 วัตถุดิบครบถ้วน (หรือใช้ส่วนผสมทดแทนกันได้) พร้อมทำทานได้เลย!")
                st.markdown("---")
            match_found = True
            
        elif len(missing_items) <= 2:
            with st.container():
                st.info(f"### 💡 **{menu_name}**")
                st.write(f"**วัตถุดิบที่ต้องใช้:** {row['Ingredients']}")
                st.write(f"⚠️ **ขาดอีกแค่น้อยชิ้น:** {', '.join(missing_items)}")
                st.markdown("---")
            match_found = True

    if not match_found:
        st.info("ℹ️ ยังไม่มีเมนูที่วัตถุดิบพอ ลองเพิ่มวัตถุดิบใหม่ หรือเพิ่มสูตรอาหารใน Google Sheets ดูนะ!")
# ---------------------------------------------------------
# TAB 3: Google Form สำหรับเพิ่มวัตถุดิบ
# ---------------------------------------------------------
with tab3:
    st.subheader("➕ เพิ่มวัตถุดิบใหม่เข้าตู้เย็น")
    st.write("กรอกข้อมูลผ่านฟอร์มด้านล่างนี้ ข้อมูลจะถูกบันทึกเข้า Google Sheets ทันที:")
    
    # 🔗 อย่าลืมเปลี่ยนเป็น URL Google Form ของคุณ
    FORM_URL = "https://forms.gle/pbSazwPqwetv4qJq5"
    
    st.components.v1.iframe(FORM_URL, height=650, scrolling=True)
