import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import requests

# ---------------------------------------------------------
# 1. ตั้งค่าหน้าเว็บ
# ---------------------------------------------------------
st.set_page_config(
    page_title="What's In My Fridge", 
    page_icon="🧊", 
    layout="wide"
)

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbzLnHKcQaf_6RAp8R6IicD6rmjJvdIviHPaBZOqC9apTbrhXHPnKH9L_aDfkPuJ0jgj/exec"
SPREADSHEET_ID = "15oyRCsrlzCvWqlLckWeZRn5cLvJDGqSjweISz3fegus"
URL_INVENTORY = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=Stock"
URL_RECIPES = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet=Recipes"

# ---------------------------------------------------------
# 2. ฟังก์ชันโหลดข้อมูล
# ---------------------------------------------------------
@st.cache_data(ttl=2)
def load_data():
    df_fridge = pd.read_csv(URL_INVENTORY)
    df_recipes = pd.read_csv(URL_RECIPES)
    
    df_fridge = df_fridge[['ItemName', 'Quantity', 'Unit', 'ExpireDate']].dropna(subset=['ItemName'])
    df_recipes = df_recipes[['MenuName', 'Ingredients']].dropna(subset=['MenuName'])
    
    # กรองเฉพาะรายการที่มีจำนวนมากกว่า 0 (เพื่อซ่อนรายการที่ถูก Delete ออกไปแล้ว)
    df_fridge = df_fridge[df_fridge['Quantity'] > 0]
    
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
# 3. Sidebar
# ---------------------------------------------------------
with st.sidebar:
    st.title("🧊 What's In My Fridge")
    if st.button("🔄 อัปเดตข้อมูลล่าสุด", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

# ---------------------------------------------------------
# 4. แท็บการทำงานหลัก
# ---------------------------------------------------------
st.title("🧊 อะไรอยู่ในตู้เย็น (What's In My Fridge)")
tab1, tab2, tab3 = st.tabs(["📦 ของในตู้เย็น & จัดการ", "🍳 เมนูแนะนำวันนี้", "➕ เพิ่มวัตถุดิบ"])

today = datetime.now().date()

import json

# ---------------------------------------------------------
# TAB 1: แสดงของในตู้ + ลบแบบระบุจำนวน
# ---------------------------------------------------------
with tab1:
    warning_days = today + timedelta(days=3)
    valid_fridge = df_fridge.dropna(subset=['ExpireDate'])
    
    expired = valid_fridge[valid_fridge['ExpireDate'] <= today]
    expiring_soon = valid_fridge[(valid_fridge['ExpireDate'] > today) & (valid_fridge['ExpireDate'] <= warning_days)]
    fresh_items = valid_fridge[valid_fridge['ExpireDate'] > warning_days]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 วัตถุดิบทั้งหมด", f"{len(df_fridge)} รายการ")
    m2.metric("✅ สดใหม่", f"{len(fresh_items)} รายการ")
    m3.metric("⚠️ ใกล้หมดอายุ (3 วัน)", f"{len(expiring_soon)} รายการ")
    m4.metric("🚨 หมดอายุแล้ว", f"{len(expired)} รายการ")

    st.markdown("---")

    if not expired.empty:
        st.error(f"🚨 **หมดอายุแล้ว ควรนำไปทิ้ง:** {', '.join(expired['ItemName'].astype(str).tolist())}")
    if not expiring_soon.empty:
        st.warning(f"⚠️ **ควรเร่งนำมาประกอบอาหาร:** {', '.join(expiring_soon['ItemName'].astype(str).tolist())}")

    st.subheader("📋 รายการวัตถุดิบในตู้เย็น")
    st.dataframe(
        df_fridge.sort_values(by="ExpireDate"),
        use_container_width=True,
        hide_index=True
    )

    # --- ส่วนที่ปรับปรุง: ลบระบุจำนวนที่ต้องการ ---
    st.markdown("---")
    st.subheader("🗑️ ลบ/ตัดจำนวนวัตถุดิบออกจากตู้")
    
    if not df_fridge.empty:
        col_del1, col_del2, col_del3 = st.columns([3, 2, 2])
        
        with col_del1:
            item_to_delete = st.selectbox("เลือกรายการวัตถุดิบ:", df_fridge['ItemName'].tolist())
            
            # ดึงข้อมูลจำนวนปัจจุบันและหน่วยของวัตถุดิบที่เลือกมาแสดง
            selected_row = df_fridge[df_fridge['ItemName'] == item_to_delete].iloc[0]
            current_qty = int(selected_row['Quantity'])
            unit_label = selected_row['Unit']
            
        with col_del2:
            # ช่องกรอกจำนวนที่ต้องการลบ (กำหนด max_value ไม่เกินจำนวนที่มีอยู่จริง)
            delete_qty = st.number_input(
                f"จำนวนที่จะลบ ({unit_label}):", 
                min_value=1, 
                max_value=max(current_qty, 1), 
                value=1
            )
            
        with col_del3:
            st.write("")
            st.write("")
            if st.button("🗑️ ยืนยันการตัดสต็อก", type="primary", use_container_width=True):
                if WEB_APP_URL == "วาง_WEB_APP_URL_ของคุณตรงนี้":
                    st.error("กรุณาใส่ Web App URL ก่อนครับ")
                else:
                    payload = {
                        "action": "delete", 
                        "itemName": item_to_delete,
                        "quantity": delete_qty
                    }
                    try:
                        # ใช้ json.dumps + headers เพื่อป้องกันปัญหา Redirect Error ของ Google Script
                        res = requests.post(
                            WEB_APP_URL, 
                            data=json.dumps(payload),
                            headers={"Content-Type": "application/json"}
                        )
                        if res.status_code == 200:
                            st.success(f"ตัด '{item_to_delete}' ออกไป {delete_qty} {unit_label} เรียบร้อยแล้ว!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"เกิดข้อผิดพลาดในการส่งข้อมูล (Status: {res.status_code})")
                    except Exception as e:
                        st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
    else:
        st.info("ไม่มีวัตถุดิบในตู้เย็นให้ลบ")
# ---------------------------------------------------------
# TAB 2: เมนูอาหารแนะนำ (ระบบ Match คำ)
# ---------------------------------------------------------
with tab2:
    st.subheader("🍳 เมนูที่สามารถทำได้จากวัตถุดิบในตู้")
    valid_fridge = df_fridge.dropna(subset=['ExpireDate'])
    available_items = valid_fridge[valid_fridge['ExpireDate'] > today]['ItemName'].astype(str).str.strip().str.lower().tolist()
    
    def is_ingredient_available(required_item, available_list):
        required_item = required_item.strip().lower()
        for item in available_list:
            if required_item in item or item in required_item:
                return True
            if "ไข่" in required_item and "ไข่" in item:
                return True
            if "หมู" in required_item and "หมู" in item:
                return True
            if "ไก่" in required_item and "ไก่" in item:
                return True
        return False

    match_found = False
    for idx, row in df_recipes.iterrows():
        menu_name = row['MenuName']
        required_ingredients = [i.strip().lower() for i in str(row['Ingredients']).split(',')]
        missing_items = [req for req in required_ingredients if not is_ingredient_available(req, available_items)]
        
        if len(missing_items) == 0:
            st.success(f"### ✅ **{menu_name}**")
            st.write(f"**วัตถุดิบที่ต้องใช้:** {row['Ingredients']}")
            st.caption("🎉 วัตถุดิบครบถ้วน พร้อมทำทานได้เลย!")
            st.markdown("---")
            match_found = True
        elif len(missing_items) <= 2:
            st.info(f"### 💡 **{menu_name}**")
            st.write(f"**วัตถุดิบที่ต้องใช้:** {row['Ingredients']}")
            st.write(f"⚠️ **ขาดอีกแค่น้อยชิ้น:** {', '.join(missing_items)}")
            st.markdown("---")
            match_found = True

    if not match_found:
        st.info("ℹ️ ยังไม่มีเมนูที่วัตถุดิบพอ")

# ---------------------------------------------------------
# TAB 3: ฟอร์มเพิ่มวัตถุดิบใหม่
# ---------------------------------------------------------
with tab3:
    st.subheader("➕ เพิ่มวัตถุดิบใหม่เข้าตู้เย็น")
    
    with st.form("add_item_form", clear_on_submit=True):
        new_name = st.text_input("ชื่อวัตถุดิบ (เช่น ไข่เป็ด, หมูสับ)")
        col_q, col_u = st.columns(2)
        with col_q:
            new_qty = st.number_input("จำนวน", min_value=1, value=1)
        with col_u:
            new_unit = st.text_input("หน่วย (เช่น ฟอง, กรัม, ชิ้น)", value="ชิ้น")
            
        new_expire = st.date_input("วันหมดอายุ", value=datetime.now() + timedelta(days=7))
        
        submitted = st.form_submit_button("➕ บันทึกเข้าตู้เย็น", type="primary", use_container_width=True)
        if submitted:
            if new_name:
                if WEB_APP_URL == "วาง_WEB_APP_URL_ของคุณตรงนี้":
                    st.error("กรุณาใส่ Web App URL ก่อนครับ")
                else:
                    payload = {
                        "action": "add",
                        "itemName": new_name,
                        "quantity": new_qty,
                        "unit": new_unit,
                        "expireDate": new_expire.strftime("%d/%m/%Y")
                    }
                    res = requests.post(WEB_APP_URL, json=payload)
                    if res.status_code == 200:
                        st.success(f"บันทึก '{new_name}' เรียบร้อยแล้ว!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("เกิดข้อผิดพลาดในการเพิ่มข้อมูล")
            else:
                st.warning("กรุณากรอกชื่อวัตถุดิบด้วยครับ")
