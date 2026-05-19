import streamlit as st
import pandas as pd
import requests

# Настройка страницы
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

st.title("📊 Юнит-экономика: Логистика, Реклама и ОСНО")

# Боковая панель
st.sidebar.header("🔑 Настройки")
c_id = st.sidebar.text_input("Client-ID")
a_key = st.sidebar.text_input("API Key", type="password")

st.sidebar.markdown("---")
vat_rate = st.sidebar.selectbox("Ставка НДС (%)", [20, 22, 0], index=1)
vat_coeff = 1 + (vat_rate / 100)

default_cost = st.sidebar.number_input("Закупка за ед. (с НДС), руб", value=2500)

# Параметры логистики
st.sidebar.markdown("---")
st.sidebar.write("🚚 **Тарифы логистики:**")
min_logistics = st.sidebar.number_input("Мин. логистика (руб)", value=76)
liter_cost = st.sidebar.number_input("Стоимость литра/кг (руб)", value=12)

# Маркетинг
st.sidebar.markdown("---")
st.sidebar.write("📣 **Маркетинг:**")
drr_pct = st.sidebar.slider("Средний ДРР (Реклама от цены), %", min_value=0, max_value=50, value=12)

if c_id and a_key:
    headers = {"Client-Id": c_id, "Api-Key": a_key, "Content-Type": "application/json"}
    
    try:
        # 1. Получаем список товаров (v3)
        res = requests.post("https://api-seller.ozon.ru/v3/product/list", 
                             headers=headers, json={"filter": {"visibility": "ALL"}, "limit": 100})
        
        if res.status_code == 200:
            items = res.json().get('result', {}).get('items', [])
            product_ids_only = [int(i['product_id']) for i in items]
            
            if not product_ids_only:
                st.warning("В вашем кабинете не найдено товаров.")
            else:
                # 2. Получаем детали через метод v3
                res_details = requests.post("https://api-seller.ozon.ru/v3/product/info/list", 
                                             headers=headers, json={"product_id": product_ids_only})
                
                if res_details.status_code == 200:
                    details = res_details.json().get('result', {}).get('items', [])
                    final_data = []
                    
                    for p in details:
                        # УПРАВЛЕНИЕ ПОИСКОМ ЦЕНЫ В V3 (ищем везде, где она может лежать)
                        price = 0.0
                        
                        # Вариант 1: Из общего поля price
                        if p.get('price'):
                            price = float(p.get('price'))
                        # Вариант 2: Из маркетинговой цены
                        elif p.get('marketing_price'):
                            price = float(p.get('marketing_price'))
                        # Вариант 3: Из вложенного блока индексов цен Ozon
                        elif p.get('price_indexes') and p.get('price_indexes').get('price_without_commission'):
                            price = float(p['price_indexes']['price_without_commission'].get('price', 0))
                        
                        # Если цену так и не нашли или товар архивный без цены — пропускаем
                        if price <= 0:
                            continue
                        
                        # ГАБАРИТЫ
                        vol_l = (p.get('height', 0) * p.get('width', 0) * p.get('depth', 0)) / 1000
                        weight_kg = p.get('weight', 0) / 1000
                        
                        # Расчет логистики
                        calc_val = max(vol_l, weight_kg)
                        item_logistics = max(min_logistics, calc_val * liter_cost)
                        
                        # Расчет рекламы
                        item_marketing = price * (drr_pct / 100)
                        
                        # МАТЕМАТИКА ОСНО (22%)
                        price_no_vat = price / vat_coeff
                        cost_no_vat = default_cost / vat_coeff
                        fee_no_vat = (price * 0.15) / vat_coeff  # Примерная комиссия 15%
                        log_no_vat = item_logistics / vat_coeff
                        marketing_no_vat = item_marketing / vat_coeff
                        
                        # Чистая прибыль
                        net_profit = price_no_vat - cost_no_vat - fee_no_vat - log_no_vat - marketing_no_vat
                        roi = (net_profit / cost_no_vat) * 100 if cost_no_vat > 0 else 0
                        
                        final_data.append({
                            "Артикул": p.get('offer_id'),
                            "Название": p.get('name')[:25] + "...",
                            "Цена": round(price, 2),
                            "Логистика": round(item_logistics, 1),
                            "Реклама": round(item_marketing, 1),
                            "Прибыль": round(net_profit, 1),
                            "ROI %": round(roi, 1)
                        })
                    
                    if final_data:
                        df = pd.DataFrame(final_data)
                        st.success(f"🔥 Успешно рассчитано товаров: {len(df)}")
                        
                        col1, col2 = st.columns(2)
                        col1.metric("Средняя чистая прибыль", f"{round(df['Прибыль'].mean(), 1)} ₽")
                        col2.metric("Средний ROI", f"{round(df['ROI %'].mean(), 1)} %")
                        
                        st.dataframe(df.sort_values("ROI %", ascending=False), use_container_width=True)
                    else:
                        st.warning("Товары обработаны, но алгоритм не смог считать цены из структуры v3. Проверяю альтернативные поля...")
                        # Показываем структуру первого товара для отладки, если таблица пуста
                        if details:
                            st.json(details[0])
                else:
                    st.error(f"❌ Код ответа деталей: {res_details.status_code}")
        else:
            st.error(f"Ошибка получения списка товаров: {res.status_code}")
            
    except Exception as e:
        st.error(f"Произошла непредвиденная ошибка: {e}")
else:
    st.info("Введите API ключи в боковой панели.")
