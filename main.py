import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Ozon Unit Eco - ОСНО", layout="wide")

# Авторизация
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pwd = st.text_input("Введите пароль доступа", type="password")
    if pwd == "ozon2026":
        st.session_state.auth = True
        st.rerun()
    st.stop()

st.title("🚀  Дашборд Юнит-Экономики (ОСНО)")

# Боковая панель
st.sidebar.header("🔑  Настройки")
c_id = st.sidebar.text_input("Client-ID")
a_key = st.sidebar.text_input("API Key", type="password")

# НАСТРОЙКИ НАЛОГА
st.sidebar.markdown("---")
vat_rate = st.sidebar.selectbox("Ставка НДС (%)", [20, 22, 0], index=1) # По умолчанию ставим 22
vat_coeff = 1 + (vat_rate / 100)

st.sidebar.markdown("---")
default_cost = st.sidebar.number_input("Закупка за ед. (с НДС), руб", value=2500)

if c_id and a_key:
    headers = {"Client-Id": c_id, "Api-Key": a_key, "Content-Type": "application/json"}
    
    try:
        # Получаем список
        res = requests.post("https://api-seller.ozon.ru/v3/product/list", 
                             headers=headers, json={"filter": {"visibility": "ALL"}, "limit": 100})
        
        if res.status_code == 200:
            items = res.json().get('result', {}).get('items', [])
            product_ids = [str(i['product_id']) for i in items]
            
            # Детали товаров
            res_details = requests.post("https://api-seller.ozon.ru/v2/product/info/list", 
                                         headers=headers, json={"product_id": product_ids})
            
            if res_details.status_code == 200:
                details = res_details.json().get('result', {}).get('items', [])
                final_data = []
                
                for p in details:
                    price = float(p.get('marketing_price') or p.get('price') or 0)
                    if price == 0: continue
                    
                    # --- МАТЕМАТИКА ОСНО 22% ---
                    # 1. Очищаем цену продажи от НДС
                    price_no_vat = price / vat_coeff
                    
                    # 2. Очищаем закупку от НДС (входящий налог)
                    cost_no_vat = default_cost / vat_coeff
                    
                    # 3. Расходы (условно считаем, что в комиссию/логистику НДС тоже включен)
                    fee_no_vat = (price * 0.15) / vat_coeff
                    logistics_no_vat = 450 / vat_coeff
                    
                    # Чистая прибыль
                    net_profit = price_no_vat - cost_no_vat - fee_no_vat - logistics_no_vat
                    roi = (net_profit / cost_no_vat) * 100 if cost_no_vat > 0 else 0
                    
                    final_data.append({
                        "Артикул": p.get('offer_id'),
                        "Название": p.get('name')[:30] + "...",
                        "Цена": price,
                        "НДС": round(price - price_no_vat, 2),
                        "Прибыль (чистая)": round(net_profit, 2),
                        "ROI %": round(roi, 1)
                    })
                
                df = pd.DataFrame(final_data)
                st.success(f"Расчет выполнен по ставке НДС {vat_rate}%")
                st.dataframe(df.sort_values("ROI %", ascending=False), use_container_width=True)
                
    except Exception as e:
        st.error(f"Ошибка: {e}")
else:
    st.info("Введите API ключи для начала пересчета прибыли.")
