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

st.title("📊  Юнит-экономика с учетом габаритов (ОСНО)")

# Боковая панель
st.sidebar.header("🔑  Настройки")
c_id = st.sidebar.text_input("Client-ID")
a_key = st.sidebar.text_input("API Key", type="password")

st.sidebar.markdown("---")
vat_rate = st.sidebar.selectbox("Ставка НДС (%)", [20, 22, 0], index=1)
vat_coeff = 1 + (vat_rate / 100)

default_cost = st.sidebar.number_input("Закупка за ед. (с НДС), руб", value=2500)

# Тарифы логистики (можно менять)
st.sidebar.markdown("---")
st.sidebar.write("🚚  **Параметры логистики:**")
min_logistics = st.sidebar.number_input("Мин. логистика (руб)", value=76)
liter_cost = st.sidebar.number_input("Стоимость за литр/кг (руб)", value=12)

if c_id and a_key:
    headers = {"Client-Id": c_id, "Api-Key": a_key, "Content-Type": "application/json"}
    
    try:
        # 1. Список SKU
        res = requests.post("https://api-seller.ozon.ru/v3/product/list", 
                             headers=headers, json={"filter": {"visibility": "ALL"}, "limit": 100})
        
        if res.status_code == 200:
            product_ids = [str(i['product_id']) for i in res.json().get('result', {}).get('items', [])]
            
            # 2. Детальные данные (включая вес и размеры)
            res_details = requests.post("https://api-seller.ozon.ru/v2/product/info/list", 
                                         headers=headers, json={"product_id": product_ids})
            
            if res_details.status_code == 200:
                details = res_details.json().get('result', {}).get('items', [])
                final_data = []
                
                for p in details:
                    price = float(p.get('marketing_price') or p.get('price') or 0)
                    if price == 0: continue
                    
                    # ПОЛУЧАЕМ ГАБАРИТЫ
                    weight = p.get('weight', 0) / 1000 # в кг
                    h = p.get('height', 0) / 100 # в см
                    w = p.get('width', 0) / 100
                    l = p.get('depth', 0) / 100
                    
                    # Расчет логистики (упрощенная модель Ozon)
                    volume_weight = (h * w * l) / 5
                    calc_weight = max(weight, volume_weight)
                    item_logistics = max(min_logistics, calc_weight * liter_cost)
                    
                    # МАТЕМАТИКА ОСНО
                    price_no_vat = price / vat_coeff
                    cost_no_vat = default_cost / vat_coeff
                    fee_no_vat = (price * 0.15) / vat_coeff
                    log_no_vat = item_logistics / vat_coeff
                    
                    net_profit = price_no_vat - cost_no_vat - fee_no_vat - log_no_vat
                    roi = (net_profit / cost_no_vat) * 100 if cost_no_vat > 0 else 0
                    
                    final_data.append({
                        "Артикул": p.get('offer_id'),
                        "Название": p.get('name')[:25],
                        "Вес (кг)": round(weight, 2),
                        "Логистика": round(item_logistics, 2),
                        "НДС 22%": round(price - price_no_vat, 2),
                        "Прибыль": round(net_profit, 2),
                        "ROI %": round(roi, 1)
                    })
                
                df = pd.DataFrame(final_data)
                st.dataframe(df.sort_values("ROI %", ascending=False), use_container_width=True)
                st.info("💡  Логистика рассчитана автоматически на основе веса и объема из карточек товаров.")
except Exception as e:
        st.error(f"Ошибка: {e}")
else:
    st.info("Введите API ключи.")
